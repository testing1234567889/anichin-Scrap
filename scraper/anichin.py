"""
Anichin HTTP client — bypass Cloudflare pakai curl_cffi.
"""
import time
from curl_cffi import requests


BASE_URL = "https://anichin.moe"


class AnichinClient:
    def __init__(self, impersonate="chrome120", delay=1.0):
        self.session = requests.Session(impersonate=impersonate)
        self.delay = delay  # jeda antar request, sopan sama server

    def get(self, path, retries=3):
        """Ambil HTML dari path. Retry kalau kena 403/503."""
        if not path.startswith("http"):
            url = f"{BASE_URL}{path}"
        else:
            url = path

        for attempt in range(1, retries + 1):
            try:
                r = self.session.get(url, timeout=30)

                if r.status_code == 200:
                    return r.text

                if r.status_code in (403, 429, 503):
                    wait = 5 * attempt
                    print(f"[!] Blocked {r.status_code} di {url}. Retry dalam {wait}s...")
                    time.sleep(wait)
                    continue

                r.raise_for_status()

            except Exception as e:
                print(f"[!] Error attempt {attempt}/{retries}: {e}")
                time.sleep(3)

        raise RuntimeError(f"Gagal ambil {url} setelah {retries} percobaan")

    def close(self):
        self.session.close()


# Test langsung kalau file dijalankan
if __name__ == "__main__":
    client = AnichinClient()
    html = client.get("/")
    print(f"OK. Panjang HTML: {len(html)} karakter")
    print(f"Ada judul? {'<title>' in html}")
    client.close()