// client.js — AtmoSync EN frontend logic.

const els = {
  connDot: document.getElementById("connDot"),
  connText: document.getElementById("connText"),
  connPill: document.getElementById("connPill"),
  themeToggle: document.getElementById("themeToggle"),
  threatBanner: document.getElementById("threatBanner"),
  threatTitle: document.getElementById("threatTitle"),
  threatSub: document.getElementById("threatSub"),
  deltaPValue: document.getElementById("deltaPValue"),
  valPressure: document.getElementById("valPressure"),
  valTemp: document.getElementById("valTemp"),
  valHumidity: document.getElementById("valHumidity"),
  valWind: document.getElementById("valWind"),
  logRows: document.getElementById("logRows"),
};

let map, marker;

// ---------- 1. Service worker registration (the "bridge" step) ----------
// sw.js is served from the root ("/sw.js" via a FastAPI route, not from
// inside /static/) specifically so its default scope is "/" — giving it
// control over the whole origin (including /api/* fallback interception),
// not just the /static/ subtree.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .then((reg) => console.log("SW registered:", reg.scope))
      .catch((err) => console.error("SW registration failed:", err));
  });
}

// ---------- 2. Theme toggle (dark tactical / light daylight) ----------
function initTheme() {
  const saved = localStorage.getItem("atmosync-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  els.themeToggle.textContent = saved === "dark" ? "🌙 Dark" : "☀️ Light";
}
els.themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("atmosync-theme", next);
  els.themeToggle.textContent = next === "dark" ? "🌙 Dark" : "☀️ Light";
});
initTheme();

// ---------- 3. Geolocation ----------
function getPosition() {
  return new Promise((resolve) => {
    if (!("geolocation" in navigator)) return resolve({ lat: 25.2048, lon: 55.2708 });
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => resolve({ lat: 25.2048, lon: 55.2708 }), // fallback: Dubai
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

function initMap(lat, lon) {
  if (map) {
    marker.setLatLng([lat, lon]);
    map.panTo([lat, lon]);
    return;
  }
  map = L.map("map", { zoomControl: false }).setView([lat, lon], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  const glowIcon = L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:#00f0ff;
            box-shadow:0 0 12px #00f0ff,0 0 24px #00f0ff;"></div>`,
  });
  marker = L.marker([lat, lon], { icon: glowIcon }).addTo(map);
}

// ---------- 4. ΔP threat classification ----------
// ΔP thresholds are a simplified MVP heuristic — a 3hPa/3hr drop is a
// widely used rule-of-thumb rapid-intensification signal for storms.
//
// Polling runs every 5 min, so history[0] vs history[1] is a 5-minute
// delta, not 3 hours — comparing adjacent polls pins ΔP near 0 forever.
// Instead we scan the queue for whichever stored reading is closest to
// (now - 3h) and diff against that.
const REFERENCE_WINDOW_MS = 3 * 60 * 60 * 1000; // 3 hours
const REFERENCE_TOLERANCE_MS = 45 * 60 * 1000; // accept a match within ±45 min

function computeDeltaP(history) {
  if (!history.length || history[0].pressure == null) return null;
  const latest = history[0];
  const targetTime = latest.timestamp - REFERENCE_WINDOW_MS;

  let best = null;
  let bestDiff = Infinity;
  for (let i = 1; i < history.length; i++) {
    if (history[i].pressure == null) continue;
    const diff = Math.abs(history[i].timestamp - targetTime);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = history[i];
    }
  }

  // Not enough history yet (app just started, or gap too large) — don't
  // guess; report "gathering baseline" instead of a misleading number.
  if (!best || bestDiff > REFERENCE_TOLERANCE_MS) return null;
  return latest.pressure - best.pressure;
}

function classifyThreat(deltaP) {
  const abs = Math.abs(deltaP);
  if (abs >= 3) return { level: "danger", label: "SEVERE — RAPID PRESSURE DROP", sub: "ΔP exceeds 3 hPa — possible incoming storm system. Alert command center." };
  if (abs >= 1.5) return { level: "warn", label: "ELEVATED — MONITOR CLOSELY", sub: "ΔP trending down — conditions worth tracking over the next readings." };
  return { level: "safe", label: "NOMINAL", sub: "Barometric trend stable — no rapid pressure drop detected." };
}

function renderThreat(deltaP) {
  if (deltaP === null) {
    els.threatBanner.className = "glass level-safe";
    els.threatTitle.textContent = "THREAT LEVEL: GATHERING BASELINE";
    els.threatSub.textContent = "Need ~3 hours of readings before ΔP trend is reliable.";
    els.deltaPValue.textContent = "ΔP —";
    return;
  }
  const t = classifyThreat(deltaP);
  els.threatBanner.className = `glass level-${t.level}`;
  els.threatTitle.textContent = `THREAT LEVEL: ${t.label}`;
  els.threatSub.textContent = t.sub;
  els.deltaPValue.textContent = `ΔP ${deltaP > 0 ? "+" : ""}${deltaP.toFixed(2)} hPa`;
}

// ---------- 5. Connection status pill ----------
function setStatus(online) {
  els.connText.textContent = online ? "ONLINE" : "OFFLINE — CACHED DATA";
  els.connDot.style.color = online ? "var(--safe)" : "var(--danger)";
  els.connDot.style.background = online ? "var(--safe)" : "var(--danger)";
}

// ---------- 6. Fetch telemetry (network-first, IndexedDB fallback) ----------
async function fetchTelemetry() {
  const { lat, lon } = await getPosition();
  initMap(lat, lon);

  let latest = null;
  try {
    const res = await fetch(`/api/telemetry?lat=${lat}&lon=${lon}`, { cache: "no-store" });
    if (!res.ok) throw new Error("bad response");
    latest = await res.json();
    await AtmoDB.saveReading({ ...latest, lat, lon, synced: true });
    setStatus(true);
  } catch (err) {
    setStatus(false);
  }

  const history = await AtmoDB.getAllReadings();
  const display = latest || history[0];

  if (display) {
    els.valPressure.textContent = display.pressure != null ? `${display.pressure} hPa` : "—";
    els.valTemp.textContent = display.temp != null ? `${display.temp}°C` : "—";
    els.valHumidity.textContent = display.humidity != null ? `${display.humidity}%` : "—";
    els.valWind.textContent = display.wind != null ? `${display.wind} km/h` : "—";
  }

  renderThreat(computeDeltaP(history));
  renderLog(history);
}

function renderLog(history) {
  els.logRows.innerHTML = history
    .slice(0, 25)
    .map(
      (r) => `
      <div class="log-row ${r.synced ? "" : "queued"}">
        <span>${new Date(r.timestamp).toLocaleString()}</span>
        <span>${r.pressure ?? "—"} hPa</span>
        <span>${r.temp ?? "—"}°C</span>
        <span>${r.humidity ?? "—"}%</span>
        <span>${r.synced ? "SYNCED" : "QUEUED"}</span>
      </div>`
    )
    .join("");
}

window.addEventListener("online", fetchTelemetry);
window.addEventListener("offline", () => setStatus(false));

fetchTelemetry();
setInterval(fetchTelemetry, 5 * 60 * 1000); // poll every 5 min
