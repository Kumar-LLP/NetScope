import asyncio
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
import logging
from fastapi import WebSocket

from app.schemas.network import TelemetryMessage, TelemetryBandwidth
from app.network.interfaces import get_network_interfaces
from app.network.gateway import (
    check_internet_connectivity,
    measure_tcp_connect_latency,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.entities import NetworkMetricModel

logger = logging.getLogger("netscope.traffic")

def format_speed(bytes_per_sec: float) -> str:
    """Formats raw bytes per second into human readable bandwidth representation."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.1f} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"

def calculate_health_score(latency_ms: Optional[float], packet_loss: float = 0.0) -> int:
    """Computes a deterministic network health score between 0 and 100."""
    score = 100
    if latency_ms is None:
        return 20
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
        # Independent client queues and tasks for slow-client isolation
        self.client_queues: Dict[WebSocket, asyncio.Queue] = {}
        self.client_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.is_running: bool = False
        self.selected_interface: Optional[str] = settings.DEFAULT_INTERFACE

        # Per-NIC previous counters: {iface_name: snetio}
        self._last_nic_counters: Dict[str, Any] = {}
        try:
            self._last_nic_counters = psutil.net_io_counters(pernic=True)
        except Exception:
            pass

        self._last_aggregate_counters = psutil.net_io_counters()
        self._last_time = time.perf_counter()
        self.history: List[Dict[str, Any]] = []
        self.latest_telemetry: Optional[TelemetryMessage] = None
        self._db_persist_counter: int = 0

    @property
    def active_connections(self) -> Set[WebSocket]:
        """Provides backwards-compatible set of active WebSocket connections."""
        return set(self.client_queues.keys())

    def get_auto_interface(self) -> str:
        """Determines the active interface name associated with the default route or live traffic."""
        try:
            interfaces = get_network_interfaces()
            def_iface = next((i for i in interfaces if i.is_default and i.is_up), None)
            if def_iface:
                return def_iface.name
            up_iface = next((i for i in interfaces if i.is_up and i.ip_address and not i.ip_address.startswith("127.")), None)
            if up_iface:
                return up_iface.name
            if interfaces:
                return interfaces[0].name
        except Exception:
            pass
        return "Default Adapter"

    def set_selected_interface(self, name: str):
        """Allows selecting a specific network interface for focused telemetry streaming."""
        self.selected_interface = name

    async def _client_sender(self, websocket: WebSocket, queue: asyncio.Queue):
        """Independent background sender task per client, isolating slow/buffering connections."""
        try:
            while True:
                payload = await queue.get()
                await websocket.send_text(payload)
                queue.task_done()
        except (asyncio.CancelledError, Exception):
            pass
        finally:
            self.disconnect_client(websocket)

    async def connect_client(self, websocket: WebSocket):
        """Accepts a new client connection, assigns an isolated bounded queue, and begins sender loop."""
        await websocket.accept()
        q: asyncio.Queue = asyncio.Queue(maxsize=10)
        task = asyncio.create_task(self._client_sender(websocket, q))
        self.client_queues[websocket] = q
        self.client_tasks[websocket] = task

        if self.latest_telemetry:
            try:
                q.put_nowait(self.latest_telemetry.model_dump_json())
            except asyncio.QueueFull:
                pass

    def disconnect_client(self, websocket: WebSocket):
        """Cleanly removes disconnected client and cancels its independent sender task."""
        if websocket in self.client_tasks:
            task = self.client_tasks.pop(websocket)
            if not task.done():
                task.cancel()
        self.client_queues.pop(websocket, None)

    async def broadcast(self, message: TelemetryMessage):
        """
        Broadcasts telemetry message to all connected clients.
        Drops oldest message if a slow client queue is full, ensuring non-blocking delivery.
        """
        payload = message.model_dump_json()
        dead_clients = []

        for ws, q in list(self.client_queues.items()):
            try:
                if q.full():
                    try:
                        q.get_nowait()  # Drop oldest unconsumed message to isolate slow client
                        q.task_done()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(payload)
            except Exception:
                dead_clients.append(ws)

        for ws in dead_clients:
            self.disconnect_client(ws)

    async def persist_metric_to_db(
        self,
        iface_name: str,
        download_rate: float,
        upload_rate: float,
        latency: Optional[float],
        loss: float,
        bytes_sent: int,
        bytes_recv: int
    ):
        """Asynchronously inserts network metric record into SQLite WAL database."""
        try:
            async with AsyncSessionLocal() as session:
                record = NetworkMetricModel(
                    interface_name=iface_name,
                    download_bytes_sec=download_rate,
                    upload_bytes_sec=upload_rate,
                    latency_ms=latency,
                    packet_loss_pct=loss,
                    total_bytes_sent=bytes_sent,
                    total_bytes_recv=bytes_recv,
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist metric snapshot to database: {e}", exc_info=True)

    async def start_loop(self):
        """Continuous background loop sampling per-interface throughput and genuine ICMP latency."""
        self.is_running = True

        while self.is_running:
            try:
                await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)
                current_time = time.perf_counter()
                elapsed = max(0.1, current_time - self._last_time)

                # 1. Sample per-interface I/O counters
                current_nic_counters = {}
                try:
                    current_nic_counters = psutil.net_io_counters(pernic=True)
                except Exception:
                    pass

                # Resolve selected or auto-detected active adapter
                active_iface_name = self.selected_interface or self.get_auto_interface()

                download_rate = 0.0
                upload_rate = 0.0
                curr_sent = 0
                curr_recv = 0

                if active_iface_name in current_nic_counters:
                    curr_io = current_nic_counters[active_iface_name]
                    prev_io = self._last_nic_counters.get(active_iface_name)

                    curr_sent = curr_io.bytes_sent
                    curr_recv = curr_io.bytes_recv

                    if prev_io and curr_recv >= prev_io.bytes_recv and curr_sent >= prev_io.bytes_sent:
                        bytes_recv_delta = curr_recv - prev_io.bytes_recv
                        bytes_sent_delta = curr_sent - prev_io.bytes_sent
                        download_rate = max(0.0, bytes_recv_delta / elapsed)
                        upload_rate = max(0.0, bytes_sent_delta / elapsed)

                self._last_nic_counters = current_nic_counters
                self._last_time = current_time

                # 2. Genuine connectivity & latency checks (offloaded to thread pool to avoid blocking event loop)
                is_net_online, icmp_latency, packet_loss = await asyncio.to_thread(check_internet_connectivity)
                tcp_latency = await asyncio.to_thread(measure_tcp_connect_latency, "1.1.1.1", 53, 0.3)

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
                    ping_ms=icmp_latency,
                    packet_loss_pct=packet_loss,
                    interface=active_iface_name,
                    is_connected=is_net_online,
                    tcp_latency_ms=tcp_latency
                )

                self.latest_telemetry = msg

                self.history.append({
                    "timestamp": now_iso,
                    "download_kbps": round(download_rate / 1024, 2),
                    "upload_kbps": round(upload_rate / 1024, 2),
                    "latency_ms": icmp_latency,
                    "interface": active_iface_name
                })
                if len(self.history) > 60:
                    self.history.pop(0)

                # Persist to database periodically (~15s)
                self._db_persist_counter += 1
                if self._db_persist_counter >= 10:
                    self._db_persist_counter = 0
                    asyncio.create_task(
                        self.persist_metric_to_db(
                            active_iface_name,
                            download_rate,
                            upload_rate,
                            icmp_latency,
                            packet_loss,
                            curr_sent,
                            curr_recv
                        )
                    )

                if self.client_queues:
                    await self.broadcast(msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in traffic monitor loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    def stop_loop(self):
        """Stops the monitoring loop and cancels all active client sender tasks."""
        self.is_running = False
        for task in list(self.client_tasks.values()):
            if not task.done():
                task.cancel()
        self.client_tasks.clear()
        self.client_queues.clear()

traffic_monitor = TrafficMonitor()
