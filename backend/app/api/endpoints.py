import platform
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.schemas.network import (
    HealthResponse,
    InterfaceSchema,
    OverviewResponse,
    DeviceDiscoverRequest,
    DeviceDiscoverResponse,
    DeviceSchema,
    TopologyResponse,
    PingRequest,
    PingResponse,
    DNSRequest,
    DNSResponse,
    TracerouteRequest,
    TracerouteResponse,
    IPInfoRequest,
    IPInfoResponse,
    PortScanRequest,
    PortScanResponse,
    SecurityFindingSchema
)
from app.models.entities import (
    NetworkDeviceModel,
    NetworkScanModel,
    ScanResultModel,
    PingResultModel,
    DNSResultModel,
    PortDiagnosticModel,
    SecurityFindingModel,
    ApplicationSettingsModel
)
from app.network.interfaces import get_network_interfaces, get_active_interface_ip, calculate_cidr
from app.network.gateway import get_default_gateway, get_gateway_mac, get_dns_servers, get_public_ip, measure_target_latency
from app.network.discovery import discover_devices
from app.network.topology import generate_topology
from app.network.diagnostics import run_ping, run_dns_lookup, run_traceroute, calculate_ip_info
from app.network.ports import run_port_scan
from app.monitoring.traffic import traffic_monitor, calculate_health_score
from app.security.auditor import security_auditor

router = APIRouter()

# Memory cache for latest discovered devices
_cached_devices: List[DeviceSchema] = []
_last_open_ports: List[dict] = []

@router.get("/health", response_model=HealthResponse)
async def get_health(db: AsyncSession = Depends(get_db)):
    """Health check verifying FastAPI status, OS platform, and SQLite connectivity."""
    db_ok = True
    try:
        await db.execute(select(1))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version=settings.VERSION,
        platform=f"{platform.system()}-{platform.release()}",
        db_connected=db_ok,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/network/interfaces", response_model=List[InterfaceSchema])
async def list_interfaces():
    """Lists all physical and virtual network adapters with IP, MAC, and speed metrics."""
    return get_network_interfaces()

@router.get("/network/overview", response_model=OverviewResponse)
async def get_overview():
    """Returns comprehensive network overview snapshot including health score, IPs, and latency."""
    interfaces = get_network_interfaces()
    active_ip = get_active_interface_ip() or "127.0.0.1"

    def_iface = next((i for i in interfaces if i.is_default), None)
    iface_name = def_iface.name if def_iface else "Ethernet"
    mask = def_iface.netmask if def_iface and def_iface.netmask else "255.255.255.0"
    cidr, _ = calculate_cidr(active_ip, mask)

    gw = get_default_gateway()
    gw_mac = get_gateway_mac(gw)
    dns_list = get_dns_servers()
    pub_ip = await get_public_ip()

    # Latency to gateway or public DNS
    latency = measure_target_latency(gw or "1.1.1.1", port=53, timeout_sec=0.5)
    loss = 0.0 if latency is not None else 100.0
    health = calculate_health_score(latency, loss)

    # Throughput from traffic monitor
    down_kbps = 0.0
    up_kbps = 0.0
    if traffic_monitor.latest_telemetry:
        down_kbps = round(traffic_monitor.latest_telemetry.bandwidth.download_bytes_per_sec / 1024.0, 1)
        up_kbps = round(traffic_monitor.latest_telemetry.bandwidth.upload_bytes_per_sec / 1024.0, 1)

    return OverviewResponse(
        active_interface=iface_name,
        local_ip=active_ip,
        public_ip=pub_ip,
        subnet_mask=mask,
        cidr=cidr,
        default_gateway=gw,
        gateway_mac=gw_mac,
        dns_servers=dns_list,
        internet_connected=(latency is not None),
        current_latency_ms=latency,
        packet_loss_pct=loss,
        download_kbps=down_kbps,
        upload_kbps=up_kbps,
        health_score=health,
        connected_devices_count=len(_cached_devices)
    )

@router.get("/network/metrics")
async def get_recent_metrics():
    """Returns the sliding-window buffer of recent throughput and latency measurements."""
    return {"metrics": traffic_monitor.history}

@router.post("/devices/discover", response_model=DeviceDiscoverResponse)
async def run_discovery(payload: DeviceDiscoverRequest, db: AsyncSession = Depends(get_db)):
    """Triggers safe local subnet discovery and persists identified devices."""
    global _cached_devices
    result = await discover_devices(
        target_cidr=payload.cidr,
        timeout_seconds=payload.timeout_seconds or 10
    )
    _cached_devices = result.devices

    # Persist scan metadata in database
    try:
        scan_record = NetworkScanModel(
            id=result.scan_id,
            scan_type="device_discovery",
            target_range=payload.cidr or "auto-detected",
            status="completed",
            total_targets=result.total_discovered,
            found_targets=result.total_discovered,
            duration_seconds=result.duration_seconds
        )
        db.add(scan_record)

        # Upsert discovered devices
        for dev in result.devices:
            # Check existing device by IP or MAC
            query = select(NetworkDeviceModel).where(NetworkDeviceModel.ip_address == dev.ip)
            res = await db.execute(query)
            existing = res.scalars().first()

            if existing:
                existing.mac_address = dev.mac or existing.mac_address
                existing.vendor = dev.vendor or existing.vendor
                existing.hostname = dev.hostname or existing.hostname
                existing.is_gateway = dev.is_gateway
                existing.is_local_host = dev.is_local_host
                existing.last_seen = datetime.now(timezone.utc)
            else:
                new_dev = NetworkDeviceModel(
                    ip_address=dev.ip,
                    mac_address=dev.mac,
                    vendor=dev.vendor,
                    hostname=dev.hostname,
                    is_gateway=dev.is_gateway,
                    is_local_host=dev.is_local_host,
                    status="online"
                )
                db.add(new_dev)

        await db.commit()
    except Exception:
        await db.rollback()

    return result

@router.get("/devices", response_model=List[DeviceSchema])
async def list_devices(db: AsyncSession = Depends(get_db)):
    """Returns discovered devices from cache or persistent database."""
    global _cached_devices
    if _cached_devices:
        return _cached_devices

    # Fallback to database
    res = await db.execute(select(NetworkDeviceModel))
    db_devs = res.scalars().all()
    return [
        DeviceSchema(
            id=d.id,
            ip=d.ip_address,
            mac=d.mac_address,
            vendor=d.vendor or "Unknown",
            hostname=d.hostname,
            is_gateway=d.is_gateway,
            is_local_host=d.is_local_host,
            status=d.status,
            first_seen=d.first_seen,
            last_seen=d.last_seen
        )
        for d in db_devs
    ]

@router.get("/topology", response_model=TopologyResponse)
async def get_network_topology():
    """Generates an interactive React Flow network topology graph."""
    global _cached_devices
    if not _cached_devices:
        # Quick initial discovery if empty
        disc = await discover_devices(timeout_seconds=5)
        _cached_devices = disc.devices

    return generate_topology(_cached_devices)

@router.post("/diagnostics/ping", response_model=PingResponse)
async def ping_endpoint(payload: PingRequest, db: AsyncSession = Depends(get_db)):
    """Executes genuine ICMP ping test and logs audit record."""
    try:
        res = await asyncio.to_thread(run_ping, payload.target, payload.count, payload.timeout_ms)
        # Log to DB
        audit = PingResultModel(
            target=payload.target,
            packets_sent=res.packets_transmitted,
            packets_received=res.packets_received,
            min_rtt_ms=res.min_rtt_ms,
            avg_rtt_ms=res.avg_rtt_ms,
            max_rtt_ms=res.max_rtt_ms,
            packet_loss_pct=res.packet_loss_pct,
            raw_output=res.raw_output
        )
        db.add(audit)
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/diagnostics/dns", response_model=DNSResponse)
async def dns_endpoint(payload: DNSRequest, db: AsyncSession = Depends(get_db)):
    """Resolves DNS records across A, AAAA, MX, NS, CNAME, TXT types."""
    try:
        res = await asyncio.to_thread(run_dns_lookup, payload.domain, payload.record_type, payload.custom_server)
        audit = DNSResultModel(
            domain=payload.domain,
            record_type=payload.record_type,
            resolved_server=res.resolved_by,
            records_json=str(res.records),
            query_time_ms=res.query_time_ms
        )
        db.add(audit)
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/diagnostics/traceroute", response_model=TracerouteResponse)
async def traceroute_endpoint(payload: TracerouteRequest):
    """Executes network hop-by-hop traceroute."""
    try:
        return await asyncio.to_thread(run_traceroute, payload.target, payload.max_hops, payload.timeout_ms)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/diagnostics/ip-info", response_model=IPInfoResponse)
async def ip_info_endpoint(payload: IPInfoRequest):
    """Performs CIDR subnet calculation, binary formatting, and usable host range analysis."""
    try:
        return calculate_ip_info(payload.ip_or_cidr)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/diagnostics/ports", response_model=PortScanResponse)
async def port_scan_endpoint(payload: PortScanRequest, db: AsyncSession = Depends(get_db)):
    """Controlled multi-threaded TCP port scan with target authorization."""
    global _last_open_ports
    if not payload.authorized:
        raise HTTPException(status_code=403, detail="Target authorization must be explicitly confirmed.")

    try:
        res = await run_port_scan(
            target=payload.target,
            ports=payload.ports,
            timeout_ms=payload.timeout_ms,
            authorized=payload.authorized
        )

        # Cache open ports for security auditor
        open_list = [
            {"port": r.port, "target": payload.target, "service": r.service}
            for r in res.results if r.state == "open"
        ]
        _last_open_ports = open_list

        # Log open ports to DB
        for r in res.results:
            audit = PortDiagnosticModel(
                target_ip=payload.target,
                port=r.port,
                state=r.state,
                service_name=r.service,
                banner=r.banner,
                response_time_ms=r.rtt_ms
            )
            db.add(audit)
        await db.commit()

        return res
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Port scan error: {str(e)}")

@router.get("/security/findings", response_model=List[SecurityFindingSchema])
async def list_security_findings():
    """Runs security analysis engine against topology, inventory, and exposed services."""
    global _cached_devices, _last_open_ports
    return security_auditor.audit_environment(_cached_devices, _last_open_ports)

@router.get("/history")
async def get_scan_history(db: AsyncSession = Depends(get_db)):
    """Retrieves previous network scan operations from the database."""
    res = await db.execute(select(NetworkScanModel).order_by(NetworkScanModel.created_at.desc()).limit(20))
    scans = res.scalars().all()
    return [
        {
            "id": s.id,
            "scan_type": s.scan_type,
            "target_range": s.target_range,
            "status": s.status,
            "found_targets": s.found_targets,
            "duration_seconds": s.duration_seconds,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in scans
    ]

@router.get("/settings")
async def get_settings():
    """Returns application configuration parameters."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "telemetry_interval": settings.TELEMETRY_INTERVAL_SECONDS,
        "max_concurrent_port_scans": settings.MAX_CONCURRENT_PORT_SCANS,
        "database_url": "sqlite+aiosqlite:///backend/data/netscope.db (WAL mode)"
    }
