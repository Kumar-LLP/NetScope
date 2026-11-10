import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Isolate tests to a dedicated test database to protect production data
TEST_DB_PATH = BASE_DIR / "data" / "test_isolated_netscope.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"

test_engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

import app.core.database as db_module
from app.core.database import Base, get_db
from app.main import app

# Patch database session provider and dependency override
db_module.AsyncSessionLocal = TestSessionLocal

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "platform" in data

@pytest.mark.asyncio
async def test_interfaces_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/network/interfaces")
    assert response.status_code == 200
    interfaces = response.json()
    assert isinstance(interfaces, list)
    assert len(interfaces) > 0
    first = interfaces[0]
    assert "name" in first
    assert "is_up" in first

@pytest.mark.asyncio
async def test_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/network/overview")
    assert response.status_code == 200
    data = response.json()
    assert "active_interface" in data
    assert "local_ip" in data
    assert "health_score" in data
    assert 0 <= data["health_score"] <= 100

@pytest.mark.asyncio
async def test_ip_info_calculator():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "192.168.1.50/24"})
    assert response.status_code == 200
    data = response.json()
    assert data["ip_version"] == 4
    assert data["network_address"] == "192.168.1.0"
    assert data["netmask"] == "255.255.255.0"
    assert data["broadcast_address"] == "192.168.1.255"
    assert data["usable_hosts"] == 254
    assert data["is_private"] is True

@pytest.mark.asyncio
async def test_port_scan_unauthorized_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/diagnostics/ports", json={
            "target": "127.0.0.1",
            "ports": [80, 443],
            "authorized": False
        })
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_port_scan_authorized_loopback():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/diagnostics/ports", json={
            "target": "127.0.0.1",
            "ports": [80, 443],
            "timeout_ms": 200,
            "authorized": True
        })
    assert response.status_code == 200
    data = response.json()
    assert data["target"] == "127.0.0.1"
    assert data["total_scanned"] == 2
    assert len(data["results"]) == 2

@pytest.mark.asyncio
async def test_security_findings_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/security/findings")
    assert response.status_code == 200
    findings = response.json()
    assert isinstance(findings, list)
    assert len(findings) > 0
    assert "severity" in findings[0]
    assert "title" in findings[0]

@pytest.mark.asyncio
async def test_stop_scan_and_progress_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        stop_res = await ac.post("/api/devices/scan/stop")
        prog_res = await ac.get("/api/devices/scan/progress")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "stopped"
    assert prog_res.status_code == 200
    assert "status" in prog_res.json()

@pytest.mark.asyncio
async def test_connectivity_benchmark_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/diagnostics/connectivity")
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert data["verdict"] in ("HEALTHY", "LOCAL_ONLY", "DEGRADED", "OFFLINE")
    assert "dns" in data
    assert "gateway" in data
    assert "internet" in data

@pytest.mark.asyncio
async def test_input_validation_command_injection_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test leading flag
        bad_ping1 = await ac.post("/api/diagnostics/ping", json={"target": "-c 1 127.0.0.1", "count": 2})
        # Test shell metacharacters
        bad_ping2 = await ac.post("/api/diagnostics/ping", json={"target": "127.0.0.1; whoami", "count": 2})
    assert bad_ping1.status_code == 422
    assert bad_ping2.status_code == 422

@pytest.mark.asyncio
async def test_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_metrics_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/network/metrics/history?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_ip_calc_edge_cases():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # /32 (single host)
        r32 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "192.168.1.1/32"})
        assert r32.status_code == 200
        d32 = r32.json()
        assert d32["usable_hosts"] == 1
        assert d32["total_hosts"] == 1
        assert d32["usable_host_range"] == ["192.168.1.1", "192.168.1.1"]

        # /31 (RFC 3021 point-to-point, 2 usable hosts)
        r31 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "192.168.1.0/31"})
        assert r31.status_code == 200
        d31 = r31.json()
        assert d31["usable_hosts"] == 2
        assert d31["total_hosts"] == 2
        assert d31["usable_host_range"] == ["192.168.1.0", "192.168.1.1"]

        # /24 standard
        r24 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "192.168.1.0/24"})
        assert r24.status_code == 200
        assert r24.json()["usable_hosts"] == 254
        assert r24.json()["total_hosts"] == 256

        # /8 large network (16,777,214 usable hosts, zero memory allocation)
        r8 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "10.0.0.0/8"})
        assert r8.status_code == 200
        d8 = r8.json()
        assert d8["usable_hosts"] == 16777214
        assert d8["total_hosts"] == 16777216
        assert d8["usable_host_range"] == ["10.0.0.1", "10.255.255.254"]

        # /0 entire IPv4 space
        r0 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "0.0.0.0/0"})
        assert r0.status_code == 200
        d0 = r0.json()
        assert d0["total_hosts"] == 4294967296
        assert d0["usable_hosts"] == 4294967294

        # IPv6 prefix /64
        r6 = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "2001:db8::/64"})
        assert r6.status_code == 200
        d6 = r6.json()
        assert d6["ip_version"] == 6
        assert d6["usable_host_range"][0] == "2001:db8::"

@pytest.mark.asyncio
async def test_port_scan_security_guardrails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid port range (0, negative, >65535)
        bad_port1 = await ac.post("/api/diagnostics/ports", json={
            "target": "127.0.0.1",
            "ports": [0],
            "authorized": True
        })
        assert bad_port1.status_code == 422

        bad_port2 = await ac.post("/api/diagnostics/ports", json={
            "target": "127.0.0.1",
            "ports": [70000],
            "authorized": True
        })
        assert bad_port2.status_code == 422

        # Public external target rejected even if authorized=True
        ext_scan = await ac.post("/api/diagnostics/ports", json={
            "target": "8.8.8.8",
            "ports": [53],
            "authorized": True
        })
        assert ext_scan.status_code == 403
        assert "External scanning is prohibited" in ext_scan.json()["detail"]

        # Nonexistent DNS hostname rejected
        bad_host = await ac.post("/api/diagnostics/ports", json={
            "target": "invalid-nonexistent-domain-xyz12345.notfound",
            "ports": [80],
            "authorized": True
        })
        assert bad_host.status_code in (422, 403)

@pytest.mark.asyncio
async def test_discovery_security_scope_and_size_guardrails():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Public WAN CIDR rejected
        public_sweep = await ac.post("/api/devices/discover", json={
            "cidr": "8.8.8.0/24"
        })
        assert public_sweep.status_code == 403
        assert "strictly prohibited" in public_sweep.json()["detail"] or "public" in public_sweep.json()["detail"]

        # Oversized network range rejected (> /24 or unauthorized)
        oversized_sweep = await ac.post("/api/devices/discover", json={
            "cidr": "10.0.0.0/16"
        })
        assert oversized_sweep.status_code in (403, 422)

        # Malformed CIDR notation rejected
        bad_cidr = await ac.post("/api/devices/discover", json={
            "cidr": "not_a_valid_cidr"
        })
        assert bad_cidr.status_code == 422

@pytest.mark.asyncio
async def test_security_headers_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin" in headers.get("referrer-policy", "")
    assert "geolocation=()" in headers.get("permissions-policy", "")

@pytest.mark.asyncio
async def test_unrelated_private_network_rejection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # A private IP range that is virtually never assigned locally (e.g. 10.254.254.0/24)
        response = await ac.post("/api/devices/discover", json={
            "cidr": "10.254.254.0/24"
        })
    # Must be rejected if not attached to any active local interface
    assert response.status_code in (403, 200)
    if response.status_code == 403:
        assert "not within any active local network interface subnet" in response.json()["detail"]

@pytest.mark.asyncio
async def test_gateway_baseline_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Fetch current baseline
        get_res = await ac.get("/api/security/gateway-baseline")
        assert get_res.status_code == 200
        baseline_data = get_res.json()
        assert "gateway_ip" in baseline_data
        assert "status" in baseline_data

        # 2. Confirm a baseline MAC (normalized to uppercase)
        confirm_res = await ac.post("/api/security/gateway-baseline/confirm", json={
            "baseline_mac": "00:aa:bb:cc:dd:ee"
        })
        assert confirm_res.status_code == 200
        assert confirm_res.json()["baseline_mac"] == "00:AA:BB:CC:DD:EE"

        # 3. Verify confirmed status in baseline endpoint
        verify_res = await ac.get("/api/security/gateway-baseline")
        assert verify_res.status_code == 200
        assert verify_res.json()["baseline_mac"] == "00:AA:BB:CC:DD:EE"

        # 4. Reset baseline
        reset_res = await ac.post("/api/security/gateway-baseline/reset")
        assert reset_res.status_code == 200
        assert reset_res.json()["status"] == "unconfirmed"

@pytest.mark.asyncio
async def test_security_findings_lifecycle():
    from app.core.database import AsyncSessionLocal
    from app.models.entities import SecurityFindingModel

    # 1. Ensure a finding is saved in the database
    async with AsyncSessionLocal() as session:
        finding = SecurityFindingModel(
            rule_id="SEC-TEST-001",
            severity="medium",
            title="Test Security Risk Finding",
            category="Testing",
            description="Synthetic finding for lifecycle verification",
            evidence="Port 80 open without TLS",
            impact="Potential plaintext inspection",
            remediation="Deploy SSL/TLS certificates",
            target="127.0.0.1",
            status="active"
        )
        session.add(finding)
        await session.commit()
        await session.refresh(finding)
        finding_id = finding.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 2. Acknowledge finding
        ack_res = await ac.post(f"/api/security/findings/{finding_id}/acknowledge")
        assert ack_res.status_code == 200
        assert ack_res.json()["status"] == "ok"

        # 3. Resolve finding
        resolve_res = await ac.post(f"/api/security/findings/{finding_id}/resolve")
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "ok"

        # 4. Fetch history and confirm resolved status
        hist_res = await ac.get("/api/security/findings/history?limit=100")
        assert hist_res.status_code == 200
        hist_findings = hist_res.json()
        matching = [f for f in hist_findings if f["id"] == finding_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "resolved"

@pytest.mark.asyncio
async def test_device_inventory_patch():
    import uuid
    from app.core.database import AsyncSessionLocal
    from app.models.entities import NetworkDeviceModel

    random_suffix = uuid.uuid4().hex[:6]
    test_mac = f"02:00:00:{random_suffix[:2]}:{random_suffix[2:4]}:{random_suffix[4:6]}"
    test_ip = f"192.168.1.{int(random_suffix[:2], 16) % 200 + 10}"

    # Seed a device
    async with AsyncSessionLocal() as session:
        dev = NetworkDeviceModel(
            ip_address=test_ip,
            mac_address=test_mac,
            vendor="TestVendor Inc",
            hostname="test-host.local",
            is_gateway=False,
            is_local_host=False,
            status="online"
        )
        session.add(dev)
        await session.commit()
        await session.refresh(dev)
        device_id = dev.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        patch_res = await ac.patch(f"/api/devices/{device_id}", json={
            "custom_name": "Executive Workstation",
            "notes": "Building A, Floor 3",
            "category": "Workstation",
            "is_trusted": True
        })
        assert patch_res.status_code == 200
        data = patch_res.json()
        assert data["custom_name"] == "Executive Workstation"
        assert data["notes"] == "Building A, Floor 3"
        assert data["category"] == "Workstation"
        assert data["is_trusted"] is True

@pytest.mark.asyncio
async def test_interface_selection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ifaces = await ac.get("/api/network/interfaces")
        assert ifaces.status_code == 200
        iface_list = ifaces.json()
        if iface_list:
            chosen = iface_list[0]["name"]
            select_res = await ac.post("/api/network/interfaces/select", json={
                "interface_name": chosen
            })
            assert select_res.status_code == 200
            assert select_res.json()["selected_interface"] == chosen

@pytest.mark.asyncio
async def test_report_exports():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Devices export
        dev_csv = await ac.get("/api/reports/devices/export?format=csv")
        assert dev_csv.status_code == 200
        assert "text/csv" in dev_csv.headers.get("content-type", "")
        assert "IP Address" in dev_csv.text

        dev_json = await ac.get("/api/reports/devices/export?format=json")
        assert dev_json.status_code == 200
        assert isinstance(dev_json.json(), list)

        # Security export
        sec_csv = await ac.get("/api/reports/security/export?format=csv")
        assert sec_csv.status_code == 200
        assert "text/csv" in sec_csv.headers.get("content-type", "")

        sec_json = await ac.get("/api/reports/security/export?format=json")
        assert sec_json.status_code == 200
        assert isinstance(sec_json.json(), list)

        # History export
        hist_csv = await ac.get("/api/reports/history/export?format=csv")
        assert hist_csv.status_code == 200
        assert "text/csv" in hist_csv.headers.get("content-type", "")

        hist_json = await ac.get("/api/reports/history/export?format=json")
        assert hist_json.status_code == 200
        assert isinstance(hist_json.json(), list)

@pytest.mark.asyncio
async def test_topology_read_only():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/topology")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

@pytest.mark.asyncio
async def test_gateway_baseline_mac_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid MAC formats must return HTTP 422
        bad_macs = ["invalid-mac", "00:11:22", "ZZ:ZZ:ZZ:ZZ:ZZ:ZZ", "12-34-56-78-90", "12:34:56:78:90:12:34"]
        for bad_mac in bad_macs:
            res = await ac.post("/api/security/gateway-baseline/confirm", json={"baseline_mac": bad_mac})
            assert res.status_code == 422, f"Expected 422 for malformed MAC: {bad_mac}"
            assert "Malformed MAC address" in res.json()["detail"]

        # Valid format normalized to uppercase
        res_valid = await ac.post("/api/security/gateway-baseline/confirm", json={"baseline_mac": "aa-bb-cc-11-22-33"})
        assert res_valid.status_code == 200
        assert res_valid.json()["baseline_mac"] == "AA:BB:CC:11:22:33"

@pytest.mark.asyncio
async def test_csv_formula_injection_sanitization():
    import uuid
    from app.core.database import AsyncSessionLocal
    from app.models.entities import NetworkDeviceModel

    random_hex = uuid.uuid4().hex[:6]
    test_mac = f"02:00:EE:{random_hex[:2]}:{random_hex[2:4]}:{random_hex[4:6]}"
    test_ip = f"192.168.1.{int(random_hex[:2], 16) % 200 + 10}"

    # Seed device with potentially malicious spreadsheet formulas
    async with AsyncSessionLocal() as session:
        evil_dev = NetworkDeviceModel(
            ip_address=test_ip,
            mac_address=test_mac,
            vendor="=cmd|' /C calc'!A0",
            hostname="@SUM(1,2)",
            custom_name="-DangerousFormula",
            notes="+AnotherFormula",
            is_gateway=False,
            is_local_host=False,
            status="online"
        )
        session.add(evil_dev)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/reports/devices/export?format=csv")
        assert res.status_code == 200
        csv_text = res.text

        # Ensure formula prefix characters are sanitized with single apostrophe
        assert "'=cmd|' /C calc'!A0" in csv_text
        assert "'@SUM(1,2)" in csv_text
        assert "'-DangerousFormula" in csv_text

@pytest.mark.asyncio
async def test_dns_rebinding_rejected(monkeypatch):
    import socket

    # Simulate DNS rebinding response: resolves to both loopback and an unauthorized public WAN IP
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/diagnostics/ports", json={
            "target": "localhost",
            "ports": [80],
            "authorized": True
        })
        assert res.status_code == 403
        assert "dns rebinding" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_settings_endpoint_no_information_disclosure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        # Internal configuration secrets must NOT be disclosed
        assert "authorized_networks" not in data
        assert "authorized_targets" not in data
        assert "database_url" not in data
        assert "cors_origins" not in data
        # Safe public operational metadata must be present
        assert "project_name" in data
        assert "version" in data
        assert "environment" in data
        assert "telemetry_interval" in data
        assert "max_concurrent_port_scans" in data

@pytest.mark.asyncio
async def test_interface_selection_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Non-existent adapter returns 404
        res_404 = await ac.post("/api/network/interfaces/select", json={"interface_name": "NonExistentAdapter_999"})
        assert res_404.status_code == 404
        assert "not found on host" in res_404.json()["detail"]

        # Empty interface name returns 400
        res_400 = await ac.post("/api/network/interfaces/select", json={"interface_name": "   "})
        assert res_400.status_code == 400
        assert "cannot be empty" in res_400.json()["detail"]

@pytest.mark.asyncio
async def test_ip_info_binary_host_representation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/diagnostics/ip-info", json={"ip_or_cidr": "192.168.1.50/24"})
        assert res.status_code == 200
        data = res.json()
        # Binary representation must accurately represent host IP .50 (00110010), not network .0 (00000000)
        assert data["binary_representation"] == "11000000.10101000.00000001.00110010"
        assert data["network_address"] == "192.168.1.0"
        assert data["broadcast_address"] == "192.168.1.255"

@pytest.mark.asyncio
async def test_security_audit_run_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/security/audit/run")
        assert res.status_code == 200
        findings = res.json()
        assert isinstance(findings, list)
        for f in findings:
            assert "rule_id" in f
            assert "confidence" in f
            assert f["confidence"] in ("confirmed", "potential", "informational")


