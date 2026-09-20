# Unreachable Testi

## Monitor Tarafı
🚨 ALERT [CRITICAL]
Cihaz: ubuntu26
Sorun: DEVICE UNREACHABLE
Detay:  Problem: Ping/Connectivity Issue
Target: 192.168.174.13
Ping Result (from monitor): PING 192.168.174.13 (192.168.174.13) 56(84) bytes of data.
From 192.168.174.30 icmp_seq=1 Destination Host Unreachable
From 192.168.174.30 icmp_seq=2 Destination Host Unreachable
From 192.168.174.30 icmp_seq=3 Destination Host Unreachable

--- 192.168.174.13 ping statistics ---
3 packets transmitted, 0 received, +3 errors, 100% packet loss, time 2037ms
pipe 3
Latency: n/a
Route to Target (monitor): 192.168.174.13 dev ens33 src 192.168.174.30 uid 1000 
    cache
TCP Probe (port 22/3389): kapali/erisilemedi
Possible Cause: Hedef gercekten erisilemez durumda (ag/cihaz kaynakli olabilir).

---
# Cpu Testi

## Monitor Tarafı
[CRITICAL] ubuntu26 - CPU 100.0%  Problem: High CPU Usage
Cores: 1
Load Average (1/5/15m): 0.77 0.33 0.13 2/269 2110
Top Processes (PID/Name/%CPU/%MEM): PID COMMAND         %CPU %MEM
   1968 stress-ng-vm    99.1  3.7
      1 systemd          0.8  1.6
   1218 snapd            0.7  4.7
     12 kworker/u512:0-  0.3  0.0
    701 systemd-udevd    0.2  1.5
Recent Logs: Sep 20 11:01:52 ubuntu26 55-scsi-sg3_id.rules[1829]: WARNING: SCSI device sda has no device ID, consider changing .SCSI_ID_SERIAL_SRC in 00-scsi-sg3_config.rules
Sep 20 11:01:52 ubuntu26 multipath[1830]: sda: failed to get sysfs uid: No such file or directory
Sep 20 11:01:52 ubuntu26 multipath[1830]: sda: failed to get sgio uid: No such file or directory
Sep 20 11:02:02 ubuntu26 55-scsi-sg3_id.rules[1922]: WARNING: SCSI device sda has no device ID, consider changing .SCSI_ID_SERIAL_SRC in 00-scs ...(kirpildi)
Possible Cause: Muhtemel sebep: tek bir process degil, genel yuk/es zamanli islemler CPU'yu zorluyor olabilir.
 -> 📱 Telegram ALERT gönderildi (ubuntu26)

## Telegram Tarafı
🚨 ALERT [CRITICAL]
Cihaz: ubuntu26
Sorun: CPU 100.0%
Detay:  Problem: High CPU Usage
Cores: 1
Load Average (1/5/15m): 71.78 19.51 6.62 129/377 12701
Top Processes (PID/Name/%CPU/%MEM): PID COMMAND         %CPU %MEM
  12699 ps              50.0  0.4
  12642 sshd-session     2.7  1.2
  12402 stress-ng-cpu    0.8  0.9
  12399 stress-ng-cpu    0.8  0.9
  12400 stress-ng-cpu    0.8  0.9
Recent Logs: Sep 11 15:16:24 ubuntu26 multipath[1639]: sda: failed to get sysfs uid: No such file or directory
Sep 11 15:16:24 ubuntu26 multipath[1639]: sda: failed to get sgio uid: No such file or directory
Sep 11 15:16:34 ubuntu26 55-scsi-sg3_id.rules[1648]: WARNING: SCSI device sda has no device ID, consider changing .SCSI_ID_SERIAL_SRC in 00-scsi-sg3_config.rules
Sep 11 15:16:34 ubuntu26 multipath[1649]: sda: failed to get sysfs uid: No such file or directory
Sep 11 15:16:34 ubuntu26 multipath[1649]: sda ...(kirpildi)
Possible Cause: Muhtemel sebep: tek bir process degil, genel yuk/es zamanli islemler CPU'yu zorluyor olabilir.

---
# Ram Testi

## Monitor Tarafı
[CRITICAL] ubuntu26 - RAM 95.51%  Problem: High RAM Usage
Memory (free -m): total        used        free      shared  buff/cache   available
Mem:             981         924          48         567         721          57
Swap:           1226         540         686
Top Processes (PID/Name/%MEM/%CPU): PID COMMAND         %MEM %CPU
   1218 snapd            1.3  0.2
   3764 sshd-session     1.2  0.0
   3543 sshd-session     1.2  0.0
    645 systemd-journal  1.1  0.1
      1 systemd          1.0  0.2
OOM/Recent Logs: Sep 20 11:10:31 ubuntu26 kernel: Out of memory: Killed process 3323 (memtester) total-vm:821988kB, anon-rss:737544kB, file-rss:1964kB, shmem-rss:0kB, UID:0 pgtables:1500kB oom_score_adj:0
Possible Cause: Muhtemel sebep: sistem swap'a dusmus (swap kullanimi ~540.0MB), asil darbogaz swap I/O olabilir.
 -> 📱 Telegram ALERT gönderildi (ubuntu26)

---
## Telegram Tarafı
🚨 ALERT [CRITICAL]
Cihaz: ubuntu26
Sorun: RAM 95.51%
Detay:  Problem: High RAM Usage
Memory (free -m): total        used        free      shared  buff/cache   available
Mem:             981         924          48         567         721          57
Swap:           1226         540         686
Top Processes (PID/Name/%MEM/%CPU): PID COMMAND         %MEM %CPU
   1218 snapd            1.3  0.2
   3764 sshd-session     1.2  0.0
   3543 sshd-session     1.2  0.0
    645 systemd-journal  1.1  0.1
      1 systemd          1.0  0.2
OOM/Recent Logs: Sep 20 11:10:31 ubuntu26 kernel: Out of memory: Killed process 3323 (memtester) total-vm:821988kB, anon-rss:737544kB, file-rss:1964kB, shmem-rss:0kB, UID:0 pgtables:1500kB oom_score_adj:0
Possible Cause: Muhtemel sebep: sistem swap'a dusmus (swap kullanimi ~540.0MB), asil darbogaz swap I/O olabilir.

---
# Disk Doluluğu Testi

## Monitor Tarafı
[CRITICAL] ubuntu26 - Disk 100.0%  Problem: High Disk Usage
Disk Usage (df -h): Filesystem                         Size  Used Avail Use% Mounted on
tmpfs                              197M  1.3M  196M   1% /run
/dev/mapper/ubuntu--vg-ubuntu--lv  8.1G  8.1G     0 100% /
tmpfs                              491M     0  491M   0% /dev/shm
none                               1.0M     0  1.0M   0% /run/credentials/systemd-journald.service
none                               1.0M     0  1.0M   0% /run/credentials/systemd-resolved.service
tmpfs                              491M     0   ...(kirpildi)
Top Usage in Fullest Mount: 8.0G        /
2.6G    /usr
596M    /var
6.3M    /etc
44K     /home
24K     /snap
Recent Logs: 2026-09-20T11:15:21.401224+00:00 ubuntu26 systemd[1]: session-17.scope: Deactivated successfully.
2026-09-20T11:16:08.245145+00:00 ubuntu26 systemd[1]: Started session-18.scope - Session 18 of User ubuntu26.
2026-09-20T11:16:09.956041+00:00 ubuntu26 systemd[1]: session-18.scope: Deactivated successfully.
2026-09-20T11:16:09.959745+00:00 ubuntu26 rsyslogd[1375]: rsyslogd: file '/var/log/auth.log'[7] write error - see https://www.rsyslog.com/solving-rsyslog-write-errors/ for help OS error: No spac ...(kirpildi)
Possible Cause: En dolu bolum: /dev/mapper/ubuntu--vg-ubuntu--lv

## Telegram Tarafı
🚨 ALERT [CRITICAL]
Cihaz: ubuntu26
Sorun: Disk 100.0%
Detay:  Problem: High Disk Usage
Disk Usage (df -h): Filesystem                         Size  Used Avail Use% Mounted on
tmpfs                              197M   19M  178M  10% /run
/dev/mapper/ubuntu--vg-ubuntu--lv  8.1G  8.1G     0 100% /
tmpfs                              491M     0  491M   0% /dev/shm
none                               1.0M     0  1.0M   0% /run/credentials/systemd-journald.service
none                               1.0M     0  1.0M   0% /run/credentials/systemd-resolved.service
tmpfs                              491M     0   ...(kirpildi)
Top Usage in Fullest Mount: 8.0G /
2.6G /usr
596M /var
6.3M /etc
44K /home
24K /snap
Recent Logs: 2026-09-20T11:15:21.401224+00:00 ubuntu26 systemd[1]: session-17.scope: Deactivated successfully.
2026-09-20T11:16:08.245145+00:00 ubuntu26 systemd[1]: Started session-18.scope - Session 18 of User ubuntu26.
2026-09-20T11:16:09.956041+00:00 ubuntu26 systemd[1]: session-18.scope: Deactivated successfully.
2026-09-20T11:16:09.959745+00:00 ubuntu26 rsyslogd[1375]: rsyslogd: file '/var/log/auth.log'[7] write error - see https://www.rsyslog.com/solving-rsyslog-write-errors/ for help OS error: No spac ...(kirpildi)
Possible Cause: En dolu bolum: /dev/mapper/ubuntu--vg-ubuntu--lv


