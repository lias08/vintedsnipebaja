import tls_client
import time
import threading
import random
from datetime import datetime

# 🌍 GLOBAL RATE LIMITER (für alle Sniper)
class GlobalLimiter:
    def __init__(self, min_delay=7):
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


global_limiter = GlobalLimiter(min_delay=7)


class VintedSniper(threading.Thread):
    def __init__(self, url, callback):
        super().__init__(daemon=True)

        self.url = self._convert_url(url)
        self.callback = callback
        self.running = True

        self.seen = set()
        self.initialized = False

        self.session = tls_client.Session(
            client_identifier="chrome_112"
        )

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9",
            "Referer": "https://www.vinted.de/",
            "Origin": "https://www.vinted.de",
        }

        self._bootstrap_session()

    # 🍪 Cookies holen (Pflicht)
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
                    time.sleep(20)
                    continue

                top_id = items[0]["id"]

                if not self.initialized:
                    for item in items:
                        self.seen.add(item["id"])
                    self.initialized = True
                    last_top_id = top_id
                    print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                    time.sleep(15)
                    continue

                for item in items:
                    if item["id"] in self.seen:
                        continue
                    self.seen.add(item["id"])
                    print("🔥 Neues Item:", item.get("title"))
                    self.callback(item)

                if top_id != last_top_id:
                    delay = random.randint(6, 7)  # Schnelle Burst-Scans
                    burst += 1
                else:
                    delay = random.randint(15, 20)  # langsamer bei wenig Bewegung
                    bur
