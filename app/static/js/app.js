// iOS standalone: keep same-origin links in-app.
if (window.navigator.standalone === true) {
  document.addEventListener("click", (e) => {
    const a = e.target.closest && e.target.closest("a[href]");
    if (!a || a.hasAttribute("target")) return;
    const url = new URL(a.getAttribute("href"), location.href);
    if (url.origin === location.origin) { e.preventDefault(); location.href = url.href; }
  });
}

// Clipboard copy (plain-HTTP LAN fallback via execCommand).
function copyText(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;
  const text = el.value || el.textContent;
  const flash = (msg) => { if (!btn) return; const old = btn.textContent; btn.textContent = msg; setTimeout(() => { btn.textContent = old; }, 1500); };
  const fallback = () => { el.focus(); el.select(); el.setSelectionRange(0, text.length); const ok = document.execCommand("copy"); flash(ok ? "Copié ✓" : "Copie impossible"); };
  if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(() => flash("Copié ✓"), fallback); }
  else { fallback(); }
}

// Quick-add FAB bottom sheet (Alpine).
document.addEventListener("alpine:init", () => {
  Alpine.data("quickAdd", () => ({ open: false, toggle() { this.open = !this.open; } }));
});

// Render a Chart.js line chart into a <canvas id=...> from JSON in data-points.
function lineChart(canvasId) {
  const el = document.getElementById(canvasId);
  if (!el || typeof Chart === "undefined") return;
  const pts = JSON.parse(el.dataset.points || "[]");
  new Chart(el, {
    type: "line",
    data: { labels: pts.map(p => p.x), datasets: [{ data: pts.map(p => p.y), borderColor: "#6d5efc", tension: 0.35, pointRadius: 0, borderWidth: 2 }] },
    options: { plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: true } } },
  });
}
