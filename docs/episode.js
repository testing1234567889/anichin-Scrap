const ANICHIN_BASE = "https://anichin.moe";

function absoluteThumb(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return ANICHIN_BASE + path;
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getSlug() {
  const p = new URLSearchParams(location.search);
  return p.get("slug");
}

function renderServerOptions(servers, activeIdx) {
  return servers.map((s, i) => {
    const adTag = s.has_ads ? " [ADS]" : "";
    const cls = i === activeIdx ? "server-btn active" : "server-btn";
    return `<button class="${cls}" data-idx="${i}">${escapeHtml(s.label)}${adTag}</button>`;
  }).join("");
}

function renderPlayer(servers, activeIdx) {
  if (!servers.length) {
    return '<div class="empty">Tidak ada server streaming.</div>';
  }
  const current = servers[activeIdx];
  if (!current.iframe) {
    return '<div class="empty">Server ini tidak punya link embed.</div>';
  }
  return `
    <div class="player-wrap">
      <iframe
        src="${current.iframe}"
        allowfullscreen
        allow="autoplay; fullscreen; picture-in-picture; web-share"
        frameborder="0"></iframe>
    </div>
  `;
}

function renderDownloads(downloads) {
  if (!downloads.length) {
    return '<div class="empty">Tidak ada link download.</div>';
  }
  return downloads.map(d => `
    <div class="dl-row">
      <strong>${escapeHtml(d.quality || "-")}</strong>
      <div class="dl-links">
        ${d.links.map(l => `
          <a href="${l.url}" target="_blank" rel="noopener">${escapeHtml(l.label)}</a>
        `).join("")}
      </div>
    </div>
  `).join("");
}

function renderInfo(info) {
  if (!info || !info.genres || !info.genres.length) return "";
  const rows = [
    ["Status", info.status],
    ["Studio", info.studio],
    ["Network", info.network],
    ["Rilis", info.release_date],
    ["Durasi", info.duration],
    ["Season", info.season],
    ["Negara", info.country],
    ["Tipe", info.type],
    ["Total Episode", info.total_episodes],
    ["Rating", info.rating],
  ].filter(([_, v]) => v);

  return `
    <div class="info-box">
      <h3>Info Series</h3>
      <div class="info-rows">
        ${rows.map(([k, v]) => `
          <div class="info-row"><span>${k}</span><b>${escapeHtml(v)}</b></div>
        `).join("")}
      </div>
      <div class="genres">
        ${info.genres.map(g => `<span class="genre-tag">${escapeHtml(g)}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderNav(prev, next) {
  const prevBtn = prev
    ? `<a class="nav-btn" href="episode.html?slug=${encodeURIComponent(slugFromUrl(prev))}">‹ Sebelumnya</a>`
    : `<span class="nav-btn disabled">‹ Sebelumnya</span>`;
  const nextBtn = next
    ? `<a class="nav-btn" href="episode.html?slug=${encodeURIComponent(slugFromUrl(next))}">Selanjutnya ›</a>`
    : `<span class="nav-btn disabled">Selanjutnya ›</span>`;
  return `<div class="nav-bar">${prevBtn}<a class="nav-btn home" href="index.html">Home</a>${nextBtn}</div>`;
}

function slugFromUrl(url) {
  if (!url) return "";
  const m = url.match(/\/([^\/]+)\/?$/);
  return m ? m[1] : "";
}

let currentServers = [];
let currentActive = 0;

function renderAll(data) {
  const main = document.getElementById("episode-main");
  main.innerHTML = `
    <h1 class="ep-title">${escapeHtml(data.title)}</h1>
    <div id="server-list" class="server-list">
      ${renderServerOptions(currentServers, currentActive)}
    </div>
    <div id="player-holder">
      ${renderPlayer(currentServers, currentActive)}
    </div>
    <div class="section">
      <h3 class="section-title">Download</h3>
      ${renderDownloads(data.downloads || [])}
    </div>
    ${renderInfo(data.info || {})}
    ${renderNav(data.prev_url, data.next_url)}
  `;

  document.querySelectorAll(".server-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentActive = parseInt(btn.dataset.idx, 10);
      document.getElementById("server-list").innerHTML = renderServerOptions(currentServers, currentActive);
      document.getElementById("player-holder").innerHTML = renderPlayer(currentServers, currentActive);
      attachServerListeners();
    });
  });
}

function attachServerListeners() {
  document.querySelectorAll(".server-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentActive = parseInt(btn.dataset.idx, 10);
      document.getElementById("server-list").innerHTML = renderServerOptions(currentServers, currentActive);
      document.getElementById("player-holder").innerHTML = renderPlayer(currentServers, currentActive);
      attachServerListeners();
    });
  });
}

async function load() {
  const slug = getSlug();
  const main = document.getElementById("episode-main");

  if (!slug) {
    main.innerHTML = '<div class="empty">Parameter slug tidak ditemukan di URL.</div>';
    return;
  }

  try {
    const res = await fetch(`data/episodes/${slug}.json`, { cache: "no-cache" });
    if (!res.ok) {
      main.innerHTML = `<div class="empty">Episode tidak ditemukan. (HTTP ${res.status})</div>`;
      return;
    }
    const data = await res.json();
    currentServers = data.servers || [];
    currentActive = 0;

    if (currentServers.length && data.primary_iframe) {
      const idx = currentServers.findIndex(s => s.iframe === data.primary_iframe);
      if (idx >= 0) currentActive = idx;
    }

    renderAll(data);
  } catch (err) {
    main.innerHTML = `<div class="empty">Gagal load episode: ${err.message}</div>`;
  }
}

load();