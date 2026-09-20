import urllib.request
import urllib.error
import json
from config.telegram import TELEGRAM_CONFIG

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_CONFIG.get("bot_token")
        self.chat_id = TELEGRAM_CONFIG.get("chat_id")
        self.enabled = TELEGRAM_CONFIG.get("enabled", False)

    def send_message(self, text):
        if not self.enabled or not self.token or "BURAYA" in self.token:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        safe_text = text.replace("<b>", "").replace("</b>", "")

        payload = {
            "chat_id": self.chat_id,
            "text": safe_text
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5):
                pass
        except urllib.error.HTTPError as e:
            error_response = e.read().decode('utf-8')
            print(f"[\033[91mTelegram Hata Detayı\033[0m] {error_response}")
        except Exception as e:
            print(f"[\033[91mTelegram Hata\033[0m] {e}")
