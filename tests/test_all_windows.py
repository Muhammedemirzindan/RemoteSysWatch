from config.windows_devices import WINDOWS_DEVICES
from collectors.winrm_windows_collector import WinRMWindowsCollector

if __name__ == "__main__":
    for device in WINDOWS_DEVICES:
        collector = WinRMWindowsCollector(
            host=device["ip"],
            username=device["user"],
            password=device["password"],
        )
        data = collector.collect(device["name"])

        if data.status == "reachable":
            m = data.metrics
            print(
                f"[OK]   {device['name']:12} "
                f"cpu={m.cpu.usage_percent}% ({m.cpu.core_count} core)  "
                f"ram={m.ram.usage_percent}% ({m.ram.used_mb}/{m.ram.total_mb} MB)  "
                f"disk={m.disk.usage_percent}% ({m.disk.used_gb}/{m.disk.total_gb} GB)  "
                f"uptime={m.uptime_seconds}s  os={m.os.version}  ip={m.network.ip_address}"
            )
        else:
            print(f"[FAIL] {device['name']:12} {data.errors}")
