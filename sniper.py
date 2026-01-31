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
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.vinted.de/",
            "Origin": "https://www.vinted.de",
        }

        # 🔑 WICHTIG: Cookie holen
        self._bootstrap_session()

    def _bootstrap_session(self):
        try:
            print("🍪 Hole Vinted Cookies …")
            self.session.get(
                "https://www.vinted.de",
                headers=self.headers
            )
            print("🍪 Cookies gesetzt")
        except Exception as e:
            print("⚠️ Cookie-Fehler:", e)

    def stop(self):
        self.running = False

    def convert_url(self, url):
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

        while self.running:
            try:
                r = self.session.get(self.url, headers=self.headers)
                print("🌐 API Status:", r.status_code)

                if r.status_code == 401:
                    print("🔁 Session ungültig – hole Cookies neu")
                    self._bootstrap_session()
                    time.sleep(5)
                    continue

                if r.status_code != 200:
                    time.sleep(10)
                    continue

                items = r.json().get("items", [])
                print("📥 Items erhalten:", len(items))

                # 🔒 Initiale Items nur merken
                if not self.initialized:
                    for item in items:
                        self.seen.add(item["id"])
                    self.initialized = True
                    print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                    time.sleep(10)
                    continue

                # 🚀 Neue Items
                for item in items:
                    item_id = item["id"]
                    if item_id in self.seen:
                        continue

                    self.seen.add(item_id)
                    print("🔥 Neues Item erkannt:", item.get("title"))
                    self.callback(item)

                if len(self.seen) > 500:
                    self.seen = set(list(self.seen)[-300:])

                time.sleep(10)

            except Exception as e:
                print("❌ Sniper Fehler:", e)
                time.sleep(10)
