import tls_client
import time
import threading


class VintedSniper(threading.Thread):
    def __init__(self, url, callback):
        super().__init__(daemon=True)

        self.url = self.convert_url(url)
        self.callback = callback
        self.running = True

        self.seen = set()
        self.initialized = False

        self.session = tls_client.Session(
            client_identifier="chrome_112"
        )

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/plain, */*",
        }

    def stop(self):
        self.running = False

    def convert_url(self, url):
        # Wenn bereits API-URL → direkt nutzen
        if "api/v2/catalog/items" in url:
            return url

        base = "https://www.vinted.de/api/v2/catalog/items"

        # Falls keine Parameter vorhanden
        if "?" not in url:
            return f"{base}?order=newest_first&per_page=20"

        params = url.split("?", 1)[1]

        # Sicherheit: doppelte order/per_page vermeiden
        if "order=" not in params:
            params += "&order=newest_first"
        if "per_page=" not in params:
            params += "&per_page=20"

        return f"{base}?{params}"

    def run(self):
        print("🟢 Sniper Loop gestartet")
        print("🔗 API URL:", self.url)

        while self.running:
            try:
                r = self.session.get(self.url, headers=self.headers)
                print("🌐 API Status:", r.status_code)

                if r.status_code != 200:
                    time.sleep(10)
                    continue

                data = r.json()
                items = data.get("items", [])
                print("📥 Items erhalten:", len(items))

                # 🔒 ERSTER DURCHLAUF → nur merken
                if not self.initialized:
                    for item in items:
                        self.seen.add(item["id"])

                    self.initialized = True
                    print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                    time.sleep(10)
                    continue

                # 🚀 NEUE ITEMS
                for item in items:
                    item_id = item["id"]

                    if item_id in self.seen:
                        continue

                    self.seen.add(item_id)
                    print("🔥 Neues Item erkannt:", item.get("title"))
                    self.callback(item)

                # Speicher begrenzen
                if len(self.seen) > 500:
                    self.seen = set(list(self.seen)[-300:])

                time.sleep(10)

            except Exception as e:
                print("❌ Sniper Fehler:", e)
                time.sleep(10)
