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
