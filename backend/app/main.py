import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api.endpoints import router as api_router
from app.monitoring.traffic import traffic_monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite WAL database and seed devices into memory & auditor
    await init_db()
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.entities import NetworkDeviceModel
        from app.security.auditor import security_auditor
        from app.api.endpoints import _cached_devices
        from app.schemas.network import DeviceSchema
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(NetworkDeviceModel))
            db_devs = res.scalars().all()
            security_auditor.load_history_from_devices([
                {"ip": d.ip_address, "mac": d.mac_address, "first_seen": d.first_seen}
                for d in db_devs
            ])
            _cached_devices.clear()
            _cached_devices.extend([
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
            ])
    except Exception:
        pass

    monitor_task = asyncio.create_task(traffic_monitor.start_loop())
    yield
    # Shutdown: Stop traffic monitor cleanly
    traffic_monitor.stop_loop()
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Professional Network Intelligence & Cybersecurity Monitoring Platform",
    lifespan=lifespan
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if settings.ENABLE_SECURITY_HEADERS:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router, prefix=settings.API_PREFIX)

# WebSocket for real-time telemetry streaming
@app.websocket("/ws/network")
async def websocket_network_endpoint(websocket: WebSocket):
    await traffic_monitor.connect_client(websocket)
    try:
        while True:
            # Keep connection open; receive client pings if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        traffic_monitor.disconnect_client(websocket)
    except Exception:
        traffic_monitor.disconnect_client(websocket)

@app.get("/")
async def root():
    return {
        "product": "NetScope",
        "tagline": "See Your Network. Understand Your Connections. Detect Potential Risks.",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
