"""
Entry point scraper. Ambil homepage, simpan ke docs/data/home.json.
TTL cache: 1 jam.
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from anichin import AnichinClient
from parser import parse_home


# Path absolut ke folder docs/data (relatif dari file ini)
# scraper/main.py -> ../docs/data
DATA_DIR = (Path(__file__).parent.parent / "docs" / "data").resolve()

TTL_HOME = timedelta(hours=1)


def now_utc():
    return datetime.now(timezone.utc)


def is_fresh(path, ttl):
    """Cek apakah file masih fresh (belum lewat TTL)."""
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        scraped = datetime.fromisoformat(data["scraped_at"])
        age = now_utc() - scraped
        return age < ttl
    except Exception as e:
        print(f"[!] Cache baca gagal: {e}")
        return False


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    home_path = DATA_DIR / "home.json"

    if is_fresh(home_path, TTL_HOME):
        print(f"[=] home.json masih fresh (< {TTL_HOME}). Skip.")
        return

    print("[*] Scrape homepage...")
    client = AnichinClient()
    try:
        html = client.get("/")
    finally:
        client.close()

    data = parse_home(html)
    save_json(home_path, data)
    print(f"[✓] Tersimpan: {home_path}")
    print(f"    slider={len(data['slider'])}, latest={len(data['latest'])}")


if __name__ == "__main__":
    main()