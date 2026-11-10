import platform
import asyncio
import uuid
import time
import io
import csv
import json
import re
import ipaddress
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.core.config import settings
from app.core.database import get_db
from app.schemas.network import (
    HealthResponse,
    InterfaceSchema,
    OverviewResponse,
    DeviceDiscoverRequest,
    DeviceDiscoverResponse,
    DeviceSchema,
    DeviceUpdateRequest,
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
    SecurityFindingSchema,
    GatewayBaselineResponse,
    SelectInterfaceRequest
)
from app.models.entities import (
    NetworkDeviceModel,
    NetworkScanModel,
    ScanResultModel,
    NetworkMetricModel,
    PingResultModel,
    DNSResultModel,
    PortDiagnosticModel,
    SecurityFindingModel,
    ApplicationSettingsModel
)
from app.network.interfaces import get_network_interfaces, get_active_interface_ip, calculate_cidr
from app.network.gateway import (
    get_default_gateway,
    get_gateway_mac,
    get_dns_servers,
    get_public_ip,
    check_internet_connectivity,
    check_gateway_connectivity,
    measure_tcp_connect_latency
)
from app.network.discovery import discover_devices, stop_discovery, get_discovery_progress
from app.network.topology import generate_topology
from app.network.diagnostics import run_ping, run_dns_lookup, run_traceroute, calculate_ip_info, run_connectivity_test
from app.network.ports import run_port_scan
from app.monitoring.traffic import traffic_monitor, calculate_health_score
from app.security.auditor import security_auditor

router = APIRouter()

MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

def sanitize_csv_field(val: Any) -> str:
    """
    Sanitizes values against Spreadsheet Formula Injection (CWE-1236).
    Prepends a single apostrophe if a field starts with dangerous formula operators.
    """
    if val is None:
        return ""
    str_val = str(val).strip()
    if str_val and str_val[0] in ('=', '+', '-', '@', '\t', '\r', '\n'):
        return "'" + str_val
    return str_val

# In-memory runtime caches
_cached_devices: List[DeviceSchema] = []
_last_open_ports: List[Dict[str, Any]] = []

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Validates backend service operational health and database connectivity."""
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
    """Enumerates host network adapters without requiring Administrator privileges."""
    return get_network_interfaces()

@router.post("/network/interfaces/select")
async def select_interface_for_monitoring(payload: SelectInterfaceRequest):
    """Sets a specific network adapter as the primary source for live telemetry sampling with server-side validation."""
    req_name = payload.interface_name.strip()
    if not req_name:
        raise HTTPException(status_code=400, detail="Interface name cannot be empty.")

    available_interfaces = get_network_interfaces()
    target_iface = next((i for i in available_interfaces if i.name.lower() == req_name.lower()), None)
    if not target_iface:
        raise HTTPException(
            status_code=404,
            detail=f"Network interface '{req_name}' not found on host. Available: {[i.name for i in available_interfaces]}"
        )
    if not target_iface.is_up:
        raise HTTPException(
            status_code=400,
            detail=f"Network interface '{target_iface.name}' is currently disconnected or down."
        )

    traffic_monitor.set_selected_interface(target_iface.name)
    return {"status": "ok", "selected_interface": target_iface.name}

@router.get("/network/overview", response_model=OverviewResponse)
async def get_overview():
    """Returns genuine network overview measurements: ICMP latency, loss, IPs, and health score."""
    interfaces = get_network_interfaces()
    active_ip = get_active_interface_ip()

    def_iface = next((i for i in interfaces if i.is_default and i.is_up), None)
    if not def_iface:
        def_iface = next((i for i in interfaces if i.is_up and i.ip_address and not i.ip_address.startswith("127.")), None)

    iface_name = def_iface.name if def_iface else traffic_monitor.get_auto_interface()
    mask = def_iface.netmask if def_iface else None
    cidr = None
    if active_ip and mask:
        cidr, _ = calculate_cidr(active_ip, mask)

    gw = get_default_gateway()
    gw_mac = get_gateway_mac(gw) if gw else None
    dns_list = get_dns_servers()
    pub_ip = await get_public_ip()

    # Genuine connectivity & latency checks
    is_net_online, icmp_latency, packet_loss = check_internet_connectivity()
    is_gw_online, _, _ = check_gateway_connectivity(gw)
    tcp_latency = measure_tcp_connect_latency("1.1.1.1", 53, 0.3)

    health = calculate_health_score(icmp_latency, packet_loss)

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
        internet_connected=is_net_online,
        gateway_connected=is_gw_online,
        current_latency_ms=icmp_latency,
        tcp_latency_ms=tcp_latency,
        packet_loss_pct=packet_loss,
        download_kbps=down_kbps,
        upload_kbps=up_kbps,
        health_score=health,
        connected_devices_count=len(_cached_devices)
    )

@router.get("/network/metrics")
async def get_recent_metrics():
    """Returns the sliding-window buffer of recent throughput and latency measurements."""
    return {"metrics": traffic_monitor.history}

@router.get("/network/metrics/history")
async def get_historical_database_metrics(
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Fetches persistent network metric records from SQLite."""
    res = await db.execute(
        select(NetworkMetricModel).order_by(NetworkMetricModel.timestamp.desc()).limit(limit)
    )
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "interface_name": r.interface_name,
            "download_kbps": round(r.download_bytes_sec / 1024.0, 2),
            "upload_kbps": round(r.upload_bytes_sec / 1024.0, 2),
            "latency_ms": r.latency_ms,
            "packet_loss_pct": r.packet_loss_pct,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        }
        for r in records
    ]

@router.post("/devices/discover", response_model=DeviceDiscoverResponse)
async def run_discovery(payload: DeviceDiscoverRequest, db: AsyncSession = Depends(get_db)):
    """Triggers safe local subnet discovery and persists identified devices and scan results."""
    global _cached_devices
    start_time = time.perf_counter()
    try:
        result = await discover_devices(
            target_cidr=payload.cidr,
            timeout_seconds=payload.timeout_seconds or 10
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    elapsed_duration = round(time.perf_counter() - start_time, 2)

    # Persist scan metadata in database
    try:
        scan_record = NetworkScanModel(
            id=result.scan_id,
            scan_type="device_discovery",
            target_range=payload.cidr or "auto-detected",
            status=result.status,
            total_targets=result.total_targets,
            found_targets=result.total_discovered,
            duration_seconds=result.duration_seconds or elapsed_duration
        )
        db.add(scan_record)

        discovered_ips = {dev.ip for dev in result.devices}

        # Subnet-aware offline marking:
        # If target subnet was specified or discovered, mark existing stored devices in that subnet not seen in this sweep as offline
        scanned_net = None
        target_subnet_str = payload.cidr
        if target_subnet_str:
            try:
                scanned_net = ipaddress.ip_network(target_subnet_str, strict=False)
            except Exception:
                pass

        all_stored_res = await db.execute(select(NetworkDeviceModel))
        all_stored = all_stored_res.scalars().all()
        for stored in all_stored:
            if stored.ip_address not in discovered_ips:
                try:
                    dev_ip_obj = ipaddress.ip_address(stored.ip_address)
                    if scanned_net and dev_ip_obj in scanned_net:
                        stored.status = "offline"
                except Exception:
                    pass

        # Upsert discovered devices and record ScanResultModel rows
        for dev in result.devices:
            # Reconcile: First by MAC (handles DHCP IP changes without unique constraint violations), then by IP
            existing = None
            if dev.mac:
                mac_clean = dev.mac.strip().upper()
                res = await db.execute(select(NetworkDeviceModel).where(NetworkDeviceModel.mac_address == mac_clean))
                existing = res.scalars().first()

            if not existing:
                res = await db.execute(select(NetworkDeviceModel).where(NetworkDeviceModel.ip_address == dev.ip))
                existing = res.scalars().first()

            device_id = None
            now = datetime.now(timezone.utc)
            if existing:
                existing.last_seen = now
                existing.status = dev.status
                existing.ip_address = dev.ip  # Handle DHCP IP reassignments seamlessly
                if dev.mac:
                    existing.mac_address = dev.mac.strip().upper()
                if dev.hostname:
                    existing.hostname = dev.hostname
                if dev.vendor and dev.vendor != "Unknown":
                    existing.vendor = dev.vendor
                device_id = existing.id
            else:
                new_dev = NetworkDeviceModel(
                    ip_address=dev.ip,
                    mac_address=dev.mac.strip().upper() if dev.mac else None,
                    vendor=dev.vendor,
                    hostname=dev.hostname,
                    is_gateway=dev.is_gateway,
                    is_local_host=dev.is_local_host,
                    status=dev.status,
                    first_seen=now,
                    last_seen=now
                )
                db.add(new_dev)
                await db.flush()
                device_id = new_dev.id

            scan_item = ScanResultModel(
                scan_id=result.scan_id,
                device_id=device_id,
                ip_address=dev.ip,
                mac_address=dev.mac,
                response_time_ms=dev.response_time_ms
            )
            db.add(scan_item)

            # Record in security auditor history for ARP spoofing / DHCP tracking
            security_auditor.record_device_history(dev.ip, dev.mac)

        await db.commit()

        # Update cached devices from persistent database
        res_all = await db.execute(select(NetworkDeviceModel).order_by(NetworkDeviceModel.ip_address.asc()))
        _cached_devices = [
            DeviceSchema(
                id=d.id,
                ip=d.ip_address,
                mac=d.mac_address,
                vendor=d.vendor or "Unknown",
                hostname=d.hostname,
                custom_name=d.custom_name,
                notes=d.notes,
                category=d.category or "workstation",
                is_trusted=d.is_trusted,
                is_gateway=d.is_gateway,
                is_local_host=d.is_local_host,
                status=d.status,
                first_seen=d.first_seen,
                last_seen=d.last_seen
            )
            for d in res_all.scalars().all()
        ]
    except Exception:
        await db.rollback()

    return result

@router.patch("/devices/{device_id}", response_model=DeviceSchema)
async def update_device_details(
    device_id: int,
    payload: DeviceUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Updates device custom label, notes, category, and trusted authorization status."""
    res = await db.execute(select(NetworkDeviceModel).where(NetworkDeviceModel.id == device_id))
    dev = res.scalars().first()
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found.")

    if payload.custom_name is not None:
        dev.custom_name = payload.custom_name.strip() or None
    if payload.notes is not None:
        dev.notes = payload.notes.strip() or None
    if payload.category is not None:
        dev.category = payload.category.strip()
    if payload.is_trusted is not None:
        dev.is_trusted = payload.is_trusted

    await db.commit()
    await db.refresh(dev)

    return DeviceSchema(
        id=dev.id,
        ip=dev.ip_address,
        mac=dev.mac_address,
        vendor=dev.vendor or "Unknown",
        hostname=dev.hostname,
        custom_name=dev.custom_name,
        notes=dev.notes,
        category=dev.category or "workstation",
        is_trusted=dev.is_trusted,
        is_gateway=dev.is_gateway,
        is_local_host=dev.is_local_host,
        status=dev.status,
        first_seen=dev.first_seen,
        last_seen=dev.last_seen
    )

@router.post("/devices/scan/stop")
async def stop_running_discovery():
    """Signals any currently running subnet discovery sweep to cancel gracefully."""
    stop_discovery()
    return {"status": "stopped", "message": "Discovery sweep cancellation signal sent."}

@router.get("/devices/scan/progress")
async def get_scan_progress():
    """Returns live progress indicators for a running subnet sweep."""
    return get_discovery_progress()

@router.get("/devices", response_model=List[DeviceSchema])
async def list_devices(db: AsyncSession = Depends(get_db)):
    """Returns discovered devices from database inventory."""
    res = await db.execute(select(NetworkDeviceModel).order_by(NetworkDeviceModel.ip_address.asc()))
    db_devs = res.scalars().all()
    return [
        DeviceSchema(
            id=d.id,
            ip=d.ip_address,
            mac=d.mac_address,
            vendor=d.vendor or "Unknown",
            hostname=d.hostname,
            custom_name=d.custom_name,
            notes=d.notes,
            category=d.category or "workstation",
            is_trusted=d.is_trusted,
            is_gateway=d.is_gateway,
            is_local_host=d.is_local_host,
            status=d.status,
            first_seen=d.first_seen,
            last_seen=d.last_seen
        )
        for d in db_devs
    ]

@router.get("/topology", response_model=TopologyResponse)
async def get_network_topology(db: AsyncSession = Depends(get_db)):
    """Generates an interactive React Flow network topology graph (Read-Only)."""
    global _cached_devices
    devices = _cached_devices
    if not devices:
        res = await db.execute(select(NetworkDeviceModel))
        db_devs = res.scalars().all()
        devices = [
            DeviceSchema(
                id=d.id,
                ip=d.ip_address,
                mac=d.mac_address,
                vendor=d.vendor or "Unknown",
                hostname=d.hostname,
                custom_name=d.custom_name,
                is_gateway=d.is_gateway,
                is_local_host=d.is_local_host,
                status=d.status
            )
            for d in db_devs
        ]

    return generate_topology(devices)

@router.post("/diagnostics/ping", response_model=PingResponse)
async def ping_endpoint(payload: PingRequest, db: AsyncSession = Depends(get_db)):
    """Executes genuine ICMP ping test and logs audit record."""
    try:
        res = await asyncio.to_thread(run_ping, payload.target, payload.count, payload.timeout_ms)
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
    """Resolves DNS records across A, AAAA, MX, NS, CNAME, TXT, SOA types."""
    try:
        res = await asyncio.to_thread(run_dns_lookup, payload.domain, payload.record_type, payload.custom_server)
        audit = DNSResultModel(
            domain=payload.domain,
            record_type=payload.record_type,
            resolved_server=res.resolved_by,
            records_json=json.dumps(res.records),
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
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diagnostics/ip-info", response_model=IPInfoResponse)
async def ip_info_endpoint(payload: IPInfoRequest):
    """Performs CIDR subnet calculation mathematically without memory allocation."""
    try:
        return calculate_ip_info(payload.ip_or_cidr)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/diagnostics/connectivity")
async def connectivity_test_endpoint():
    """Executes multi-tier automated connectivity benchmark (Loopback, Gateway, Internet)."""
    return await asyncio.to_thread(run_connectivity_test)

@router.post("/diagnostics/ports", response_model=PortScanResponse)
async def port_scan_endpoint(payload: PortScanRequest, db: AsyncSession = Depends(get_db)):
    """Controlled multi-threaded TCP port scan with target authorization."""
    global _last_open_ports
    if not payload.authorized:
        raise HTTPException(status_code=403, detail="Target authorization must be explicitly confirmed.")

    start_scan_time = time.perf_counter()
    try:
        scan_id = str(uuid.uuid4())[:8]

        res = await run_port_scan(
            target=payload.target,
            ports=payload.ports,
            timeout_ms=payload.timeout_ms,
            authorized=payload.authorized
        )

        elapsed_sec = round(time.perf_counter() - start_scan_time, 2)

        open_list = [
            {"port": r.port, "target": payload.target, "service": r.service, "banner": r.banner}
            for r in res.results if r.state == "open"
        ]
        _last_open_ports = open_list

        # Record scan metadata in network_scans with actual measured elapsed duration
        scan_record = NetworkScanModel(
            id=scan_id,
            scan_type="port_scan",
            target_range=f"{payload.target}:{len(payload.ports)} ports",
            status="completed",
            total_targets=len(payload.ports),
            found_targets=res.open_count,
            duration_seconds=elapsed_sec
        )
        db.add(scan_record)

        # Log individual port results linked to scan_id preserving banner evidence
        for r in res.results:
            audit = PortDiagnosticModel(
                scan_id=scan_id,
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Port scan error: {str(e)}")

# =========================================================================
# GATEWAY MAC BASELINE MANAGEMENT
# =========================================================================

@router.get("/security/gateway-baseline", response_model=GatewayBaselineResponse)
async def get_gateway_baseline(db: AsyncSession = Depends(get_db)):
    """Returns detected gateway IP and hardware MAC alongside confirmed baseline status."""
    gw_ip = get_default_gateway()
    detected_mac = get_gateway_mac(gw_ip) if gw_ip else None

    res_mac = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_mac"))
    res_status = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_status"))
    res_time = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_confirmed_at"))

    mac_row = res_mac.scalars().first()
    status_row = res_status.scalars().first()
    time_row = res_time.scalars().first()

    confirmed_mac = mac_row.value if mac_row and mac_row.value else None
    confirmed_status = status_row.value if status_row else "unconfirmed"
    confirmed_time = time_row.value if time_row else None

    # Check for baseline mismatch
    if confirmed_mac and detected_mac and confirmed_mac.upper() != detected_mac.upper():
        current_status = "mismatch"
    elif confirmed_status == "confirmed" and confirmed_mac:
        current_status = "confirmed"
    else:
        current_status = "unconfirmed"

    return GatewayBaselineResponse(
        gateway_ip=gw_ip,
        detected_mac=detected_mac,
        confirmed_mac=confirmed_mac,
        baseline_mac=confirmed_mac,
        status=current_status,
        confirmed_at=confirmed_time
    )

@router.post("/security/gateway-baseline/confirm", response_model=GatewayBaselineResponse)
async def confirm_gateway_baseline(
    payload: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    """Explicitly confirms the gateway MAC as the trusted baseline with strict format validation."""
    gw_ip = get_default_gateway()
    detected_mac = get_gateway_mac(gw_ip) if gw_ip else None
    
    mac_to_confirm = None
    if payload and payload.get("baseline_mac"):
        mac_to_confirm = str(payload["baseline_mac"]).strip()
    elif detected_mac:
        mac_to_confirm = detected_mac

    if not mac_to_confirm:
        raise HTTPException(status_code=400, detail="Cannot confirm baseline: No active gateway MAC detected or provided.")

    # Strict MAC address format validation (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)
    if not MAC_REGEX.match(mac_to_confirm):
        raise HTTPException(
            status_code=422,
            detail=f"Malformed MAC address '{mac_to_confirm}'. Expected standard 6-byte hexadecimal format (e.g. AA:BB:CC:DD:EE:FF)."
        )

    mac_to_confirm = mac_to_confirm.replace("-", ":").upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Upsert settings
    for key, val in [
        ("gateway_baseline_mac", mac_to_confirm),
        ("gateway_baseline_status", "confirmed"),
        ("gateway_baseline_confirmed_at", now_iso)
    ]:
        res = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == key))
        row = res.scalars().first()
        if row:
            row.value = val
        else:
            db.add(ApplicationSettingsModel(key=key, value=val, description="Gateway MAC baseline"))

    await db.commit()

    return GatewayBaselineResponse(
        gateway_ip=gw_ip,
        detected_mac=detected_mac,
        confirmed_mac=mac_to_confirm,
        baseline_mac=mac_to_confirm,
        status="confirmed",
        confirmed_at=now_iso
    )

@router.post("/security/gateway-baseline/reset", response_model=GatewayBaselineResponse)
async def reset_gateway_baseline(db: AsyncSession = Depends(get_db)):
    """Clears the confirmed gateway baseline so the operator can establish a new one."""
    for key, val in [
        ("gateway_baseline_mac", ""),
        ("gateway_baseline_status", "unconfirmed"),
        ("gateway_baseline_confirmed_at", "")
    ]:
        res = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == key))
        row = res.scalars().first()
        if row:
            row.value = val

    await db.commit()

    gw_ip = get_default_gateway()
    detected_mac = get_gateway_mac(gw_ip) if gw_ip else None

    return GatewayBaselineResponse(
        gateway_ip=gw_ip,
        detected_mac=detected_mac,
        confirmed_mac=None,
        baseline_mac=None,
        status="unconfirmed",
        confirmed_at=None
    )

# =========================================================================
# SECURITY FINDINGS & LIFECYCLE MANAGEMENT
# =========================================================================

async def _execute_security_audit(db: AsyncSession) -> List[SecurityFindingSchema]:
    global _cached_devices, _last_open_ports

    current_devices = _cached_devices
    if not current_devices:
        res = await db.execute(select(NetworkDeviceModel))
        db_devs = res.scalars().all()
        current_devices = [
            DeviceSchema(
                id=d.id,
                ip=d.ip_address,
                mac=d.mac_address,
                vendor=d.vendor or "Unknown",
                hostname=d.hostname,
                custom_name=d.custom_name,
                notes=d.notes,
                category=d.category or "workstation",
                is_trusted=d.is_trusted,
                is_gateway=d.is_gateway,
                is_local_host=d.is_local_host,
                status=d.status,
                first_seen=d.first_seen,
                last_seen=d.last_seen
            )
            for d in db_devs
        ]

    # Load baseline settings
    res_mac = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_mac"))
    res_status = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_status"))
    res_time = await db.execute(select(ApplicationSettingsModel).where(ApplicationSettingsModel.key == "gateway_baseline_confirmed_at"))

    mac_row = res_mac.scalars().first()
    status_row = res_status.scalars().first()
    time_row = res_time.scalars().first()

    confirmed_mac = mac_row.value if mac_row and mac_row.value else None
    baseline_status = status_row.value if status_row and status_row.value else "unconfirmed"
    confirmed_time = time_row.value if time_row else None

    # Run auditor
    evaluated_findings = security_auditor.audit_environment(
        devices=current_devices,
        open_ports=_last_open_ports,
        confirmed_baseline_mac=confirmed_mac,
        baseline_status=baseline_status,
        confirmed_at=confirmed_time
    )

    # Persist findings to database avoiding duplicates for active findings
    try:
        for f in evaluated_findings:
            if f.rule_id == "SEC-000":
                continue # Informational baseline satisfaction not stored as a defect
            
            existing_query = select(SecurityFindingModel).where(
                SecurityFindingModel.rule_id == f.rule_id,
                SecurityFindingModel.title == f.title,
                SecurityFindingModel.status == "active"
            )
            res_ex = await db.execute(existing_query)
            existing = res_ex.scalars().first()

            if existing:
                existing.evidence = f.evidence
                existing.confidence = f.confidence
                f.id = existing.id
                f.status = existing.status
            else:
                new_finding = SecurityFindingModel(
                    rule_id=f.rule_id,
                    severity=f.severity,
                    title=f.title,
                    category=f.category,
                    description=f.description,
                    evidence=f.evidence,
                    impact=f.impact,
                    remediation=f.remediation,
                    target=f.target,
                    confidence=f.confidence,
                    status="active"
                )
                db.add(new_finding)
                await db.flush()
                f.id = new_finding.id

        await db.commit()
    except Exception:
        await db.rollback()

    return evaluated_findings

@router.post("/security/audit/run", response_model=List[SecurityFindingSchema])
async def trigger_security_audit(db: AsyncSession = Depends(get_db)):
    """
    Explicitly triggers security audit heuristic evaluation across devices and open ports,
    persists new findings to the database, and returns the findings list.
    """
    return await _execute_security_audit(db)

@router.get("/security/findings", response_model=List[SecurityFindingSchema])
async def list_security_findings(db: AsyncSession = Depends(get_db)):
    """
    Returns active security findings strictly read-only from the persistent database.
    """
    query = (
        select(SecurityFindingModel)
        .where(SecurityFindingModel.status == "active")
        .order_by(SecurityFindingModel.created_at.desc())
    )
    res = await db.execute(query)
    findings = res.scalars().all()

    if not findings:
        return await _execute_security_audit(db)

    return [
        SecurityFindingSchema(
            id=f.id,
            rule_id=f.rule_id,
            severity=f.severity,
            title=f.title,
            category=f.category,
            description=f.description,
            evidence=f.evidence,
            impact=f.impact,
            remediation=f.remediation,
            target=f.target,
            confidence=f.confidence or "potential",
            status=f.status,
            created_at=f.created_at,
            acknowledged_at=f.acknowledged_at,
            resolved_at=f.resolved_at
        )
        for f in findings
    ]

@router.get("/security/findings/history", response_model=List[SecurityFindingSchema])
async def get_security_findings_history(
    status: Optional[str] = Query(default=None, description="Filter by status: active, acknowledged, resolved"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: critical, high, medium, low, info"),
    db: AsyncSession = Depends(get_db)
):
    """Returns persistent security audit findings history with optional status and severity filtering."""
    query = select(SecurityFindingModel).order_by(SecurityFindingModel.created_at.desc())
    if status:
        query = query.where(SecurityFindingModel.status == status)
    if severity:
        query = query.where(SecurityFindingModel.severity == severity)

    res = await db.execute(query)
    findings = res.scalars().all()
    return [
        SecurityFindingSchema(
            id=f.id,
            rule_id=f.rule_id,
            severity=f.severity,
            title=f.title,
            category=f.category,
            description=f.description,
            evidence=f.evidence,
            impact=f.impact,
            remediation=f.remediation,
            target=f.target,
            confidence=f.confidence or "potential",
            status=f.status,
            created_at=f.created_at,
            acknowledged_at=f.acknowledged_at,
            resolved_at=f.resolved_at
        )
        for f in findings
    ]

@router.post("/security/findings/{finding_id}/acknowledge")
async def acknowledge_security_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    """Marks an active security finding as acknowledged by the operator."""
    res = await db.execute(select(SecurityFindingModel).where(SecurityFindingModel.id == finding_id))
    finding = res.scalars().first()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding with ID {finding_id} not found.")

    finding.status = "acknowledged"
    finding.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok", "message": f"Finding {finding_id} marked as acknowledged."}

@router.post("/security/findings/{finding_id}/resolve")
async def resolve_security_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    """Marks an active or acknowledged security finding as resolved."""
    res = await db.execute(select(SecurityFindingModel).where(SecurityFindingModel.id == finding_id))
    finding = res.scalars().first()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding with ID {finding_id} not found.")

    finding.status = "resolved"
    finding.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "ok", "message": f"Finding {finding_id} marked as resolved."}

# =========================================================================
# REPORT EXPORTS (CSV & JSON)
# =========================================================================

@router.get("/reports/devices/export")
async def export_devices_report(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """Exports discovered device inventory as downloadable CSV or JSON."""
    res = await db.execute(select(NetworkDeviceModel).order_by(NetworkDeviceModel.ip_address.asc()))
    devices = res.scalars().all()

    if format == "json":
        data = [
            {
                "id": d.id,
                "ip": d.ip_address,
                "mac": d.mac_address,
                "vendor": d.vendor,
                "hostname": d.hostname,
                "custom_name": d.custom_name,
                "category": d.category,
                "is_trusted": d.is_trusted,
                "status": d.status,
                "first_seen": d.first_seen.isoformat() if d.first_seen else None,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None
            }
            for d in devices
        ]
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=netscope_devices.json"}
        )

    # Generate CSV protected against Spreadsheet Formula Injection (CWE-1236)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "IP Address", "MAC Address", "Vendor", "Hostname", "Custom Name", "Category", "Trusted", "Status", "Last Seen"])
    for d in devices:
        writer.writerow([
            d.id,
            sanitize_csv_field(d.ip_address),
            sanitize_csv_field(d.mac_address or "N/A"),
            sanitize_csv_field(d.vendor or "Unknown"),
            sanitize_csv_field(d.hostname or "N/A"),
            sanitize_csv_field(d.custom_name or "N/A"),
            sanitize_csv_field(d.category or "workstation"),
            "Yes" if d.is_trusted else "No",
            sanitize_csv_field(d.status),
            d.last_seen.isoformat() if d.last_seen else "N/A"
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netscope_devices.csv"}
    )

@router.get("/reports/security/export")
async def export_security_report(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """Exports security audit findings as downloadable CSV or JSON."""
    res = await db.execute(select(SecurityFindingModel).order_by(SecurityFindingModel.created_at.desc()))
    findings = res.scalars().all()

    if format == "json":
        data = [
            {
                "id": f.id,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "title": f.title,
                "category": f.category,
                "target": f.target,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in findings
        ]
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=netscope_security_findings.json"}
        )

    # Generate CSV protected against Spreadsheet Formula Injection (CWE-1236)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Rule ID", "Severity", "Title", "Category", "Target", "Status", "Evidence", "Remediation", "Timestamp"])
    for f in findings:
        writer.writerow([
            f.id,
            sanitize_csv_field(f.rule_id),
            sanitize_csv_field(f.severity.upper()),
            sanitize_csv_field(f.title),
            sanitize_csv_field(f.category),
            sanitize_csv_field(f.target or "N/A"),
            sanitize_csv_field(f.status),
            sanitize_csv_field(f.evidence),
            sanitize_csv_field(f.remediation),
            f.created_at.isoformat() if f.created_at else "N/A"
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netscope_security_findings.csv"}
    )

@router.get("/reports/history/export")
async def export_history_report(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """Exports scan operation history as downloadable CSV or JSON."""
    res = await db.execute(select(NetworkScanModel).order_by(NetworkScanModel.created_at.desc()).limit(100))
    scans = res.scalars().all()

    if format == "json":
        data = [
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
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=netscope_scan_history.json"}
        )

    # Generate CSV protected against Spreadsheet Formula Injection (CWE-1236)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Scan ID", "Scan Type", "Target Range", "Status", "Targets Found", "Duration (s)", "Timestamp"])
    for s in scans:
        writer.writerow([
            s.id,
            sanitize_csv_field(s.scan_type),
            sanitize_csv_field(s.target_range),
            sanitize_csv_field(s.status),
            s.found_targets,
            s.duration_seconds,
            s.created_at.isoformat() if s.created_at else "N/A"
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netscope_scan_history.csv"}
    )

@router.get("/history")
async def get_scan_history(db: AsyncSession = Depends(get_db)):
    """Retrieves previous network scan operations from the database."""
    res = await db.execute(select(NetworkScanModel).order_by(NetworkScanModel.created_at.desc()).limit(50))
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
    """Returns safe application configuration parameters for frontend consumption."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "telemetry_interval": settings.TELEMETRY_INTERVAL_SECONDS,
        "max_concurrent_port_scans": settings.MAX_CONCURRENT_PORT_SCANS
    }
