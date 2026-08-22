# api/index.py — AtmoSync EN API gateway.
# Local dev:  uvicorn api.index:app --reload --port 8000
# Then open:  http://localhost:8000/  (redirects to /static/index.html)

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import pathlib
import logging

logger = logging.getLogger("atmosync")

app = FastAPI(title="AtmoSync EN API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ROOT_DIR = pathlib.Path(__file__).parent.parent
STATIC_DIR = ROOT_DIR / "static"
MODEL_PATH = ROOT_DIR / "atmosync_model.pkl"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------------------------------------------
# Model loading — startup only, not per-request.
# We use joblib (not pickle) because joblib handles numpy arrays
# inside sklearn/xgboost pipelines more safely than raw pickle.
# scikit-learn is NOT required in requirements.txt for this to work:
#   - If the .pkl was saved with joblib from an XGBoost model, only
#     the `xgboost` and `joblib` packages are needed at inference time.
#   - scikit-learn Pipeline wrappers DO require sklearn at load time —
#     if your model is wrapped in a Pipeline, add scikit-learn back.
# ----------------------------------------------------------------
_model = None

def load_model():
    global _model
    if not MODEL_PATH.exists():
        logger.warning(f"Model not found at {MODEL_PATH} — /api/predict will return rule-based fallback")
        return
    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        logger.info(f"Model loaded from {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Model load failed: {e}")
        _model = None

load_model()

# Label map — must match the integer classes your model was trained on.
# 0 = Nominal, 1 = Cautionary, 2 = Disaster
STATE_LABELS = {0: "nominal", 1: "cautionary", 2: "disaster"}

class PredictRequest(BaseModel):
    pressure: float       # hPa
    temp: float           # °C
    humidity: float       # %
    wind: float           # km/h
    delta_p: float = 0.0  # ΔP over 3h window (hPa); 0 if baseline not yet established

# ----------------------------------------------------------------
# Rule-based fallback — mirrors the JS evaluateSystemState() logic
# exactly, so the backend and frontend agree when the model is absent.
# ----------------------------------------------------------------
def rule_based_state(pressure, temp, humidity, wind, delta_p):
    abs_dp = abs(delta_p)
    if abs_dp >= 3 or wind >= 60:
        return "disaster"
    if abs_dp >= 1.5 or wind >= 35:
        return "cautionary"
    return "nominal"

@app.post("/api/predict")
def predict(req: PredictRequest):
    """
    Accepts current telemetry + ΔP, returns system state prediction.
    Uses the XGBoost model if loaded; falls back to rule-based logic otherwise.
    Feature order must match training: [pressure, temp, humidity, wind, delta_p]
    """
    features = [[req.pressure, req.temp, req.humidity, req.wind, req.delta_p]]

    if _model is not None:
        try:
            import numpy as np
            pred = int(_model.predict(np.array(features))[0])
            state = STATE_LABELS.get(pred, "nominal")
            source = "model"
        except Exception as e:
            logger.error(f"Model inference failed: {e} — using rule-based fallback")
            state = rule_based_state(**req.dict())
            source = "rules-fallback"
    else:
        state = rule_based_state(**req.dict())
        source = "rules-no-model"

    label_map = {
        "nominal":     "NOMINAL",
        "cautionary":  "CAUTIONARY — MONITOR CLOSELY",
        "disaster":    "DISASTER MODE — SEVERE CONDITIONS",
    }
    return {
        "state": state,
        "label": label_map[state],
        "source": source,
        "inputs": req.dict(),
    }


# ----------------------------------------------------------------
# Static routes
# ----------------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/sw.js")
def service_worker():
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
