"""
Parser HTML Anichin → dict Python (siap di-dump ke JSON).
"""
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def extract_slug(url):
    """Ambil slug dari URL. Contoh:
    https://anichin.moe/soul-land-2-episode-175-sub/ -> soul-land-2-episode-175-sub
    """
    if not url:
        return None
    m = re.search(r"anichin\.moe/([^/]+)/?$", url)
    if m:
        return m.group(1)
    m = re.search(r"^/([^/]+)/?$", url)
    return m.group(1) if m else None


def parse_article(art):
    """Parse satu <article class="bs"> jadi dict."""
    a = art.select_one("a[itemprop='url']")
    if not a:
        return None

    img = art.select_one("img")
    tt = art.select_one(".tt")
    epx = art.select_one(".epx")
    typez = art.select_one(".typez")
    status = art.select_one(".status")

    # Judul series diambil dari h2 itemprop atau teks .tt
    h2 = art.select_one("h2[itemprop='headline']")
    title = h2.get_text(strip=True) if h2 else (
        tt.get_text(strip=True) if tt else None
    )

    url = a.get("href")

    return {
        "title": title,
        "url": url,
        "slug": extract_slug(url),
        "thumbnail": img.get("src") if img else None,
        "episode": epx.get_text(strip=True) if epx else None,
        "type": typez.get_text(strip=True) if typez else None,
        "status": status.get_text(strip=True) if status else None,
    }


def parse_slider(soup):
    """Parse slider (banner besar di atas)."""
    items = []
    for slide in soup.select("#slidertwo .swiper-slide.item"):
        a = slide.select_one("h2 a")
        if not a:
            continue
        backdrop = slide.select_one(".backdrop")
        bg = backdrop.get("style", "") if backdrop else ""
        # ambil url('...') dari style
        m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", bg)
        thumb = m.group(1) if m else None

        items.append({
            "title": a.get_text(strip=True),
            "url": a.get("href"),
            "slug": extract_slug(a.get("href")),
            "thumbnail": thumb,
        })
    return items


def parse_home(html):
    """Parser utama halaman homepage."""
    soup = BeautifulSoup(html, "lxml")

    # Slider
    slider = parse_slider(soup)

    # Semua article di section "Rilisan Terbaru"
    # Section ini biasanya di bawah <div class="releases latesthome">
    latest = []
    seen = set()
    latest_box = soup.select_one(".releases.latesthome")
    if latest_box:
        parent = latest_box.find_parent("div", class_="bixbox")
        if parent:
            for art in parent.select("article.bs"):
                data = parse_article(art)
                if data and data["url"] not in seen:
                    seen.add(data["url"])
                    latest.append(data)

    # Fallback: kalau cara di atas gagal, ambil semua article
    if not latest:
        for art in soup.select("article.bs"):
            data = parse_article(art)
            if data and data["url"] not in seen:
                seen.add(data["url"])
                latest.append(data)

    return {
        "slider": slider,
        "latest": latest,
        "scraped_at": now_iso(),
    }


if __name__ == "__main__":
    # Tes: baca file test.html yang barusan dibuat? Atau fetch langsung
    import sys
    import json

    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            html = f.read()
    else:
        from anichin import AnichinClient
        client = AnichinClient()
        html = client.get("/")
        client.close()

    result = parse_home(html)
    print(f"Slider items: {len(result['slider'])}")
    print(f"Latest items: {len(result['latest'])}")
    print()
    print("Contoh 3 rilisan terbaru:")
    for item in result["latest"][:3]:
        print(f"  - {item['title']}")
        print(f"    slug: {item['slug']}")
        print(f"    ep: {item['episode']}")