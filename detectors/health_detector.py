# detectors/health_detector.py
from config.thresholds import THRESHOLDS

class HealthDetector:
    def __init__(self):
        self.thresholds = THRESHOLDS

    def analyze(self, device_data):
        device_name = device_data.get("name", "Unknown")
        status = device_data.get("status")

        # 1. Reachability Kontrolü (En kritik durum)
        if status == "unreachable":
            return {
                "device": device_name,
                "state": "CRITICAL",
                "issues": ["DEVICE UNREACHABLE"]
            }

        issues = []
        overall_state = "OK"
        metrics = device_data.get("metrics", {})

        # 2. RAM Kontrolü
        ram_usage = metrics.get("ram", {}).get("usage_percent")
        if ram_usage is not None:
            if ram_usage > self.thresholds["ram"]["critical"]:
                issues.append(f"RAM {ram_usage}%")
                overall_state = "CRITICAL"
            elif ram_usage > self.thresholds["ram"]["warning"]:
                issues.append(f"RAM {ram_usage}%")
                if overall_state == "OK": overall_state = "WARNING"

        # 3. CPU Kontrolü
        cpu_usage = metrics.get("cpu", {}).get("usage_percent")
        if cpu_usage is not None:
            if cpu_usage > self.thresholds["cpu"]["critical"]:
                issues.append(f"CPU {cpu_usage}%")
                overall_state = "CRITICAL"
            elif cpu_usage > self.thresholds["cpu"]["warning"]:
                issues.append(f"CPU {cpu_usage}%")
                if overall_state == "OK": overall_state = "WARNING"

        # 4. Disk Kontrolü
        disk_usage = metrics.get("disk", {}).get("usage_percent")
        if disk_usage is not None:
            if disk_usage > self.thresholds["disk"]["critical"]:
                issues.append(f"Disk {disk_usage}%")
                overall_state = "CRITICAL"
            elif disk_usage > self.thresholds["disk"]["warning"]:
                issues.append(f"Disk {disk_usage}%")
                if overall_state == "OK": overall_state = "WARNING"

        return {
            "device": device_name,
            "state": overall_state,
            "issues": issues
        }

