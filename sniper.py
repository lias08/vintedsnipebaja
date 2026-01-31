import tls_client
import time
import threading
import json
import random
from datetime import datetime

# 🌍 GLOBAL RATE LIMITER (für alle Sniper)
class GlobalLimiter:
    def __init__(self, min_delay=1):  # 1 Sekunde Verzögerung für schnellere Anfragen
        self.lock = threading.Lock()
        self.last = 0
        self.min_delay = min_delay

    def wait(self):
        with self.lock:
            now = time.time()
            diff = now - self.last
            if diff < self.min_delay:
                time.sleep(self.min_delay - diff)
            self.last = time.time()


global_limiter = GlobalLimiter(min_delay=1)  # Setze die Verzögerung auf 1 Sekunde

# Mapping für den Zustand des Artikels
status_mapping = {
    "6": "Neu mit Etikett ✨",
    "new_with_tags": "Neu mit Etikett ✨",
    "1": "Neu ohne Etikett ✨",
    "new_without_tags": "Neu ohne Etikett ✨",
    "2": "Sehr gut 👌",
    "very_good": "Sehr gut 👌",
    "3": "Gut 👍",
    "good": "Gut 👍",
    "4": "Zufriedenstellend 🆗",
    "satisfactory": "Zufriedenstellend 🆗",
    "5": "Nicht akzeptabel 🚫",
    "not_acceptable": "Nicht akzeptabel 🚫"
}

class VintedSniper(threading.Thread):
    def __init__(self, url, callback):
        super().__init__(daemon=True)
        self.url = self._convert_url(url)
        self.callback = callback
        self.running = True

        self.seen = self.load_seen_items()
        self.initialized = False

        self.session = tls_client.Session(client_identifier="chrome_112")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9",
            "Referer": "https://www.vinted.de/",
            "Origin": "https://www.vinted.de",
        }
        self._bootstrap_session()

    def _bootstrap_session(self):
        try:
            print("🍪 Hole Vinted Cookies …")
            self.session.get("https://www.vinted.de", headers=self.headers)
            print("🍪 Cookies gesetzt")
        except Exception as e:
            print("⚠️ Cookie Fehler:", e)

    def stop(self):
        self.running = False

    def _convert_url(self, url):
        if "api/v2/catalog/items" in url:
            return url

        base = "https://www.vinted.de/api/v2/catalog/items"
        if "?" not in url:
            return f"{base}?order=newest_first&per_page=20"

        params = url.split("?", 1)[1]
        if "order=" not in params:
            params += "&order=newest_first"
        if "per_page=" not in params:
            params += "&per_page=20"

        return f"{base}?{params}"

    def load_seen_items(self):
        try:
            with open("seen_items.json", "r") as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()

    def save_seen_items(self):
        with open("seen_items.json", "w") as f:
            json.dump(list(self.seen), f)

    def run(self):
        print("🟢 Sniper Loop gestartet")
        print("🔗 API URL:", self.url)

        burst = 0
        last_top_id = None
        consecutive_403s = 0

        while self.running:
            try:
                global_limiter.wait()

                r = self.session.get(self.url, headers=self.headers)
                print("🌐 API Status:", r.status_code)

                if r.status_code == 403:
                    consecutive_403s += 1
                    print(f"⛔ 403 Block – Cooldown {consecutive_403s * 10}s")
                    time.sleep(consecutive_403s * 10)
                    if consecutive_403s > 3:
                        print("🔴 Viele 403s – längere Pause!")
                        time.sleep(30)
                    continue

                if r.status_code != 200:
                    time.sleep(10)
                    continue

                items = r.json().get("items", [])
                print("📥 Items erhalten:", len(items))

                if not items:
                    time.sleep(10)
                    continue

                top_id = items[0]["id"]

                if not self.initialized:
                    for item in items:
                        self.seen.add(item["id"])
                    self.initialized = True
                    last_top_id = top_id
                    print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                    time.sleep(5)
                    continue

                for item in items:
                    if item["id"] in self.seen:
                        continue
                    self.seen.add(item["id"])
                    print("🔥 Neues Item:", item.get("title"))
                    self.callback(item)

                if top_id != last_top_id:
                    delay = random.randint(6, 7)
                    burst += 1
                else:
                    delay = random.randint(10, 12)  # Anpassung für schnellere Durchläufe
                    burst = 0

                last_top_id = top_id

                if burst >= 5:
                    print("🧊 Burst Cooldown 30s")
                    time.sleep(30)
                    burst = 0
                else:
                    time.sleep(delay)

                self.save_seen_items()

            except Exception as e:
                print("❌ Sniper Fehler:", e)
                time.sleep(10)

# 🕒 Upload-Zeit Helper
def get_upload_timestamp(item):
    if item.get("created_at_ts"):
        return int(item["created_at_ts"])

    if item.get("created_at"):
        dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        return int(dt.timestamp())

    return None

def get_clean_status(item):
    raw_status = item.get('status_id') or item.get('status') or "Unbekannt"
    return status_mapping.get(str(raw_status).lower(), str(raw_status))
