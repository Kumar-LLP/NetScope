from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, BigInteger
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class NetworkInterfaceModel(Base):
    __tablename__ = "network_interfaces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    netmask = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    is_default = Column(Boolean, default=False)
    is_up = Column(Boolean, default=True)
    speed_mbps = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    metrics = relationship("NetworkMetricModel", back_populates="interface", cascade="all, delete-orphan")


class NetworkDeviceModel(Base):
    __tablename__ = "network_devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip_address = Column(String(45), nullable=False, index=True)
    mac_address = Column(String(17), unique=True, nullable=True, index=True)
    vendor = Column(String(255), default="Unknown")
    hostname = Column(String(255), nullable=True)
    is_gateway = Column(Boolean, default=False)
    is_local_host = Column(Boolean, default=False)
    status = Column(String(32), default="online")
    first_seen = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow, onupdate=utcnow)

    scan_results = relationship("ScanResultModel", back_populates="device")
    security_findings = relationship("SecurityFindingModel", back_populates="device")


class NetworkScanModel(Base):
    __tablename__ = "network_scans"

    id = Column(String(64), primary_key=True)
    scan_type = Column(String(32), nullable=False) # 'device_discovery', 'port_scan'
    target_range = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="in_progress") # 'in_progress', 'completed', 'failed', 'stopped'
    total_targets = Column(Integer, default=0)
    found_targets = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

    results = relationship("ScanResultModel", back_populates="scan", cascade="all, delete-orphan")
    port_diagnostics = relationship("PortDiagnosticModel", back_populates="scan", cascade="all, delete-orphan")


class ScanResultModel(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scan_id = Column(String(64), ForeignKey("network_scans.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=True)
    ip_address = Column(String(45), nullable=False)
    mac_address = Column(String(17), nullable=True)
    response_time_ms = Column(Float, nullable=True)
    discovered_at = Column(DateTime, default=utcnow)

    scan = relationship("NetworkScanModel", back_populates="results")
    device = relationship("NetworkDeviceModel", back_populates="scan_results")


class NetworkMetricModel(Base):
    __tablename__ = "network_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interface_id = Column(Integer, ForeignKey("network_interfaces.id"), nullable=True)
    download_bytes_sec = Column(Float, nullable=False, default=0.0)
    upload_bytes_sec = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, default=0.0)
    total_bytes_sent = Column(BigInteger, nullable=False, default=0)
    total_bytes_recv = Column(BigInteger, nullable=False, default=0)
    timestamp = Column(DateTime, default=utcnow, index=True)

    interface = relationship("NetworkInterfaceModel", back_populates="metrics")


class PingResultModel(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    target = Column(String(255), nullable=False)
    packets_sent = Column(Integer, nullable=False)
    packets_received = Column(Integer, nullable=False)
    min_rtt_ms = Column(Float, nullable=True)
    avg_rtt_ms = Column(Float, nullable=True)
    max_rtt_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=False, default=0.0)
    raw_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class DNSResultModel(Base):
    __tablename__ = "dns_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain = Column(String(255), nullable=False)
    record_type = Column(String(16), nullable=False)
    resolved_server = Column(String(64), nullable=True)
    records_json = Column(Text, nullable=False)
    query_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class PortDiagnosticModel(Base):
    __tablename__ = "port_diagnostics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scan_id = Column(String(64), ForeignKey("network_scans.id"), nullable=True, index=True)
    target_ip = Column(String(45), nullable=False)
    port = Column(Integer, nullable=False)
    state = Column(String(16), nullable=False) # 'open', 'closed', 'filtered'
    service_name = Column(String(64), nullable=True)
    banner = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    scan = relationship("NetworkScanModel", back_populates="port_diagnostics")


class SecurityFindingModel(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=True)
    rule_id = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False) # 'critical', 'high', 'medium', 'low', 'info'
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    remediation = Column(Text, nullable=False)
    status = Column(String(32), default="active") # 'active', 'resolved', 'ignored'
    created_at = Column(DateTime, default=utcnow)

    device = relationship("NetworkDeviceModel", back_populates="security_findings")


class ApplicationSettingsModel(Base):
    __tablename__ = "application_settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
