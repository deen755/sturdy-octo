# api/index.py — AtmoSync EN API gateway.
# This matches the path your existing vercel.json already routes every
# request to — no vercel.json changes needed, just add this file (in an
# api/ folder) and the static/ folder as siblings of your existing app.py.
#
# Local dev:  uvicorn api.index:app --reload --port 8000
# Then open:  http://localhost:8000/  (redirects to /static/index.html)
#
# Your Streamlit app.py stays exactly as-is (dashboard/judge-facing view).
# This file is the lightweight API + static host for the responder PWA.

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import pathlib

app = FastAPI(title="AtmoSync EN API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your real domain before final submission
    allow_methods=["GET"],
    allow_headers=["*"],
)

# api/index.py -> parent = api/, parent.parent = repo root
ROOT_DIR = pathlib.Path(__file__).parent.parent
STATIC_DIR = ROOT_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    """
    Redirect (not serve-in-place) to /static/index.html. index.html uses
    relative asset paths (href="style.css", src="client.js", etc.), which
    resolve against the browser's *current URL* — so the page must actually
    be at /static/... for those relative links to hit the right files.
    Returning the file's contents directly at "/" would leave the browser
    thinking it's at "/", and every relative asset request would 404.
    """
    return RedirectResponse(url="/static/index.html")


@app.get("/sw.js")
def service_worker():
    """
    Served at root (not under /static/) so the browser's default service
    worker scope is "/" — full-origin control, not just /static/. This is
    also why sw.js is a repo-root file, not part of the /static mount.
    no-cache is set so a redeployed sw.js is picked up on next visit
    instead of the browser holding onto a stale cached worker.
    """
    return FileResponse(
        ROOT_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC_DIR / "icons" / "icon-192.png")


@app.get("/api/telemetry")
def get_telemetry(lat: float, lon: float, response: Response):
    response.headers["Cache-Control"] = "no-store"
    """
    Latest single reading, used by the PWA for real-time ΔP threat detection.
    Same Open-Meteo source your Streamlit fetch_pressure_data() uses; the
    168-hour trend history stays in the dashboard for post-event analysis.
    Falls back with a 503 (not fake data) so client.js knows to pull the
    last known reading from IndexedDB instead of silently showing junk.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=surface_pressure,temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    try:
        res = requests.get(url, timeout=4)
        res.raise_for_status()
        hourly = res.json()["hourly"]
        return {
            "pressure": hourly["surface_pressure"][-1],
            "temp": hourly["temperature_2m"][-1],
            "humidity": hourly["relative_humidity_2m"][-1],
            "wind": hourly["wind_speed_10m"][-1],
            "time": hourly["time"][-1],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"upstream unavailable: {e}")
