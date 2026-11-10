import time
import threading
import sys
import socket
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid

from app.schemas.network import PacketStats, PacketCaptureStatusResponse

class PacketAnalyzer:
    """
    Optional, privacy-preserving packet-level analysis module.
    Inspects transport-layer protocols (TCP, UDP, ICMP, DNS) without capturing
    or logging plaintext payload contents or user credentials.
    Accurately reports when raw packet drivers (e.g. Npcap on Windows) or permissions
    are unavailable, without fabricating synthetic statistics.
    """
    def __init__(self):
        self.is_capturing = False
        self.session_id: Optional[str] = None
        self.interface_name: Optional[str] = None
        self.start_time: Optional[float] = None
        self.stats = PacketStats()
        self.last_error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def is_supported(self) -> Tuple[bool, str]:
        """
        Tests whether raw packet capture capabilities are genuinely supported in the current environment.
        Verifies both library presence and underlying OS driver/privilege availability.
        """
        try:
            import scapy.all as scapy
        except ImportError:
            return False, "Scapy library is not installed in the Python environment."
        except Exception as e:
            return False, f"Failed to initialize packet analysis library: {str(e)}"

        # Windows platform verification: Check for active WinPcap / Npcap driver
        if sys.platform == "win32":
            use_pcap = getattr(scapy.conf, "use_pcap", False)
            l2_name = getattr(scapy.conf.L2listen, "__name__", str(scapy.conf.L2listen))
            if not use_pcap or "NotAvailableSocket" in l2_name or "missing" in str(scapy.conf.L2listen).lower():
                return False, "Npcap driver is not installed on Windows. Install Npcap in WinPcap API-compatible mode to enable packet capture."
            return True, "Npcap packet capture driver available."

        # Linux / POSIX platform verification: Check raw socket capability
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            test_sock.close()
            return True, "Raw packet capture socket capability confirmed."
        except PermissionError:
            return False, "Raw packet capture requires elevated privileges (CAP_NET_RAW or root on Linux)."
        except Exception as e:
            return False, f"Raw socket capability unavailable: {str(e)}"

    def start_capture(self, iface_name: str) -> PacketCaptureStatusResponse:
        """
        Starts an opt-in continuous packet capture session on the specified interface.
        """
        with self._lock:
            if self.is_capturing:
                return self.get_status()

            supported, reason = self.is_supported()
            if not supported:
                self.last_error = reason
                return PacketCaptureStatusResponse(
                    is_capturing=False,
                    supported=False,
                    session_id=None,
                    interface_name=iface_name,
                    stats=self.stats,
                    note=f"Packet capture unsupported: {reason} (Standard user-mode operation active).",
                    error_message=reason
                )

            self.session_id = str(uuid.uuid4())[:8]
            self.interface_name = iface_name
            self.start_time = time.perf_counter()
            self.stats = PacketStats()
            self.last_error = None
            self.is_capturing = True
            self._stop_event.clear()

        def _capture_worker():
            try:
                import scapy.all as scapy

                def _process_packet(pkt):
                    if self._stop_event.is_set():
                        return
                    with self._lock:
                        self.stats.total_packets += 1
                        pkt_len = len(pkt)
                        self.stats.total_bytes += pkt_len

                        if pkt.haslayer(scapy.TCP):
                            self.stats.tcp_packets += 1
                            self.stats.protocols["TCP"] = self.stats.protocols.get("TCP", 0) + 1
                        elif pkt.haslayer(scapy.UDP):
                            self.stats.udp_packets += 1
                            self.stats.protocols["UDP"] = self.stats.protocols.get("UDP", 0) + 1
                            if pkt.haslayer(scapy.DNS):
                                self.stats.dns_packets += 1
                                self.stats.protocols["DNS"] = self.stats.protocols.get("DNS", 0) + 1
                        elif pkt.haslayer(scapy.ICMP):
                            self.stats.icmp_packets += 1
                            self.stats.protocols["ICMP"] = self.stats.protocols.get("ICMP", 0) + 1
                        else:
                            self.stats.other_packets += 1
                            proto_name = type(pkt.payload).__name__
                            self.stats.protocols[proto_name] = self.stats.protocols.get(proto_name, 0) + 1

                        if self.start_time:
                            self.stats.duration_seconds = round(time.perf_counter() - self.start_time, 2)

                # Continuous capture loop until stop event is signaled
                while not self._stop_event.is_set():
                    scapy.sniff(
                        iface=iface_name,
                        prn=_process_packet,
                        stop_filter=lambda p: self._stop_event.is_set(),
                        store=False,
                        timeout=2.0
                    )
            except Exception as e:
                with self._lock:
                    self.last_error = str(e)
            finally:
                with self._lock:
                    self.is_capturing = False

        self._thread = threading.Thread(target=_capture_worker, daemon=True)
        self._thread.start()

        return self.get_status()

    def stop_capture(self) -> PacketCaptureStatusResponse:
        """Stops the active capture session gracefully and computes final duration."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.5)

        with self._lock:
            self.is_capturing = False
            if self.start_time:
                self.stats.duration_seconds = round(time.perf_counter() - self.start_time, 2)

        return self.get_status()

    def get_status(self) -> PacketCaptureStatusResponse:
        """Returns the live capture status and thread-safe protocol statistics."""
        supported, reason = self.is_supported()

        with self._lock:
            if self.start_time and self.is_capturing:
                self.stats.duration_seconds = round(time.perf_counter() - self.start_time, 2)

            note_msg = None
            if not supported:
                note_msg = f"Packet capture requires Npcap on Windows or CAP_NET_RAW privileges on Linux. Zero-admin diagnostics mode active."

            stats_copy = self.stats.model_copy(deep=True)
            return PacketCaptureStatusResponse(
                is_capturing=self.is_capturing,
                supported=supported,
                session_id=self.session_id,
                interface_name=self.interface_name,
                stats=stats_copy,
                note=note_msg,
                error_message=self.last_error
            )

packet_analyzer = PacketAnalyzer()
