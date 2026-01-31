import time
import random

def run(self):
    print("🟢 Sniper Loop gestartet")
    print("🔗 API URL:", self.url)

    burst = 0
    last_top_id = None

    while self.running:
        try:
            r = self.session.get(self.url, headers=self.headers)
            print("🌐 API Status:", r.status_code)

            # ⛔ 403 = Cooldown, NICHT neu starten
            if r.status_code == 403:
                print("⛔ 403 Block – Cooldown 90s")
                time.sleep(90)
                continue

            if r.status_code != 200:
                time.sleep(20)
                continue

            items = r.json().get("items", [])
            print("📥 Items erhalten:", len(items))

            if not items:
                time.sleep(20)
                continue

            top_id = items[0]["id"]

            # 📦 Initiale Items
            if not self.initialized:
                for item in items:
                    self.seen.add(item["id"])
                self.initialized = True
                last_top_id = top_id
                print(f"📦 Initiale Items gespeichert: {len(self.seen)}")
                time.sleep(15)
                continue

            # 🔥 Neue Items
            for item in items:
                if item["id"] in self.seen:
                    continue
                self.seen.add(item["id"])
                print("🔥 Neues Item:", item.get("title"))
                self.callback(item)

            # ⚡ Speed-Logik
            if top_id != last_top_id:
                delay = random.randint(6, 8)   # Markt aktiv
                burst += 1
            else:
                delay = random.randint(15, 22) # ruhig
                burst = 0

            last_top_id = top_id

            # 🧊 Burst-Cooldown
            if burst >= 5:
                print("🧊 Burst Cooldown 60s")
                time.sleep(60)
                burst = 0
            else:
                time.sleep(delay)

        except Exception as e:
            print("❌ Sniper Fehler:", e)
            time.sleep(20)
