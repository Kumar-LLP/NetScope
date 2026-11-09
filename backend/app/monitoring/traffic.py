import asyncio
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from fastapi import WebSocket

from app.schemas.network import TelemetryMessage, TelemetryBandwidth
from app.network.interfaces import get_active_interface_ip
from app.network.gateway import measure_target_latency, get_default_gateway

def format_speed(bytes_per_sec: float) -> str:
    """Formats byte rate into human readable string (KB/s or MB/s)."""
    if bytes_per_sec >= 1_048_576:
        return f"{bytes_per_sec / 1_048_576:.2f} MB/s"
    elif bytes_per_sec >= 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    else:
        return f"{bytes_per_sec:.0f} B/s"

def calculate_health_score(latency_ms: Optional[float], packet_loss: float = 0.0) -> int:
    """Computes a deterministic network health score between 0 and 100."""
    score = 100
    if latency_ms is None:
        return 20 # Disconnected or severe impairment
    if latency_ms > 150:
        score -= 40
    elif latency_ms > 80:
        score -= 20
    elif latency_ms > 40:
        score -= 10

    if packet_loss > 10:
        score -= 40
    elif packet_loss > 0:
        score -= int(packet_loss * 2)

    return max(10, min(100, score))

class TrafficMonitor:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_running: bool = False
        self._last_counters = psutil.net_io_counters()
        self._last_time = time.perf_counter()
        self.history: List[Dict] = []
        self.latest_telemetry: Optional[TelemetryMessage] = None

    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Immediately send latest telemetry if available
        if self.latest_telemetry:
            try:
                await websocket.send_text(self.latest_telemetry.model_dump_json())
            except Exception:
                pass

    def disconnect_client(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: TelemetryMessage):
        payload = message.model_dump_json()
        dead_connections = set()
        for conn in self.active_connections:
            try:
                await conn.send_text(payload)
            except Exception:
                dead_connections.add(conn)
        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def start_loop(self):
        """Continuous background task sampling network throughput at 1.5s intervals."""
        self.is_running = True
        gw = get_default_gateway() or "1.1.1.1"

        while self.is_running:
            try:
                await asyncio.sleep(1.5)
                current_time = time.perf_counter()
                elapsed = max(0.1, current_time - self._last_time)

                current_counters = psutil.net_io_counters()

                bytes_recv = current_counters.bytes_recv - self._last_counters.bytes_recv
                bytes_sent = current_counters.bytes_sent - self._last_counters.bytes_sent

                download_rate = max(0.0, bytes_recv / elapsed)
                upload_rate = max(0.0, bytes_sent / elapsed)

                self._last_counters = current_counters
                self._last_time = current_time

                # Measure current latency
                latency = measure_target_latency(gw, port=53, timeout_sec=0.5)

                active_ip = get_active_interface_ip() or "127.0.0.1"
                now_iso = datetime.now(timezone.utc).isoformat()

                msg = TelemetryMessage(
                    type="telemetry_update",
                    timestamp=now_iso,
                    bandwidth=TelemetryBandwidth(
                        download_bytes_per_sec=round(download_rate, 2),
                        upload_bytes_per_sec=round(upload_rate, 2),
                        download_formatted=format_speed(download_rate),
                        upload_formatted=format_speed(upload_rate),
                    ),
                    ping_ms=latency,
                    packet_loss_pct=0.0 if latency is not None else 100.0,
                    interface=active_ip,
                    is_connected=latency is not None
                )

                self.latest_telemetry = msg

                # Append to sliding window history (keep last 60 points)
                self.history.append({
                    "timestamp": now_iso,
                    "download_kbps": round(download_rate / 1024, 2),
                    "upload_kbps": round(upload_rate / 1024, 2),
                    "latency_ms": latency
                })
                if len(self.history) > 60:
                    self.history.pop(0)

                # Broadcast to UI clients
                if self.active_connections:
                    await self.broadcast(msg)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    def stop_loop(self):
        self.is_running = False

traffic_monitor = TrafficMonitor()
