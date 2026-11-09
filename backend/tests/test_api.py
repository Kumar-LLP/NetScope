import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.core.database import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()

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
        assert "outside authorized" in public_sweep.json()["detail"]

        # Oversized network range rejected (> /24)
        oversized_sweep = await ac.post("/api/devices/discover", json={
            "cidr": "10.0.0.0/16"
        })
        assert oversized_sweep.status_code == 422
        assert "Oversized network range" in oversized_sweep.json()["detail"]

        # Malformed CIDR notation rejected
        bad_cidr = await ac.post("/api/devices/discover", json={
            "cidr": "not_a_valid_cidr"
        })
        assert bad_cidr.status_code == 422
