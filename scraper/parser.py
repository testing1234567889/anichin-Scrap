import re
import base64
from datetime import datetime, timezone
from bs4 import BeautifulSoup


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def extract_slug(url):
    if not url:
        return None
    m = re.search(r"anichin\.moe/([^/]+)/?$", url)
    if m:
        return m.group(1)
    m = re.search(r"^/([^/]+)/?$", url)
    return m.group(1) if m else None


def parse_article(art):
    a = art.select_one("a[itemprop='url']")
    if not a:
        return None

    img = art.select_one("img")
    tt = art.select_one(".tt")
    epx = art.select_one(".epx")
    typez = art.select_one(".typez")
    status = art.select_one(".status")
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
    items = []
    for slide in soup.select("#slidertwo .swiper-slide.item"):
        a = slide.select_one("h2 a")
        if not a:
            continue

        backdrop = slide.select_one(".backdrop")
        bg = backdrop.get("style", "") if backdrop else ""
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
    soup = BeautifulSoup(html, "lxml")
    slider = parse_slider(soup)

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


def decode_mirror_value(value):
    if not value:
        return None
    try:
        decoded = base64.b64decode(value).decode("utf-8", errors="ignore")
    except Exception:
        return None
    m = re.search(r'src=["\']([^"\']+)["\']', decoded, re.IGNORECASE)
    return m.group(1) if m else None


def parse_mirror_servers(soup):
    servers = []
    select = soup.select_one("select.mirror")
    if not select:
        return servers

    for opt in select.find_all("option"):
        value = opt.get("value", "").strip()
        label = opt.get_text(strip=True)
        if not value or not label or label.lower().startswith("pilih"):
            continue

        src = decode_mirror_value(value)
        is_ad = "[ADS]" in label
        clean_label = re.sub(r"\s*\[ADS\]", "", label).strip()
        clean_label = re.sub(r"\s*\[Setting DNS\]", "", clean_label).strip()

        servers.append({
            "label": clean_label,
            "iframe": src,
            "has_ads": is_ad,
        })
    return servers


def parse_episode(html, slug):
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("h1.entry-title") or soup.select_one(".entry-title")
    title = title_el.get_text(strip=True) if title_el else slug

    series_url = None
    series_slug = None
    breadcrumb = soup.select(".ts-breadcrumb a[itemprop='item']")
    if len(breadcrumb) >= 2:
        series_url = breadcrumb[1].get("href")
        series_slug = extract_slug(series_url)
    if not series_url:
        el = soup.select_one(".naveps .nvsc a")
        if el:
            series_url = el.get("href")
            series_slug = extract_slug(series_url)

    iframe_el = soup.select_one("#pembed iframe") or soup.select_one(".player-embed iframe")
    primary_iframe = iframe_el.get("src") if iframe_el else None

    servers = parse_mirror_servers(soup)

    downloads = []
    dl_box = soup.select_one(".soraddlx") or soup.select_one(".soradlg")
    if dl_box:
        for row in dl_box.select(".soraurlx"):
            strong = row.find("strong")
            quality = strong.get_text(strip=True) if strong else None

            links = []
            for a in row.select("a"):
                href = a.get("href")
                label = a.get_text(strip=True) or "Link"
                if href:
                    links.append({"label": label, "url": href})

            if links:
                downloads.append({"quality": quality, "links": links})

    info = {}
    info_box = soup.select_one(".single-info")
    if info_box:
        alter = info_box.select_one(".alter")
        rating_el = info_box.select_one(".rating strong")
        genres = [a.get_text(strip=True) for a in info_box.select(".genxed a")]
        desc_el = info_box.select_one(".desc h5") or info_box.select_one(".mindes h5")

        spe = {}
        for span in info_box.select(".spe span"):
            txt = span.get_text(strip=True)
            if ":" in txt:
                key, _, val = txt.partition(":")
                spe[key.strip().lower()] = val.strip()

        info = {
            "alter_title": alter.get_text(strip=True) if alter else None,
            "rating": rating_el.get_text(strip=True).replace("Rating", "").strip() if rating_el else None,
            "genres": genres,
            "description": desc_el.get_text(strip=True) if desc_el else None,
            "status": spe.get("status"),
            "studio": spe.get("studio"),
            "network": spe.get("network"),
            "release_date": spe.get("tanggal rilis"),
            "duration": spe.get("durasi"),
            "season": spe.get("season"),
            "country": spe.get("negara"),
            "type": spe.get("tipe"),
            "total_episodes": spe.get("episode"),
        }

    prev_url = None
    next_url = None
    for nv in soup.select(".naveps .nvs a"):
        txt = nv.get_text(strip=True).lower()
        href = nv.get("href")
        if not href:
            continue
        if "prev" in txt or "sebelum" in txt:
            prev_url = href
        elif "next" in txt or "selanjut" in txt:
            next_url = href

    return {
        "slug": slug,
        "title": title,
        "series_url": series_url,
        "series_slug": series_slug,
        "primary_iframe": primary_iframe,
        "servers": servers,
        "downloads": downloads,
        "info": info,
        "prev_url": prev_url,
        "next_url": next_url,
        "scraped_at": now_iso(),
    }


if __name__ == "__main__":
    import sys
    from anichin import AnichinClient

    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            html = f.read()
    else:
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