import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from curl_cffi import requests

BASE = "https://api.sofascore.com/api/v1"
OUT = Path("data")
OUT.mkdir(exist_ok=True)

def get_json(url):
    r = requests.get(
        url,
        timeout=15,
        impersonate="chrome",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
    )
    r.raise_for_status()
    return r.json()

def collect(event_id):
    snapshot = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id,
        "event": get_json(f"{BASE}/event/{event_id}"),
        "statistics": get_json(f"{BASE}/event/{event_id}/statistics"),
        "incidents": get_json(f"{BASE}/event/{event_id}/incidents"),
        "graph": get_json(f"{BASE}/event/{event_id}/graph"),
    }
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"{event_id}_{ts}.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python collector.py EVENT_ID")
        sys.exit(1)
    collect(sys.argv[1])
