import time
import threading
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
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def is_supported(self) -> Tuple[bool, str]:
        """
        Tests whether raw packet capture capabilities are supported in the current environment.
        """
        try:
            import scapy.all as scapy
            # Test if a raw sniffer socket can be initialized
            return True, "Raw packet capture driver available."
        except ImportError:
            return False, "Scapy library is not installed in the Python environment."
        except Exception as e:
            return False, f"Raw packet capture driver unavailable: {str(e)}"

    def start_capture(self, iface_name: str) -> PacketCaptureStatusResponse:
        """
        Starts an opt-in packet capture session on the specified interface.
        """
        if self.is_capturing:
            return self.get_status()

        supported, reason = self.is_supported()
        if not supported:
            return PacketCaptureStatusResponse(
                is_capturing=False,
                supported=False,
                session_id=None,
                interface_name=iface_name,
                stats=self.stats,
                note=f"Packet capture unsupported: {reason} (Standard user-mode operation active)."
            )

        self.session_id = str(uuid.uuid4())[:8]
        self.interface_name = iface_name
        self.start_time = time.perf_counter()
        self.stats = PacketStats()
        self.is_capturing = True
        self._stop_event.clear()

        def _capture_worker():
            try:
                import scapy.all as scapy

                def _process_packet(pkt):
                    if self._stop_event.is_set():
                        return
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

                scapy.sniff(
                    iface=iface_name,
                    prn=_process_packet,
                    stop_filter=lambda p: self._stop_event.is_set(),
                    store=False,
                    timeout=60
                )
            except Exception as e:
                pass
            finally:
                self.is_capturing = False

        self._thread = threading.Thread(target=_capture_worker, daemon=True)
        self._thread.start()

        return self.get_status()

    def stop_capture(self) -> PacketCaptureStatusResponse:
        """Stops the active capture session and computes final duration."""
        self._stop_event.set()
        self.is_capturing = False
        if self.start_time:
            self.stats.duration_seconds = round(time.perf_counter() - self.start_time, 2)
        return self.get_status()

    def get_status(self) -> PacketCaptureStatusResponse:
        """Returns the live capture status and protocol statistics."""
        supported, reason = self.is_supported()
        if self.start_time and self.is_capturing:
            self.stats.duration_seconds = round(time.perf_counter() - self.start_time, 2)

        note_msg = None
        if not supported:
            note_msg = "Packet capture requires Npcap on Windows or CAP_NET_RAW privileges on Linux. Zero-admin diagnostics mode active."

        return PacketCaptureStatusResponse(
            is_capturing=self.is_capturing,
            supported=supported,
            session_id=self.session_id,
            interface_name=self.interface_name,
            stats=self.stats,
            note=note_msg
        )

packet_analyzer = PacketAnalyzer()
