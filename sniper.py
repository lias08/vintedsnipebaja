import tls_client
import time
import threading

class VintedSniper(threading.Thread):
    def __init__(self, api_url, send_func):
        super().__init__()
        self.api_url = api_url
        self.send = send_func
        self.running = True
        self.seen = set()
        self.session = tls_client.Session(client_identifier="chrome_112")

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            try:
                r = self.session.get(self.api_url)
                if r.status_code == 200:
                    for item in r.json().get("items", []):
                        if item["id"] not in self.seen:
                            self.seen.add(item["id"])
                            self.send(item)
                time.sleep(10)
            except:
                time.sleep(10)
