import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from collectors.winrm_windows_collector import WinRMWindowsCollector

if __name__ == "__main__":
    collector = WinRMWindowsCollector(
        host=os.environ["WIN_TARGET_HOST"],
        username=os.environ["WIN_TARGET_USER"],
        password=os.environ["WIN_TARGET_PASSWORD"],
    )
    data = collector.collect("windows7")
    print(data.to_dict())
