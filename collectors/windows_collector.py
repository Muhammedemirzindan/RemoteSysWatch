import winrm
from datetime import datetime, timezone

from models.device_data import DeviceData


class WinRMWindowsCollector:
    def __init__(self, host, username, password, port=5985, use_https=False, transport="basic"):
        scheme = "https" if use_https else "http"
        endpoint = f"{scheme}://{host}:{port}/wsman"
        self.session = winrm.Session(endpoint, auth=(username, password), transport=transport)
        self.host = host

    def _run_ps(self, script):
        result = self.session.run_ps(script)
        out = result.std_out.decode(errors="replace").strip()
        err = result.std_err.decode(errors="replace").strip()
        return out, err, result.status_code

    @staticmethod
    def _to_float(value):
        """TR locale'li Windows'larda ondalık ayracı virgül olabilir ('31,1').
        PowerShell tarafında InvariantCulture zorluyoruz, burada da çift önlem."""
        return float(value.replace(",", "."))

    def collect(self, device_name, important_services=None):
        """important_services: ör. ['Spooler', 'wuauserv'] -> verilirse durumları toplanır."""
        data = DeviceData(name=device_name, ip=self.host)
        data.timestamp = datetime.now(timezone.utc).isoformat()
        data.metrics.os.name = "windows"

        try:
            out, err, code = self._run_ps("$env:COMPUTERNAME")
            if code != 0:
                raise RuntimeError(err or "WinRM komutu başarısız (status != 0)")
            data.status = "reachable"
            data.metrics.os.hostname = out or None

            # ---- CPU ----
            out, _, _ = self._run_ps(
                "(Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average)."
                "Average.ToString([System.Globalization.CultureInfo]::InvariantCulture)"
            )
            if out:
                data.metrics.cpu.usage_percent = self._to_float(out)

            out, _, _ = self._run_ps("(Get-WmiObject Win32_ComputerSystem).NumberOfLogicalProcessors")
                      if out:
                data.metrics.cpu.core_count = int(out)
            # Not: Windows'ta Unix tarzı load average (1/5/15dk) kavramı yok, boş kalıyor.

            # ---- RAM ----
            out, _, _ = self._run_ps(
                "$o = Get-WmiObject Win32_OperatingSystem; "
                "$total = [math]::Round($o.TotalVisibleMemorySize / 1024, 2); "
                "$avail = [math]::Round($o.FreePhysicalMemory / 1024, 2); "
                "$used = [math]::Round($total - $avail, 2); "
                "\"$($total.ToString([System.Globalization.CultureInfo]::InvariantCulture)) "
                "$($used.ToString([System.Globalization.CultureInfo]::InvariantCulture)) "
                "$($avail.ToString([System.Globalization.CultureInfo]::InvariantCulture))\""
            )
            if out:
                total, used, avail = (self._to_float(x) for x in out.split())
                data.metrics.ram.total_mb = total
                data.metrics.ram.used_mb = used
                data.metrics.ram.available_mb = avail
                if total:
                    data.metrics.ram.usage_percent = round((used / total) * 100, 2)

            # ---- Disk (C:) ----
            out, _, _ = self._run_ps(
                "$d = Get-WmiObject Win32_LogicalDisk -Filter \"DeviceID='C:'\"; "
                "$total = [math]::Round($d.Size / 1GB, 2); "
                "$used = [math]::Round(($d.Size - $d.FreeSpace) / 1GB, 2); "
                "$pct = [math]::Round((($d.Size - $d.FreeSpace) / $d.Size) * 100, 2); "
                "\"$($total.ToString([System.Globalization.CultureInfo]::InvariantCulture)) "
                "$($used.ToString([System.Globalization.CultureInfo]::InvariantCulture)) "
                "$($pct.ToString([System.Globalization.CultureInfo]::InvariantCulture))\""
            )
            if out:
                total, used, pct = (self._to_float(x) for x in out.split())
                data.metrics.disk.total_gb = total
                data.metrics.disk.used_gb = used
                data.metrics.disk.usage_percent = pct

            # ---- Uptime ----
            out, _, _ = self._run_ps(
                "$o = Get-WmiObject Win32_OperatingSystem; "
                "$boot = $o.ConvertToDateTime($o.LastBootUpTime); "
                "$span = (Get-Date) - $boot; "
                "$span.TotalSeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)"
            )
           if out:
                total, used, pct = (self._to_float(x) for x in out.split())
                data.metrics.disk.total_gb = total
                data.metrics.disk.used_gb = used
                data.metrics.disk.usage_percent = pct

            # ---- Uptime ----
            out, _, _ = self._run_ps(
                "$o = Get-WmiObject Win32_OperatingSystem; "
                "$boot = $o.ConvertToDateTime($o.LastBootUpTime); "
                "$span = (Get-Date) - $boot; "
                "$span.TotalSeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)"
            )
            if out:
                data.metrics.uptime_seconds = int(self._to_float(out))

            # ---- OS bilgisi ----
            out, _, _ = self._run_ps("(Get-WmiObject Win32_OperatingSystem).Caption")
            data.metrics.os.version = out or None

            # ---- Network (birincil arayüzün IPv4'ü) ----
            out, _, _ = self._run_ps(
                "(Get-WmiObject Win32_NetworkAdapterConfiguration | "
                "Where-Object {$_.IPEnabled -eq $true} | Select-Object -First 1).IPAddress[0]"
            )
            data.metrics.network.ip_address = out or None

            # ---- Servisler (opsiyonel) ----
            if important_services:
                svc_names = ",".join(f"'{s}'" for s in important_services)
                out, _, _ = self._run_ps(
                    f"Get-Service -Name {svc_names} -ErrorAction SilentlyContinue | "
                    "ForEach-Object { \"$($_.Name):$($_.Status)\" }"
                )
                for line in out.splitlines():
                    if ":" in line:
                        name, status = line.split(":", 1)
                        data.metrics.services[name] = status

        except Exception as e:
            data.status = "unreachable"
            data.errors.append(f"WinRM hatası: {e}")

        return data
