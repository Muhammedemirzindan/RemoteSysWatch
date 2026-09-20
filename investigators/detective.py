# investigators/detective.py
"""
SystemDetective
---------------
COLLECT -> DETECT -> INVESTIGATE -> DIAGNOSIS -> TELEGRAM -> RECOVERY

Bu modul, DETECT asamasinda bir problem tespit edildikten sonra devreye girer.
Amac: "RAM yuksek" demek yerine "RAM yuksek VE muhtemel sebebi X" diyebilmek.

Tasarim kurallari:
- Collector'dan bagimsiz calisir (sadece device_config + issue_string + os_name alir).
- Problem turune gore SADECE ilgili bilgiyi toplar (her seferinde her seyi taramaz).
- Linux: Ubuntu 18 uyumlu (systemctl/journalctl yoksa eski komutlara fallback yapar).
- Windows: Win7/PS2 uyumlu (Get-CimInstance/ConvertTo-Json KULLANILMAZ;
  bunun yerine Get-WmiObject ve Get-EventLog kullanilir).
- investigate() imzasi geriye donuk uyumlu: eski cagri yerleri (3 parametre) calismaya devam eder.
"""

import re
import socket
import subprocess

import paramiko
import winrm


class SystemDetective:

    # -----------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # -----------------------------------------------------------------
    def investigate(self, device_config, issue_string, os_name, service_name=None):
        issue_type = self._classify_issue(issue_string, service_name)

        if not service_name:
            service_name = self._guess_service_name(issue_string)

        try:
            if "linux" in (os_name or "").lower():
                return self._investigate_linux(device_config, issue_type, issue_string, service_name)
            elif "windows" in (os_name or "").lower():
                return self._investigate_windows(device_config, issue_type, issue_string, service_name)
            else:
                return "[Detay alinamadi: bilinmeyen OS tipi]"
        except Exception as e:
            return f"[Detay alinamadi: {e}]"

    # -----------------------------------------------------------------
    # ISSUE CLASSIFICATION (case-insensitive, genis anahtar kelime seti)
    # -----------------------------------------------------------------
    def _classify_issue(self, issue_string, service_name=None):
        text = (issue_string or "").lower()

        if service_name or any(k in text for k in ["service", "servis", "systemd", "daemon"]):
            return "service"
        if any(k in text for k in ["cpu", "islemci", "processor"]):
            return "cpu"
        if any(k in text for k in ["ram", "memory", "bellek", "mem "]):
            return "ram"
        if any(k in text for k in ["disk", "storage", "depolama", "drive", "partition", "mount"]):
            return "disk"
        if any(k in text for k in ["ping", "unreachable", "erisilemiyor", "erişilemiyor", "timeout",
                                    "down", "offline", "latency", "network"]):
            return "ping"
        return "general"

    def _guess_service_name(self, issue_string):
        # "service X is down" / "X servisi durdu" gibi metinlerden servis adini cikarmayi dener.
        if not issue_string:
            return None
        m = re.search(r"service[:\s]+([A-Za-z0-9_\-\.]+)", issue_string, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"([A-Za-z0-9_\-\.]+)\s+servis", issue_string, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    # ===================================================================
    # LINUX
    # ===================================================================
    def _connect_linux(self, device):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_path = device.get("key_path") or device.get("key_filename")
        if key_path:
            client.connect(device["ip"], username=device["user"], key_filename=key_path, timeout=6)
        else:
            client.connect(device["ip"], username=device["user"], password=device.get("password"), timeout=6)
        return client

    def _run(self, client, cmd, timeout=8):
        try:
            _, stdout, _ = client.exec_command(cmd, timeout=timeout)
            return stdout.read().decode(errors="ignore").strip()
        except Exception:
            return ""

    def _investigate_linux(self, device, issue_type, issue_string, service_name):
        # Ping/erisilebilirlik problemi icin hedefe SSH ile baglanmayi DENEMIYORUZ
        # (zaten baglanamiyoruz ki). Monitor sunucudan hedefe giden yolu kontrol ederiz.
        if issue_type == "ping":
            return self._investigate_ping(device)

        client = self._connect_linux(device)
        try:
            if issue_type == "cpu":
                return self._linux_cpu(client)
            elif issue_type == "ram":
                return self._linux_ram(client)
            elif issue_type == "disk":
                return self._linux_disk(client)
            elif issue_type == "service":
                return self._linux_service(client, service_name)
            else:
                return self._linux_general(client)
        finally:
            client.close()

    def _linux_logs(self, client, grep_term=None, n=8):
        # journalctl varsa onu kullan (Ubuntu 18+ destekler), yoksa dmesg/syslog'a dus.
        has_journalctl = self._run(client, "command -v journalctl")
        if has_journalctl:
            cmd = f"journalctl -p err..warning --no-pager -n {n}"
            if grep_term:
                cmd += f" | grep -i '{grep_term}'"
            logs = self._run(client, cmd)
            if logs:
                return logs
        # fallback: dmesg + /var/log/syslog
        logs = self._run(client, f"dmesg 2>/dev/null | tail -n {n}")
        if not logs:
            logs = self._run(client, f"tail -n {n} /var/log/syslog 2>/dev/null || tail -n {n} /var/log/messages 2>/dev/null")
        return logs

    def _linux_cpu(self, client):
        top = self._run(client, "ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 6")
        load = self._run(client, "cat /proc/loadavg")
        cores = self._run(client, "nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo")
        logs = self._linux_logs(client, n=6)

        top_proc = self._first_data_row(top)
        cause = ""
        if top_proc:
            name, cpu_pct = top_proc[1], self._safe_float(top_proc[2])
            if cpu_pct and cpu_pct > 50:
                cause = f"Muhtemel sebep: '{name}' process'i CPU'nun buyuk kismini tek basina tuketiyor (%{cpu_pct})."
            else:
                cause = "Muhtemel sebep: tek bir process degil, genel yuk/es zamanli islemler CPU'yu zorluyor olabilir."

        return self._format_diagnosis(
            problem="High CPU Usage",
            fields={
                "Cores": cores or "n/a",
                "Load Average (1/5/15m)": load or "n/a",
                "Top Processes (PID/Name/%CPU/%MEM)": top or "n/a",
                "Recent Logs": logs or "yok",
                "Possible Cause": cause or "Belirlenemedi",
            },
        )

    def _linux_ram(self, client):
        top = self._run(client, "ps -eo pid,comm,%mem,%cpu --sort=-%mem | head -n 6")
        mem = self._run(client, "free -m")
        logs = self._linux_logs(client, grep_term="oom", n=6)

        swap_used = self._parse_free_swap_used(mem)
        top_proc = self._first_data_row(top)
        cause = ""
        if swap_used and swap_used > 0:
            cause = f"Muhtemel sebep: sistem swap'a dusmus (swap kullanimi ~{swap_used}MB), asil darbogaz swap I/O olabilir."
        elif top_proc:
            name, mem_pct = top_proc[1], self._safe_float(top_proc[2])
            if mem_pct and mem_pct > 40:
                cause = f"Muhtemel sebep: '{name}' process'i bellegin buyuk kismini kullaniyor (%{mem_pct}), sizinti olasi."
        if not cause:
            cause = "Belirlenemedi"

        return self._format_diagnosis(
            problem="High RAM Usage",
            fields={
                "Memory (free -m)": mem or "n/a",
                "Top Processes (PID/Name/%MEM/%CPU)": top or "n/a",
                "OOM/Recent Logs": logs or "yok",
                "Possible Cause": cause,
            },
        )

    def _linux_disk(self, client):
        df_out = self._run(client, "df -h --output=source,size,used,avail,pcent,target 2>/dev/null || df -h")
        worst_mount = self._worst_disk_mount(df_out)
        top_dirs = ""
        if worst_mount:
            top_dirs = self._run(
                client,
                f"du -x -h --max-depth=1 {worst_mount} 2>/dev/null | sort -rh | head -n 6",
                timeout=15,
            )
        logs = self._linux_logs(client, grep_term="disk\\|i/o\\|filesystem", n=6)

        cause = f"En dolu bolum: {worst_mount}" if worst_mount else "Belirlenemedi"

        return self._format_diagnosis(
            problem="High Disk Usage",
            fields={
                "Disk Usage (df -h)": df_out or "n/a",
                "Top Usage in Fullest Mount": top_dirs or "n/a (izin/zaman asimi olabilir)",
                "Recent Logs": logs or "yok",
                "Possible Cause": cause,
            },
        )

    def _linux_service(self, client, service_name):
        if not service_name:
            return "[Detay alinamadi: servis adi belirlenemedi]"

        has_systemctl = self._run(client, "command -v systemctl")
        if has_systemctl:
            status = self._run(client, f"systemctl status {service_name} --no-pager -l | head -n 12")
            enabled = self._run(client, f"systemctl is-enabled {service_name} 2>/dev/null")
            logs = self._run(client, f"journalctl -u {service_name} --no-pager -n 8 2>/dev/null")
        else:
            status = self._run(client, f"service {service_name} status 2>&1")
            enabled = self._run(client, f"chkconfig --list {service_name} 2>/dev/null")
            logs = self._linux_logs(client, grep_term=service_name, n=8)

        return self._format_diagnosis(
            problem="Service Down",
            fields={
                "Service": service_name,
                "Status": status or "n/a",
                "Start Mode/Enabled": enabled or "n/a",
                "Recent Logs": logs or "yok",
            },
        )

    def _linux_general(self, client):
        os_info = self._run(client, "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME")
        hostname = self._run(client, "hostname")
        uptime = self._run(client, "uptime -p 2>/dev/null || uptime")
        cpu_ram = self._run(client, "free -m | head -n 2")
        disk = self._run(client, "df -h / 2>/dev/null | tail -n 1")
        logs = self._linux_logs(client, n=6)

        return self._format_diagnosis(
            problem="General System Issue",
            fields={
                "OS": os_info or "n/a",
                "Hostname": hostname or "n/a",
                "Uptime": uptime or "n/a",
                "Memory Summary": cpu_ram or "n/a",
                "Root Disk": disk or "n/a",
                "Recent Logs": logs or "yok",
            },
        )

    # ===================================================================
    # WINDOWS  (Win7 / PowerShell 2.0 uyumlu - Get-CimInstance / ConvertTo-Json YOK)
    # ===================================================================
    def _connect_windows(self, device):
        return winrm.Session(f"http://{device['ip']}:5985/wsman", auth=(device["user"], device["password"]))

    def _run_ps(self, session, script, timeout_note=""):
        try:
            result = session.run_ps(script)
            if result.status_code == 0:
                return result.std_out.decode(errors="ignore").strip()
            return ""
        except Exception:
            return ""

    def _investigate_windows(self, device, issue_type, issue_string, service_name):
        if issue_type == "ping":
            return self._investigate_ping(device)

        session = self._connect_windows(device)

        if issue_type == "cpu":
            return self._win_cpu(session)
        elif issue_type == "ram":
            return self._win_ram(session)
        elif issue_type == "disk":
            return self._win_disk(session)
        elif issue_type == "service":
            return self._win_service(session, service_name)
        else:
            return self._win_general(session)

    def _win_event_logs(self, session, n=8, source_filter=None):
        filter_clause = ""
        if source_filter:
            filter_clause = f' | Where-Object {{$_.Message -like "*{source_filter}*" -or $_.Source -like "*{source_filter}*"}}'
        script = (
            f"Get-EventLog -LogName System -EntryType Error,Warning -Newest 30{filter_clause} "
            f"| Select-Object -First {n} TimeGenerated, Source, EventID, Message "
            f"| Format-Table -Wrap -AutoSize | Out-String -Width 200"
        )
        return self._run_ps(session, script)

    def _win_cpu(self, session):
        top = self._run_ps(
            session,
            "Get-WmiObject Win32_PerfFormattedData_PerfProc_Process | "
            "Where-Object {$_.Name -ne '_Total' -and $_.Name -ne 'Idle'} | "
            "Sort-Object PercentProcessorTime -Descending | Select-Object -First 5 "
            "Name, IDProcess, PercentProcessorTime | Format-Table -AutoSize | Out-String -Width 200",
        )
        cores = self._run_ps(session, "(Get-WmiObject Win32_ComputerSystem).NumberOfLogicalProcessors")
        logs = self._win_event_logs(session, n=6)

        top_name, top_pct = self._first_win_table_row(top)
        cause = "Belirlenemedi"
        if top_name and top_pct and top_pct > 50:
            cause = f"Muhtemel sebep: '{top_name}' process'i CPU'nun buyuk kismini tek basina tuketiyor (%{top_pct})."

        return self._format_diagnosis(
            problem="High CPU Usage",
            fields={
                "Logical Cores": cores or "n/a",
                "Top Processes (Name/PID/%CPU)": top or "n/a",
                "Recent System Events": logs or "yok",
                "Possible Cause": cause,
            },
        )

    def _win_ram(self, session):
        top = self._run_ps(
            session,
            "Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5 "
            "Name, Id, @{Name='WorkingSetMB';Expression={[math]::Round($_.WorkingSet/1MB,1)}} "
            "| Format-Table -AutoSize | Out-String -Width 200",
        )
        mem = self._run_ps(
            session,
            "Get-WmiObject Win32_OperatingSystem | Select-Object "
            "@{Name='TotalMB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,0)}}, "
            "@{Name='FreeMB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,0)}} | Out-String",
        )
        pagefile = self._run_ps(
            session,
            "Get-WmiObject Win32_PageFileUsage | Select-Object Name, CurrentUsage, AllocatedBaseSize | Out-String",
        )
        logs = self._win_event_logs(session, n=6, source_filter="memory")

        cause = "Belirlenemedi"
        if pagefile and re.search(r"CurrentUsage\s*:\s*[1-9]", pagefile):
            cause = "Muhtemel sebep: pagefile aktif olarak kullaniliyor, sistem RAM yerine disk'e yazip okuyor olabilir."

        return self._format_diagnosis(
            problem="High RAM Usage",
            fields={
                "Memory (Total/Free MB)": mem or "n/a",
                "Pagefile Usage": pagefile or "n/a",
                "Top Processes (Name/PID/WorkingSetMB)": top or "n/a",
                "Recent System Events": logs or "yok",
                "Possible Cause": cause,
            },
        )

    def _win_disk(self, session):
        disks = self._run_ps(
            session,
            "Get-WmiObject Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID, "
            "@{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,1)}}, "
            "@{Name='FreeGB';Expression={[math]::Round($_.FreeSpace/1GB,1)}} | Format-Table -AutoSize | Out-String -Width 200",
        )
        logs = self._win_event_logs(session, n=6, source_filter="disk")

        worst_drive = self._worst_win_drive(disks)
        cause = f"En dolu surucu: {worst_drive}" if worst_drive else "Belirlenemedi"

        return self._format_diagnosis(
            problem="High Disk Usage",
            fields={
                "Drives (DeviceID/SizeGB/FreeGB)": disks or "n/a",
                "Recent System Events": logs or "yok",
                "Possible Cause": cause,
            },
        )

    def _win_service(self, session, service_name):
        if not service_name:
            return "[Detay alinamadi: servis adi belirlenemedi]"

        status = self._run_ps(
            session,
            f"Get-WmiObject Win32_Service -Filter \"Name='{service_name}'\" | "
            f"Select-Object Name, State, StartMode | Out-String",
        )
        logs = self._win_event_logs(session, n=8, source_filter=service_name)

        return self._format_diagnosis(
            problem="Service Down",
            fields={
                "Service": service_name,
                "Status/StartMode": status or "n/a",
                "Recent Related Events": logs or "yok",
            },
        )

    def _win_general(self, session):
        os_info = self._run_ps(
            session,
            "Get-WmiObject Win32_OperatingSystem | Select-Object Caption, Version | Out-String",
        )
        hostname = self._run_ps(session, "$env:COMPUTERNAME")
        uptime = self._run_ps(
            session,
            "$os = Get-WmiObject Win32_OperatingSystem; "
            "$boot = [Management.ManagementDateTimeConverter]::ToDateTime($os.LastBootUpTime); "
            "((Get-Date) - $boot).ToString()",
        )
        mem = self._run_ps(
            session,
            "Get-WmiObject Win32_OperatingSystem | Select-Object "
            "@{Name='TotalMB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,0)}}, "
            "@{Name='FreeMB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,0)}} | Out-String",
        )
        disk = self._run_ps(
            session,
            "Get-WmiObject Win32_LogicalDisk -Filter \"DeviceID='C:'\" | Select-Object "
            "@{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,1)}}, "
            "@{Name='FreeGB';Expression={[math]::Round($_.FreeSpace/1GB,1)}} | Out-String",
        )
        logs = self._win_event_logs(session, n=6)

        return self._format_diagnosis(
            problem="General System Issue",
            fields={
                "OS": os_info or "n/a",
                "Hostname": hostname or "n/a",
                "Uptime": uptime or "n/a",
                "Memory": mem or "n/a",
                "C: Drive": disk or "n/a",
                "Recent System Events": logs or "yok",
            },
        )

    # ===================================================================
    # PING / ERISILEBILIRLIK  (hedefe degil, hedefe giden yola bakariz -
    # cunku zaten SSH/WinRM ile hedefe baglanamiyoruz)
    # ===================================================================
    def _investigate_ping(self, device):
        ip = device.get("ip", "")
        ping_out, latency, reachable = self._ping_from_monitor(ip)
        route_out = self._route_from_monitor(ip)
        tcp_reachable = self._tcp_probe(ip)

        cause = "Hedef gercekten erisilemez durumda (ag/cihaz kaynakli olabilir)."
        if not route_out:
            cause = "Monitor sunucudan hedefe giden route bulunamadi - ag konfigurasyonu kontrol edilmeli."
        elif tcp_reachable:
            cause = "ICMP basarisiz ama TCP port acik - hedef muhtemelen ayakta, ping/ICMP filtrelenmis olabilir."

        return self._format_diagnosis(
            problem="Ping/Connectivity Issue",
            fields={
                "Target": ip,
                "Ping Result (from monitor)": ping_out or "yanit yok",
                "Latency": latency or "n/a",
                "Route to Target (monitor)": route_out or "n/a",
                "TCP Probe (port 22/3389)": "acik" if tcp_reachable else "kapali/erisilemedi",
                "Possible Cause": cause,
            },
        )

    def _ping_from_monitor(self, ip):
        if not ip:
            return "", "", False
        try:
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "2", ip],
                capture_output=True, text=True, timeout=10,
            )
            out = result.stdout.strip()
            reachable = result.returncode == 0
            latency_match = re.search(r"time=([\d.]+)\s*ms", out)
            latency = f"{latency_match.group(1)} ms" if latency_match else ""
            return out[-400:], latency, reachable
        except Exception:
            return "", "", False

    def _route_from_monitor(self, ip):
        if not ip:
            return ""
        try:
            result = subprocess.run(
                ["ip", "route", "get", ip],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _tcp_probe(self, ip, ports=(22, 3389)):
        for port in ports:
            try:
                with socket.create_connection((ip, port), timeout=3):
                    return True
            except Exception:
                continue
        return False

    # ===================================================================
    # HELPERS
    # ===================================================================
    def _format_diagnosis(self, problem, fields):
        lines = [f"Problem: {problem}"]
        for key, value in fields.items():
            value = (value or "n/a").strip()
            if len(value) > 500:
                value = value[:500] + " ...(kirpildi)"
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _first_data_row(self, ps_table_output):
        # "ps -eo pid,comm,%cpu,%mem" ciktisindan ilk veri satirini kolonlara ayirir.
        if not ps_table_output:
            return None
        lines = [l for l in ps_table_output.splitlines() if l.strip()]
        if not lines:
            return None
        return lines[0].split()

    def _safe_float(self, val):
        try:
            return float(val)
        except Exception:
            return None

    def _parse_free_swap_used(self, free_output):
        if not free_output:
            return None
        for line in free_output.splitlines():
            if line.lower().startswith("swap"):
                parts = line.split()
                if len(parts) >= 3:
                    return self._safe_float(parts[2])
        return None

    def _worst_disk_mount(self, df_output):
        # df -h ciktisinda kullanim yuzdesi en yuksek satirin mount noktasini bulur.
        if not df_output:
            return None
        worst_pct, worst_mount = -1, None
        for line in df_output.splitlines():
            m = re.search(r"(\d+)%\s+(\S+)\s*$", line)
            if m:
                pct = int(m.group(1))
                if pct > worst_pct:
                    worst_pct, worst_mount = pct, m.group(2)
        return worst_mount

    def _first_win_table_row(self, ps_table_output):
        # PowerShell Format-Table ciktisindan ilk veri satirini (Name, PID, Pct) ayiklar.
        if not ps_table_output:
            return None, None
        lines = [l for l in ps_table_output.splitlines() if l.strip()]
        # ilk 2 satir genelde basliktir (header + dashes)
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                pct = self._safe_float(parts[-1])
                return name, pct
        return None, None
    def _worst_win_drive(self, target):
        try:
            # Eğer halihazırda çekilmiş tablo metni geldiyse
            if isinstance(target, str):
                lines = [l.strip() for l in target.splitlines() if l.strip()]
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 3:
                        return f"{parts[0]} sürücüsü (Boyut: {parts[1]} GB, Boş: {parts[2]} GB)"
                return "C: sürücüsü"

            # Eğer WinRM session nesnesi geldiyse
            script = "Get-WmiObject Win32_LogicalDisk | Where-Object DriveType -eq 3 | ForEach-Object { $_.DeviceID + ' %' + [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 1) + ' dolu' }"
            result = target.run_ps(script)
            if result.status_code == 0 and result.std_out:
                return result.std_out.decode().strip().replace('\r\n', ', ')
            return "C: sürücüsü"
        except Exception:
            return "C: sürücüsü"
