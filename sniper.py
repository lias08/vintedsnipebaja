import asyncio

class VintedSniper:
    def __init__(self, url, callback):
        self.url = self._convert_url(url)
        self.callback = callback
        self.running = True

        self.seen = self.load_seen_items()  # Lade die gesehenen Items aus der Datei
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

    async def run(self):  # Wir machen die Methode asynchron
        print("🟢 Sniper Loop gestartet")
        burst = 0
        last_top_id = None
        consecutive_403s = 0

        while self.running:
            try:
                await global_limiter.wait()

                r = self.session.get(self.url, headers=self.headers)
                print("🌐 API Status:", r.status_code)

                if r.status_code == 403:
                    consecutive_403s += 1
                    print(f"⛔ 403 Block – Cooldown {consecutive_403s * 10}s")
                    await asyncio.sleep(consecutive_403s * 10)
                    if consecutive_403s > 3:
                        print("🔴 Viele 403s – längere Pause!")
                        await asyncio.sleep(30)
                    continue

                if r.status_code != 200:
                    await asyncio.sleep(10)
                    continue

                items = r.json().get("items", [])
                print("📥 Items erhalten:", len(items))

                if not items:
                    await asyncio.sleep(10)  # Kürzere Wartezeit bei keinem neuen Artikel
                    continue

                top_id = items[0]["id"]

                if not self.initialized:
                    for item in items:
                        self.seen.add(item["id"])
                    self.initialized = True
                    last_top_id = top_id
                    print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                    await asyncio.sleep(5)
                    continue

                for item in items:
                    if item["id"] in self.seen:
                        continue
                    self.seen.add(item["id"])
                    print("🔥 Neues Item:", item.get("title"))
                    await self.callback(item)

                if top_id != last_top_id:
                    delay = random.randint(6, 7)  # Schnelle Burst-Scans
                    burst += 1
                else:
                    delay = random.randint(12, 15)  # langsamer bei wenig Bewegung
                    burst = 0

                last_top_id = top_id

                if burst >= 5:
                    print("🧊 Burst Cooldown 30s")
                    await asyncio.sleep(30)
                    burst = 0
                else:
                    await asyncio.sleep(delay)

                # Speichere die IDs nach jedem Scan
                self.save_seen_items()

            except Exception as e:
                print("❌ Sniper Fehler:", e)
                await asyncio.sleep(10)  # Kurze Pause bei Fehlern
