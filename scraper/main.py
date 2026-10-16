import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from anichin import AnichinClient
from parser import parse_home, parse_episode


DATA_DIR = (Path(__file__).parent.parent / "docs" / "data").resolve()

TTL_HOME = timedelta(hours=1)
TTL_EPISODE = timedelta(days=30)


def now_utc():
    return datetime.now(timezone.utc)


def is_fresh(path, ttl):
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
    episodes_dir = DATA_DIR / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    home_path = DATA_DIR / "home.json"

    if is_fresh(home_path, TTL_HOME):
        print("[=] home.json fresh, skip.")
        home_data = json.loads(home_path.read_text(encoding="utf-8"))
    else:
        print("[*] Scrape homepage...")
        client = AnichinClient()
        try:
            html = client.get("/")
        finally:
            client.close()
        home_data = parse_home(html)
        save_json(home_path, home_data)
        print(f"[✓] home.json tersimpan: slider={len(home_data['slider'])}, latest={len(home_data['latest'])}")

    client = AnichinClient()
    try:
        for item in home_data.get("latest", []):
            ep_slug = item.get("slug")
            if not ep_slug:
                continue

            ep_path = episodes_dir / f"{ep_slug}.json"

            if is_fresh(ep_path, TTL_EPISODE):
                print(f"[=] {ep_slug} fresh, skip.")
                continue

            print(f"[*] Scrape episode: {ep_slug}")
            try:
                html = client.get(f"/{ep_slug}/")
                ep_data = parse_episode(html, ep_slug)
                save_json(ep_path, ep_data)
                print(f"[✓] {ep_slug}: servers={len(ep_data['servers'])}, downloads={len(ep_data['downloads'])}")
            except Exception as e:
                print(f"[!] Gagal {ep_slug}: {e}")
    finally:
        client.close()

    print("[✓] Selesai.")


if __name__ == "__main__":
    main()