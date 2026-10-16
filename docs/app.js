const ANICHIN_BASE = "https://anichin.moe";

function absoluteThumb(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return ANICHIN_BASE + path;
}

function localEpisodeUrl(slug) {
  return "episode.html?slug=" + encodeURIComponent(slug);
}

function renderSlider(items) {
  const el = document.getElementById("slider");
  if (!items.length) {
    el.innerHTML = '<div class="empty">Tidak ada data slider.</div>';
    return;
  }
  el.innerHTML = items.map(item => `
    <div class="slide" style="background-image:url('${absoluteThumb(item.thumbnail)}')" onclick="location.href='${localEpisodeUrl(item.slug)}'">
      <div class="slide-title">${item.title}</div>
    </div>
  `).join("");
}

function renderLatest(items) {
  const el = document.getElementById("latest");
  if (!items.length) {
    el.innerHTML = '<div class="empty">Tidak ada data rilisan.</div>';
    return;
  }
  el.innerHTML = items.map(item => `
    <a class="card" href="${localEpisodeUrl(item.slug)}">
      <img class="card-img" src="${absoluteThumb(item.thumbnail)}" alt="${item.title}" loading="lazy">
      <div class="card-body">
        <div class="card-title">${item.title}</div>
        <div class="card-meta">
          <span class="ep-badge">${item.episode || "-"}</span>
          <span>${item.type || ""}</span>
        </div>
      </div>
    </a>
  `).join("");
}

function renderScrapedAt(iso) {
  const el = document.getElementById("scraped-at");
  if (!iso) { el.textContent = ""; return; }
  const d = new Date(iso);
  el.textContent = `Data terakhir diupdate: ${d.toLocaleString("id-ID")}`;
}

function filterLatest(items, query) {
  if (!query) return items;
  const q = query.toLowerCase();
  return items.filter(i => (i.title || "").toLowerCase().includes(q));
}

let allLatest = [];

async function load() {
  try {
    const res = await fetch("data/home.json", { cache: "no-cache" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    renderSlider(data.slider || []);
    allLatest = data.latest || [];
    renderLatest(allLatest);
    renderScrapedAt(data.scraped_at);
  } catch (err) {
    document.getElementById("latest").innerHTML =
      `<div class="empty">Gagal load data: ${err.message}</div>`;
  }
}

document.getElementById("search").addEventListener("input", e => {
  renderLatest(filterLatest(allLatest, e.target.value));
});

load();