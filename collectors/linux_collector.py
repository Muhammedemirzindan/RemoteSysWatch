import socket
import paramiko
from datetime import datetime, timezone

from models.device_data import DeviceData

LOCALE_PREFIX = "LANG=C LC_ALL=C "


class SSHLinuxCollector:
    def __init__(self, host, username, password=None, key_filename=None, port=22, timeout=5):
        self.host = host
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.timeout = timeout

    def _run(self, client, command, cmd_timeout=5):
        """Tek bir komutu çalıştırıp stdout'u temizlenmiş string olarak döner."""
        stdin, stdout, stderr = client.exec_command(LOCALE_PREFIX + command, timeout=cmd_timeout)
        return stdout.read().decode(errors="replace").strip()

    def collect(self, device_name, important_services=None):
        """important_services: ör. ['sshd', 'cron'] -> verilirse durumları toplanır.
        Verilmezse services boş kalır (opsiyonel özellik)."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        data = DeviceData(name=device_name, ip=self.host)
        data.timestamp = datetime.now(timezone.utc).isoformat()
        data.metrics.os.name = "linux"

        try:
            client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=self.timeout,
                banner_timeout=self.timeout,
                auth_timeout=self.timeout,
            )
            data.status = "reachable"
            # ---- CPU ----
            cpu_out = self._run(client, "vmstat 1 2 | tail -1 | awk '{print 100-$15}'", cmd_timeout=6)
            if cpu_out:
                data.metrics.cpu.usage_percent = round(float(cpu_out), 2)

            load_out = self._run(client, "cat /proc/loadavg")
            if load_out:
                parts = load_out.split()
                data.metrics.cpu.load_1m = float(parts[0])
                data.metrics.cpu.load_5m = float(parts[1])
                data.metrics.cpu.load_15m = float(parts[2])

            core_out = self._run(client, "nproc")
            if core_out:
                data.metrics.cpu.core_count = int(core_out)

            # ---- RAM (total, used, available - tek komutla) ----
            ram_out = self._run(client, "free -m | awk 'NR==2{print $2, $3, $7}'")
            if ram_out:
                total, used, available = map(float, ram_out.split())
                data.metrics.ram.total_mb = total
                data.metrics.ram.used_mb = used
                data.metrics.ram.available_mb = available
                if total:
                    data.metrics.ram.usage_percent = round((used / total) * 100, 2)

            # ---- Disk (/ mount noktası) ----
            disk_out = self._run(client, "df -BG / | awk 'NR==2{print $2, $3, $5}'")
            if disk_out:
                total, used, pct = disk_out.split()
                data.metrics.disk.total_gb = float(total.replace('G', ''))
                data.metrics.disk.used_gb = float(used.replace('G', ''))
                data.metrics.disk.usage_percent = float(pct.replace('%', ''))

            # ---- Uptime ----
            uptime_out = self._run(client, "cat /proc/uptime | awk '{print $1}'")
            if uptime_out:
                data.metrics.uptime_seconds = int(float(uptime_out))

            # ---- Hostname / OS sürümü ----
            data.metrics.os.hostname = self._run(client, "hostname") or None
            os_version = self._run(client, "grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"'")
            data.metrics.os.version = os_version or None
            # ---- Network (internete çıkan birincil arayüz) ----
            iface = self._run(client, "ip route get 1.1.1.1 2>/dev/null | awk '{print $5; exit}'")
            if iface:
                data.metrics.network.interface = iface
                ip_out = self._run(
                    client,
                    "ip -4 addr show %s | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'" % iface,
                )
                if ip_out:
                    data.metrics.network.ip_address = ip_out.splitlines()[0]

            # ---- Servisler (opsiyonel) ----
            if important_services:
                svc_list = " ".join(important_services)
                svc_out = self._run(client, f"systemctl is-active {svc_list} 2>/dev/null")
                statuses = svc_out.splitlines()
                for name, status in zip(important_services, statuses):
                    data.metrics.services[name] = status

        except paramiko.AuthenticationException:
            data.status = "unreachable"
            data.errors.append("SSH kimlik doğrulama hatası (kullanıcı adı / şifre / anahtar yanlış)")
        except (paramiko.SSHException, socket.timeout, socket.error, OSError) as e:
            data.status = "unreachable"
            data.errors.append(f"SSH bağlantı hatası: {e}")
        except Exception as e:
            data.status = "unreachable"
            data.errors.append(f"Beklenmeyen hata: {e}")
        finally:
            client.close()

        return data
