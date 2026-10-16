import os
import time
import random
from curl_cffi import requests


BASE_URL = "https://anichin.moe"


def parse_proxy_line(line):
    line = line.strip()
    if not line:
        return None
    parts = line.split(":")
    if len(parts) != 4:
        return None
    ip, port, user, pwd = parts
    return f"http://{user}:{pwd}@{ip}:{port}"


def load_proxies():
    raw = os.environ.get("PROXY_LIST", "").strip()
    if not raw:
        return []
    proxies = []
    for chunk in raw.split(","):
        p = parse_proxy_line(chunk)
        if p:
            proxies.append(p)
    return proxies


class AnichinClient:
    def __init__(self, impersonate="chrome120", delay=1.0):
        self.session = requests.Session(impersonate=impersonate)
        self.delay = delay
        self.proxies_list = load_proxies()
        self.proxy_index = 0
        self.dead_proxies = set()

        if self.proxies_list:
            print(f"[*] {len(self.proxies_list)} proxy ter-load.")
        else:
            print("[*] Tanpa proxy (langsung).")

    def next_proxy(self):
        if not self.proxies_list:
            return None
        alive = [p for p in self.proxies_list if p not in self.dead_proxies]
        if not alive:
            self.dead_proxies.clear()
            alive = list(self.proxies_list)
        chosen = alive[self.proxy_index % len(alive)]
        self.proxy_index += 1
        return chosen

    def get(self, path, retries=3):
        if not path.startswith("http"):
            url = f"{BASE_URL}{path}"
        else:
            url = path

        last_err = None

        for attempt in range(1, retries + 1):
            proxy = self.next_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else None

            try:
                r = self.session.get(url, timeout=30, proxies=proxies)

                if r.status_code == 200:
                    if self.delay:
                        time.sleep(self.delay)
                    return r.text

                if r.status_code in (403, 429, 503):
                    tag = proxy.split("@")[-1] if proxy else "direct"
                    wait = 5 * attempt
                    print(f"[!] Blocked {r.status_code} via {tag}. Retry dalam {wait}s...")
                    if proxy:
                        self.dead_proxies.add(proxy)
                    time.sleep(wait)
                    continue

                r.raise_for_status()

            except Exception as e:
                last_err = e
                tag = proxy.split("@")[-1] if proxy else "direct"
                print(f"[!] Error attempt {attempt}/{retries} via {tag}: {e}")
                if proxy:
                    self.dead_proxies.add(proxy)
                time.sleep(2)

        raise RuntimeError(f"Gagal ambil {url} setelah {retries} percobaan: {last_err}")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    client = AnichinClient()
    html = client.get("/")
    print(f"OK. Panjang HTML: {len(html)} karakter")
    print(f"Ada judul? {'<title>' in html}")
    client.close()