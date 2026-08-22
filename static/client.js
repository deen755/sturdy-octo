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
  // Compass / device telemetry
  enableSensors: document.getElementById("enableSensors"),
  compassNeedle: document.getElementById("compassNeedle"),
  valHeading: document.getElementById("valHeading"),
  valPitch: document.getElementById("valPitch"),
  valRoll: document.getElementById("valRoll"),
  valSpeed: document.getElementById("valSpeed"),
};

let map, marker;

// ================================================================
// 1. Service worker registration (the "bridge" step)
// ================================================================
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

// ================================================================
// 2. Theme toggle (dark tactical / light daylight)
// ================================================================
// syncThemeColor reads the active --bg-0 CSS variable from the root
// element after the data-theme attribute is set, then writes that
// exact color into the <meta name="theme-color"> tag. This syncs the
// Android/iOS status bar to match the app background on every toggle
// without hardcoding any color values here — the CSS variables are
// the single source of truth.
function syncThemeColor() {
  const meta = document.getElementById("theme-meta");
  if (!meta) return;
  // getPropertyValue reads the resolved CSS variable value after the
  // data-theme attribute has already been applied to :root.
  const bg = getComputedStyle(document.documentElement)
    .getPropertyValue("--bg-0")
    .trim();
  if (bg) meta.setAttribute("content", bg);
}

function initTheme() {
  const saved = localStorage.getItem("atmosync-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  els.themeToggle.textContent = saved === "dark" ? "🌙 Dark" : "☀️ Light";
  syncThemeColor();
}

els.themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("atmosync-theme", next);
  els.themeToggle.textContent = next === "dark" ? "🌙 Dark" : "☀️ Light";
  syncThemeColor();
});
initTheme();

// ================================================================
// 3. Geolocation (one-off, used for the telemetry API call + map)
// ================================================================
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

// ================================================================
// 4. ΔP calculation
// ================================================================
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

  if (!best || bestDiff > REFERENCE_TOLERANCE_MS) return null;
  return latest.pressure - best.pressure;
}

// ================================================================
// 5. System States — Nominal / Cautionary / Disaster Mode
// ================================================================
// Single source of truth for what "state" the whole app is in. Drives
// the banner text/color AND the global UI theme (data-state attribute +
// disaster-mode body class), not just a badge — Disaster Mode strips the
// UI down to the essentials per the spec ("simplified high-contrast UI").
//
// Thresholds combine ΔP (rapid pressure drop) and wind speed, since either
// alone can signal a severe event. Extend this function first if you need
// more inputs (e.g. humidity spikes, a real storm-cell API) later.
function evaluateSystemState({ deltaP, wind }) {
  const absDeltaP = deltaP === null ? 0 : Math.abs(deltaP);
  const windVal = wind ?? 0;

  if (absDeltaP >= 3 || windVal >= 60) {
    return {
      state: "disaster",
      label: "DISASTER MODE — SEVERE CONDITIONS",
      sub: "Rapid pressure drop or extreme wind detected. Simplified emergency view active.",
    };
  }
  if (absDeltaP >= 1.5 || windVal >= 35) {
    return {
      state: "cautionary",
      label: "CAUTIONARY — MONITOR CLOSELY",
      sub: "Conditions trending toward severe. Stay alert and recheck often.",
    };
  }
  if (deltaP === null) {
    return {
      state: "nominal",
      label: "GATHERING BASELINE",
      sub: "Need ~3 hours of readings before ΔP trend is reliable.",
    };
  }
  return {
    state: "nominal",
    label: "NOMINAL",
    sub: "Barometric trend stable — no rapid pressure drop detected.",
  };
}

function applySystemState(stateInfo, deltaP) {
  // data-state on <html> for any CSS that wants to key off it.
  document.documentElement.setAttribute("data-state", stateInfo.state);

  // Remove all mode classes, then apply the current one.
  // This drives both the top indicator bar (body::after) and the
  // left-bordered status badge — no background floods anywhere.
  document.body.classList.remove("mode-nominal", "mode-cautionary", "mode-disaster");
  document.body.classList.add(`mode-${stateInfo.state}`);

  // Banner class only controls glass base now; color comes from CSS mode rules.
  els.threatBanner.className = "glass";
  els.threatTitle.textContent = `SYSTEM STATE: ${stateInfo.label}`;
  els.threatSub.textContent = stateInfo.sub;
  els.deltaPValue.textContent =
    deltaP === null ? "ΔP —" : `ΔP ${deltaP > 0 ? "+" : ""}${deltaP.toFixed(2)} hPa`;
}

// ================================================================
// 6. Connection status pill
// ================================================================
function setStatus(online) {
  els.connText.textContent = online ? "ONLINE" : "OFFLINE — CACHED DATA";
  els.connDot.style.color = online ? "var(--safe)" : "var(--danger)";
  els.connDot.style.background = online ? "var(--safe)" : "var(--danger)";
}

// ================================================================
// 7. Real-life telemetry fetch — network-first, IndexedDB fallback,
//    synthetic simulation as a last resort (Fail-Safe Telemetry Pipeline)
// ================================================================
// Three-tier data source, in priority order:
//   1. Live network fetch (/api/telemetry) — real Open-Meteo data
//   2. Cached IndexedDB reading — last known real reading, works offline
//   3. Simulated synthetic cycle — ONLY when there is no network AND no
//      cached history at all (e.g. brand-new device, first launch, no
//      connectivity yet). Keeps the dashboard from showing a blank screen
//      on a cold start, exactly like the original Streamlit fallback engine.
function simulateReading() {
  const now = Date.now();
  return {
    pressure: Number((1013 + 4 * Math.sin(now / (1000 * 60 * 60 * 6))).toFixed(2)),
    temp: Number((28 + 3 * Math.sin(now / (1000 * 60 * 60 * 12))).toFixed(1)),
    humidity: Number((60 + 10 * Math.sin(now / (1000 * 60 * 60 * 8))).toFixed(0)),
    wind: Number((12 + 8 * Math.abs(Math.sin(now / (1000 * 60 * 60 * 4)))).toFixed(1)),
    simulated: true,
  };
}

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
    const existing = await AtmoDB.getAllReadings();
    if (existing.length === 0) {
      // No network AND no history at all yet — seed with a simulated
      // reading so the UI never renders a blank/empty dashboard.
      const sim = simulateReading();
      await AtmoDB.saveReading({ ...sim, lat, lon, synced: false });
    }
  }

  const history = await AtmoDB.getAllReadings();
  const display = latest || history[0];

  if (display) {
    els.valPressure.textContent = display.pressure != null ? `${display.pressure} hPa` : "—";
    els.valTemp.textContent = display.temp != null ? `${display.temp}°C` : "—";
    els.valHumidity.textContent = display.humidity != null ? `${display.humidity}%` : "—";
    els.valWind.textContent = display.wind != null ? `${display.wind} km/h` : "—";
  }

  const deltaP = computeDeltaP(history);

  // Try backend model prediction first; fall back to local JS rule-based
  // evaluation if the endpoint is unreachable (offline or model not loaded).
  let stateInfo;
  if (display && navigator.onLine) {
    try {
      const predRes = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pressure: display.pressure ?? 1013,
          temp: display.temp ?? 25,
          humidity: display.humidity ?? 60,
          wind: display.wind ?? 0,
          delta_p: deltaP ?? 0,
        }),
      });
      if (predRes.ok) {
        const pred = await predRes.json();
        // Backend returns { state, label, source } — map to the same
        // shape applySystemState() expects so we don't duplicate display logic.
        stateInfo = {
          state: pred.state,
          label: pred.label,
          sub: pred.source === "model"
            ? "XGBoost model prediction based on live telemetry."
            : evaluateSystemState({ deltaP, wind: display.wind }).sub,
        };
      } else {
        throw new Error("predict endpoint error");
      }
    } catch {
      stateInfo = evaluateSystemState({ deltaP, wind: display?.wind ?? null });
    }
  } else {
    stateInfo = evaluateSystemState({ deltaP, wind: display?.wind ?? null });
  }

  applySystemState(stateInfo, deltaP);
  renderLog(history);
}

// ================================================================
// PWA install button (optional — works alongside the auto-prompt)
// ================================================================
// The beforeinstallprompt event is captured in index.html before body
// loads (window.__pwaInstallPrompt). Here we just expose a function
// client code can call to trigger it on demand (e.g. an install button).
window.addEventListener("pwa-install-ready", () => {
  console.log("[PWA] install prompt ready — can trigger on user gesture");
});

window.triggerInstall = async function () {
  if (!window.__pwaInstallPrompt) {
    console.warn("[PWA] no install prompt available — already installed or not eligible");
    return;
  }
  window.__pwaInstallPrompt.prompt();
  const { outcome } = await window.__pwaInstallPrompt.userChoice;
  console.log(`[PWA] install outcome: ${outcome}`);
  window.__pwaInstallPrompt = null;
};

function renderLog(history) {
  els.logRows.innerHTML = history
    .slice(0, 25)
    .map((r) => {
      const statusLabel = r.simulated ? "SIMULATED" : r.synced ? "SYNCED" : "QUEUED";
      const rowClass = r.simulated ? "simulated" : r.synced ? "" : "queued";
      return `
      <div class="log-row ${rowClass}">
        <span>${new Date(r.timestamp).toLocaleString()}</span>
        <span>${r.pressure ?? "—"} hPa</span>
        <span>${r.temp ?? "—"}°C</span>
        <span>${r.humidity ?? "—"}%</span>
        <span>${statusLabel}</span>
      </div>`;
    })
    .join("");
}

window.addEventListener("online", fetchTelemetry);
window.addEventListener("offline", () => setStatus(false));

fetchTelemetry();
setInterval(fetchTelemetry, 5 * 60 * 1000); // poll every 5 min

// ================================================================
// 8. Compass & device orientation telemetry
// ================================================================
// iOS 13+ requires an explicit user-gesture permission prompt for both
// DeviceOrientationEvent and DeviceMotionEvent (privacy requirement —
// these APIs can otherwise fingerprint/track a device). Android (and
// desktop Chrome) expose them with no permission step at all. We detect
// which situation we're in and only show a gate when actually needed.
function iosPermissionNeeded() {
  return (
    typeof DeviceOrientationEvent !== "undefined" &&
    typeof DeviceOrientationEvent.requestPermission === "function"
  );
}

function headingLabel(deg) {
  const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return dirs[Math.round(deg / 45) % 8];
}

function updateCompassUI(heading, beta, gamma) {
  const normalized = ((heading % 360) + 360) % 360;
  if (els.compassNeedle) els.compassNeedle.style.transform = `rotate(${normalized}deg)`;
  if (els.valHeading) els.valHeading.textContent = `${Math.round(normalized)}° ${headingLabel(normalized)}`;
  if (els.valPitch) els.valPitch.textContent = beta != null ? `${Math.round(beta)}°` : "—";
  if (els.valRoll) els.valRoll.textContent = gamma != null ? `${Math.round(gamma)}°` : "—";
}

function handleOrientation(event) {
  let heading;
  if (event.webkitCompassHeading !== undefined) {
    // iOS: webkitCompassHeading is already a true compass bearing (0 = N,
    // clockwise), no conversion needed.
    heading = event.webkitCompassHeading;
  } else if (event.alpha !== null) {
    // Android/most others: alpha is the device's rotation around the Z
    // axis, counter-clockwise from its initial orientation — 360 - alpha
    // approximates true heading for a flat, front-facing device. Not as
    // accurate as a magnetometer-fused API, but standard for this event.
    heading = 360 - event.alpha;
  } else {
    return; // no usable data on this device/browser
  }
  updateCompassUI(heading, event.beta, event.gamma);
}

function startCompass() {
  const eventName = "ondeviceorientationabsolute" in window
    ? "deviceorientationabsolute"
    : "deviceorientation";
  window.addEventListener(eventName, handleOrientation);
}

function startSpeedWatch() {
  if (!("geolocation" in navigator)) return;
  navigator.geolocation.watchPosition(
    (pos) => {
      // coords.speed is meters/second and can be null if the device can't
      // determine it (e.g. stationary, no GPS fix yet).
      const speedMs = pos.coords.speed;
      if (els.valSpeed) {
        els.valSpeed.textContent = speedMs != null ? `${(speedMs * 3.6).toFixed(1)} km/h` : "—";
      }
    },
    (err) => console.warn("watchPosition error:", err),
    { enableHighAccuracy: true }
  );
}

async function requestSensorPermissions() {
  els.enableSensors.disabled = true;
  els.enableSensors.textContent = "Requesting…";
  try {
    if (iosPermissionNeeded()) {
      const result = await DeviceOrientationEvent.requestPermission();
      if (result !== "granted") throw new Error("orientation permission denied");
    }
    // Motion permission (iOS) is separate from orientation; request it too
    // if present, but don't block compass/heading on it — it's only used
    // for future accelerometer-based features, not heading itself.
    if (typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function") {
      await DeviceMotionEvent.requestPermission().catch(() => {});
    }
    startCompass();
    startSpeedWatch();
    els.enableSensors.textContent = "Sensors Active";
  } catch (err) {
    console.error("Sensor permission denied:", err);
    els.enableSensors.disabled = false;
    els.enableSensors.textContent = "Permission Denied — Tap to Retry";
  }
}

els.enableSensors?.addEventListener("click", requestSensorPermissions);

// Android / desktop: no permission gate needed, start immediately.
// iOS: leave the button active, waiting for the required user tap.
if (!iosPermissionNeeded() && typeof DeviceOrientationEvent !== "undefined") {
  startCompass();
  startSpeedWatch();
  if (els.enableSensors) {
    els.enableSensors.textContent = "Sensors Active";
    els.enableSensors.disabled = true;
  }
} else if (typeof DeviceOrientationEvent === "undefined" && els.enableSensors) {
  els.enableSensors.textContent = "Not Supported";
  els.enableSensors.disabled = true;
}
