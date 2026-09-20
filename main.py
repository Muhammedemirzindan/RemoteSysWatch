import time
from concurrent.futures import ThreadPoolExecutor
from config.devices import LINUX_DEVICES
from config.windows_devices import WINDOWS_DEVICES
from collectors.linux_collector import SSHLinuxCollector
from collectors.windows_collector import WinRMWindowsCollector
from detectors.health_detector import HealthDetector
from investigators.detective import SystemDetective
from utils.state_manager import StateManager
from notifiers.telegram import TelegramNotifier

def fetch_linux(device):
    collector = SSHLinuxCollector(
        host=device["ip"],
        username=device["user"],
        password=device.get("password"),
        key_filename=device.get("key_path") or device.get("key_filename")
    )
    data = collector.collect(device_name=device["name"])
    return data.to_dict() if hasattr(data, "to_dict") else data.__dict__

def fetch_windows(device):
    collector = WinRMWindowsCollector(
        host=device["ip"],
        username=device["user"],
        password=device["password"]
    )
    data = collector.collect(device_name=device["name"])
    return data.to_dict() if hasattr(data, "to_dict") else data.__dict__

def main():
    detector = HealthDetector()
    detective = SystemDetective()
    state_mgr = StateManager()
    notifier = TelegramNotifier()
    all_devices = LINUX_DEVICES + WINDOWS_DEVICES

    print("--- İzleme Servisi Başlatıldı ---")

    while True:
        print(f"\n--- [İzleme Döngüsü: {time.strftime('%Y-%m-%d %H:%M:%S')}] ---")
        results = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            linux_futures = [executor.submit(fetch_linux, dev) for dev in LINUX_DEVICES]
            win_futures = [executor.submit(fetch_windows, dev) for dev in WINDOWS_DEVICES]

            for future in linux_futures + win_futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({"name": "Unknown", "status": "unreachable", "error": str(e)})

        for res in results:
            health = detector.analyze(res)
            device_name = health["device"]
            current_state = health["state"]

            # 1. Dedektif İncelemesi
            investigation_notes = []
            if current_state != "OK" and current_state != "unreachable" and res.get("metrics"):
                device_config = next((d for d in all_devices if d["name"] == device_name), None)
                os_name = res["metrics"]["os"]["name"]
                if device_config:
                    for issue in health["issues"]:
                        note = detective.investigate(device_config, issue, os_name)
                        if note:
                            investigation_notes.append(note)

            inv_str = f" {', '.join(investigation_notes)}" if investigation_notes else ""

            # 2. Terminal Çıktısı
            if current_state == "OK":
                print(f"[OK] {device_name}")
            else:
                color = "\033[93m" if current_state == "WARNING" else "\033[91m"
                issues_str = " | ".join(health["issues"])
                print(f"[{color}{current_state}\033[0m] {device_name} - {issues_str} \033[96m{inv_str}\033[0m")

            # 3. State Management & Telegram Bildirimi
            action = state_mgr.check_state_change(device_name, current_state)

            if action == "ALERT":
                msg = f"🚨 <b>ALERT [{current_state}]</b>\n<b>Cihaz:</b> {device_name}\n<b>Sorun:</b> {' | '.join(health['issues'])}\n<b>Detay:</b> {inv_str}"
                notifier.send_message(msg)
                print(f" -> 📱 Telegram ALERT gönderildi ({device_name})")

            elif action == "RECOVERY":
                msg = f"✅ <b>RECOVERY [OK]</b>\n<b>Cihaz:</b> {device_name}\nSistem normale döndü."
                notifier.send_message(msg)
                print(f" -> 📱 Telegram RECOVERY gönderildi ({device_name})")

        time.sleep(10)

if __name__ == "__main__":
    main()
