from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CPUMetrics:
    usage_percent: Optional[float] = None
    load_1m: Optional[float] = None
    load_5m: Optional[float] = None
    load_15m: Optional[float] = None
    core_count: Optional[int] = None


@dataclass
class RAMMetrics:
    usage_percent: Optional[float] = None
    used_mb: Optional[float] = None
    total_mb: Optional[float] = None
    available_mb: Optional[float] = None


@dataclass
class DiskMetrics:
    usage_percent: Optional[float] = None
    used_gb: Optional[float] = None
    total_gb: Optional[float] = None

@dataclass
class NetworkMetrics:
    interface: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class OSInfo:
    name: str = ""              # "linux" / "windows"
    version: Optional[str] = None
    hostname: Optional[str] = None


@dataclass
class Metrics:
    cpu: CPUMetrics = field(default_factory=CPUMetrics)
    ram: RAMMetrics = field(default_factory=RAMMetrics)
    disk: DiskMetrics = field(default_factory=DiskMetrics)
    network: NetworkMetrics = field(default_factory=NetworkMetrics)
    os: OSInfo = field(default_factory=OSInfo)
    uptime_seconds: Optional[int] = None
    services: Dict[str, str] = field(default_factory=dict)   # {"sshd": "active", ...}


@dataclass
class DeviceData:
    name: str
    ip: str
    status: str = "unknown"     # "reachable" | "unreachable"
    metrics: Metrics = field(default_factory=Metrics)
    errors: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "status": self.status,
            "timestamp": self.timestamp,
            "metrics": {
                "cpu": self.metrics.cpu.__dict__,
                "ram": self.metrics.ram.__dict__,
                "disk": self.metrics.disk.__dict__,
                "network": self.metrics.network.__dict__,
                "os": self.metrics.os.__dict__,
                "uptime_seconds": self.metrics.uptime_seconds,
                "services": self.metrics.services,
            },
            "errors": self.errors,
        }
