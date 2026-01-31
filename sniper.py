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

        self.session = tls_client.Session(
            client_identifier="chrome_112"
        )

        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

    def stop(self):
        self.running = False

    def convert_url(self, url):
        if "api/v2/catalog/items" in url:
            return url
        base = "https://www.vinted.de/api/v2/catalog/items?"
        params = url.split("?")[-1]
        return base + params + "&order=newest_first&per_page=20"

    def run(self):
        print("🟢 Sniper Loop gestartet")

        while self.running:
            try:
                r = self.session.get(self.url, headers=self.headers)
                if r.status_code != 200:
                    time.sleep(10)
                    continue

                items = r.json().get("items", [])

                for item in items:
                    item_id = item["id"]
                    if item_id in self.seen:
                        continue

                    self.seen.add(item_id)

                    # Erstes Item nur merken (kein Spam beim Start)
                    if len(self.seen) == 1:
                        continue

                    print("🔥 Neues Item:", item.get("title"))
                    self.callback(item)

                if len(self.seen) > 300:
                    self.seen = set(list(self.seen)[-150:])

                time.sleep(10)

            except Exception as e:
                print("❌ Sniper Fehler:", e)
                time.sleep(10)
