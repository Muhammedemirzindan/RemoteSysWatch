from config.devices import LINUX_DEVICES
from collectors.ssh_linux_collector import SSHLinuxCollector

if __name__ == "__main__":
    for device in LINUX_DEVICES:
        collector = SSHLinuxCollector(
            host=device["ip"],
            username=device["user"],
            password=device["password"],
        )
        data = collector.collect(device["name"])

        if data.reachable:
            print(f"[OK]   {device['name']:12} cpu={data.cpu}%  ram={data.ram}%  disk={data.disk}%")
        else:
            print(f"[FAIL] {device['name']:12} {data.events}")
