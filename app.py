import streamlit as st
import pandas as pd
import os
import glob
import joblib
import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="AtmoSync Emergency Network", layout="wide", initial_sidebar_state="collapsed")
st.set_page_config(
    page_title="AtmoSync Emergency Network",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load XGBoost AI Model Artifact
MODEL_PATH = "atmosync_model.pkl"


@st.cache_resource
def load_xgboost_model():
  if os.path.exists(MODEL_PATH):
    try:
      return joblib.load(MODEL_PATH)
    except Exception as e:
      st.warning(f"Failed to load model file: {e}")
      return None
  return None


ai_model = load_xgboost_model()

# Session State Initialization
if 'lat' not in st.session_state:
    st.session_state.lat = 25.7617
if 'lon' not in st.session_state:
    st.session_state.lon = -80.1918
if 'city_name' not in st.session_state:
    st.session_state.city_name = "Miami, USA (Default)"
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "🏠 Home"
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if "lat" not in st.session_state:
  st.session_state.lat = 25.7617
if "lon" not in st.session_state:
  st.session_state.lon = -80.1918
if "city_name" not in st.session_state:
  st.session_state.city_name = "Miami, USA (Default)"
if "current_tab" not in st.session_state:
  st.session_state.current_tab = "🏠 Home"
if "dark_mode" not in st.session_state:
  st.session_state.dark_mode = True

# Dynamic Styling
bg_color = "#0B0F19" if st.session_state.dark_mode else "#F4F7FB"
@@ -28,7 +52,8 @@
accent_aqua = "#00F0FF" if st.session_state.dark_mode else "#0284C7"
plot_template = "plotly_dark" if st.session_state.dark_mode else "plotly_white"

st.markdown(f"""
st.markdown(
    f"""
   <style>
       .stApp {{ background-color: {bg_color}; color: {text_color} !important; }}
       h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: {text_color} !important; }}
@@ -48,78 +73,126 @@
           margin-bottom: 12px;
       }}
   </style>
""", unsafe_allow_html=True)
""",
    unsafe_allow_html=True,
)

# --- Header ---
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.markdown(f"""
  st.markdown(
      f"""
       <div style="margin-bottom: 12px;">
           <h1 style="margin: 0; color: {accent_aqua}; font-weight: 900; font-size: 2.3rem;">⚡ AtmoSync Emergency Network</h1>
           <div style="font-size: 1.05rem; color: {accent_aqua}; font-weight: 600;">Early Warning System & Off-Grid Navigation</div>
       </div>
    """, unsafe_allow_html=True)
    """,
      unsafe_allow_html=True,
  )
with header_col2:
    if st.button("☀️" if st.session_state.dark_mode else "🌙", key="btn_theme_toggle_header"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
  if st.button(
      "☀️" if st.session_state.dark_mode else "🌙",
      key="btn_theme_toggle_header",
  ):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

# --- Navigation Bar ---
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("🏠 Home", key="nav_btn_home", use_container_width=True):
        st.session_state.current_tab = "🏠 Home"
        st.rerun()
  if st.button("🏠 Home", key="nav_btn_home", use_container_width=True):
    st.session_state.current_tab = "🏠 Home"
    st.rerun()
with nav_col2:
    if st.button("📡 Live Weather & GPS Map", key="nav_btn_map", use_container_width=True):
        st.session_state.current_tab = "📡 Live Weather & GPS Map"
        st.rerun()
  if st.button(
      "📡 Live Weather & GPS Map", key="nav_btn_map", use_container_width=True
  ):
    st.session_state.current_tab = "📡 Live Weather & GPS Map"
    st.rerun()
with nav_col3:
    if st.button("🧭 Compass", key="nav_btn_compass", use_container_width=True):
        st.session_state.current_tab = "🧭 Compass"
        st.rerun()
  if st.button("🧭 Compass", key="nav_btn_compass", use_container_width=True):
    st.session_state.current_tab = "🧭 Compass"
    st.rerun()
with nav_col4:
    if st.button("📋 Active Log", key="nav_btn_log", use_container_width=True):
        st.session_state.current_tab = "📋 Active Log"
        st.rerun()
  if st.button("📋 Active Log", key="nav_btn_log", use_container_width=True):
    st.session_state.current_tab = "📋 Active Log"
    st.rerun()

st.markdown("---")


# --- Robust Telemetry Fetcher ---
def fetch_pressure_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=surface_pressure,temperature_2m,relative_humidity_2m,wind_speed_10m&past_days=7"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()['hourly']
            df = pd.DataFrame({
                'time': pd.to_datetime(data['time']),
                'p (mbar)': data['surface_pressure'],
                'temp (°C)': data['temperature_2m'],
                'humidity (%)': data['relative_humidity_2m'],
                'wind (km/h)': data['wind_speed_10m']
            })
            df['delta_p_3h'] = df['p (mbar)'].diff(3).fillna(0)
            return df
    except Exception:
        pass
    
    # Fallback local dataset
    dates = pd.date_range(end=pd.Timestamp.now(), periods=168, freq='h')
    base_p = 1013.25 + np.sin(np.linspace(0, 20, 168)) * 8
    df = pd.DataFrame({
        'time': dates,
        'p (mbar)': base_p,
        'temp (°C)': 24.0 + np.sin(np.linspace(0, 10, 168)) * 3,
        'humidity (%)': 65.0,
        'wind (km/h)': 12.0,
        'delta_p_3h': pd.Series(base_p).diff(3).fillna(0)
    })
    return df

# Helper to render map
  try:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=surface_pressure,temperature_2m,relative_humidity_2m,wind_speed_10m&past_days=7"
    res = requests.get(url, timeout=4)
    if res.status_code == 200:
      data = res.json()["hourly"]
      df = pd.DataFrame({
          "time": pd.to_datetime(data["time"]),
          "p (mbar)": data["surface_pressure"],
          "temp (°C)": data["temperature_2m"],
          "humidity (%)": data["relative_humidity_2m"],
          "wind (km/h)": data["wind_speed_10m"],
      })
      df["delta_p_3h"] = df["p (mbar)"].diff(3).fillna(0)
      return df
  except Exception:
    pass

  # Fallback local dataset
  dates = pd.date_range(end=pd.Timestamp.now(), periods=168, freq="h")
  base_p = 1013.25 + np.sin(np.linspace(0, 20, 168)) * 8
  df = pd.DataFrame({
      "time": dates,
      "p (mbar)": base_p,
      "temp (°C)": 24.0 + np.sin(np.linspace(0, 10, 168)) * 3,
      "humidity (%)": 65.0,
      "wind (km/h)": 12.0,
      "delta_p_3h": pd.Series(base_p).diff(3).fillna(0),
  })
  return df


# --- AI Prediction Function ---
def predict_threat_level(latest_row):
  if ai_model is None:
    # Rule-based fallback if model file is not present
    dp = latest_row["delta_p_3h"]
    p = latest_row["p (mbar)"]
    if p < 970 or dp < -10:
      return "DISASTER", "#EF4444", 0.95
    elif 970 <= p < 1000:
      return "CAUTIONARY", "#F59E0B", 0.85
    else:
      return "NOMINAL", "#10B981", 0.99

  # Feature alignment: [surface_pressure, pressure_delta_3h, temperature, humidity, wind_speed]
  features = np.array([[
      latest_row["p (mbar)"],
      latest_row["delta_p_3h"],
      latest_row["temp (°C)"],
      latest_row["humidity (%)"],
      latest_row["wind (km/h)"],
  ]])

  pred = int(ai_model.predict(features)[0])
  probs = ai_model.predict_proba(features)[0]

  state_labels = {
      0: ("NOMINAL", "#10B981"),
      1: ("CAUTIONARY", "#F59E0B"),
      2: ("DISASTER", "#EF4444"),
  }

  label, color = state_labels.get(pred, ("UNKNOWN", "#A855F7"))
  confidence = probs[pred]
  return label, color, confidence


# --- Helper to render map ---
def render_emergency_map_with_geolocator(lat, lon, location_name):
    map_html = f"""
  map_html = f"""
   <!DOCTYPE html>
   <html>
   <head>
@@ -172,129 +245,194 @@ def render_emergency_map_with_geolocator(lat, lon, location_name):
   </body>
   </html>
   """
    components.html(map_html, height=480)
  components.html(map_html, height=480)


# Fetch data & perform AI assessment
df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
latest_telemetry = df_raw.iloc[-1]
threat_label, threat_color, confidence = predict_threat_level(latest_telemetry)

# --- TAB 1: HOME ---
if st.session_state.current_tab == "🏠 Home":
    st.title("🏠 System Overview & Command Center")
    
    # Quick Status Bar
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown(f"""
  st.title("🏠 System Overview & Command Center")

  col_s1, col_s2, col_s3, col_s4 = st.columns(4)
  with col_s1:
    st.markdown(
        f"""
           <div class="status-card">
               <div style="font-weight: bold; color: {accent_aqua};">Network Status</div>
               <div style="font-size: 1.4rem; font-weight: bold; color: #10B981;">🟢 ONLINE</div>
           </div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
        """,
        unsafe_allow_html=True,
    )
  with col_s2:
    st.markdown(
        f"""
           <div class="status-card">
               <div style="font-weight: bold; color: {accent_aqua};">Active Station</div>
               <div style="font-size: 1.1rem; font-weight: bold;">{st.session_state.city_name}</div>
           </div>
        """, unsafe_allow_html=True)
    with col_s3:
        st.markdown(f"""
        """,
        unsafe_allow_html=True,
    )
  with col_s3:
    st.markdown(
        f"""
           <div class="status-card">
                <div style="font-weight: bold; color: {accent_aqua};">Telemetry Stream</div>
                <div style="font-size: 1.4rem; font-weight: bold;">168 Hrs Cached</div>
                <div style="font-weight: bold; color: {accent_aqua};">AI Model Engine</div>
                <div style="font-size: 1.1rem; font-weight: bold;">{'XGBoost Active' if ai_model else 'Rule Engine'}</div>
           </div>
        """, unsafe_allow_html=True)
    with col_s4:
        st.markdown(f"""
        """,
        unsafe_allow_html=True,
    )
  with col_s4:
    st.markdown(
        f"""
           <div class="status-card">
                <div style="font-weight: bold; color: {accent_aqua};">Barometric Threat</div>
                <div style="font-size: 1.4rem; font-weight: bold; color: #10B981;">LOW</div>
                <div style="font-weight: bold; color: {accent_aqua};">AI Threat Level</div>
                <div style="font-size: 1.4rem; font-weight: bold; color: {threat_color};">{threat_label} ({confidence * 100:.0f}%)</div>
           </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Navigation & Actions")
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        if st.button("📡 View Live GPS Map & Graphs", use_container_width=True):
            st.session_state.current_tab = "📡 Live Weather & GPS Map"
            st.rerun()
    with q_col2:
        if st.button("🧭 Launch Emergency Compass", use_container_width=True):
            st.session_state.current_tab = "🧭 Compass"
            st.rerun()
    with q_col3:
        if st.button("📋 Access Telemetry Logs", use_container_width=True):
            st.session_state.current_tab = "📋 Active Log"
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Station Snapshot")
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    latest = df_raw.iloc[-1]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Pressure", f"{latest['p (mbar)']:.1f} mbar")
    m2.metric("Temperature", f"{latest['temp (°C)']:.1f} °C")
    m3.metric("Humidity", f"{latest['humidity (%)']:.0f}%")
    m4.metric("Wind Speed", f"{latest['wind (km/h)']:.1f} km/h")

    st.markdown("---")
    st.markdown("### 🛡️ System Capabilities")
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("""
        """,
        unsafe_allow_html=True,
    )

  st.markdown("### ⚡ Quick Navigation & Actions")
  q_col1, q_col2, q_col3 = st.columns(3)
  with q_col1:
    if st.button("📡 View Live GPS Map & Graphs", use_container_width=True):
      st.session_state.current_tab = "📡 Live Weather & GPS Map"
      st.rerun()
  with q_col2:
    if st.button("🧭 Launch Emergency Compass", use_container_width=True):
      st.session_state.current_tab = "🧭 Compass"
      st.rerun()
  with q_col3:
    if st.button("📋 Access Telemetry Logs", use_container_width=True):
      st.session_state.current_tab = "📋 Active Log"
      st.rerun()

  st.markdown("---")
  st.markdown("### 📊 Station Snapshot")

  m1, m2, m3, m4 = st.columns(4)
  m1.metric("Current Pressure", f"{latest_telemetry['p (mbar)']:.1f} mbar")
  m2.metric("Temperature", f"{latest_telemetry['temp (°C)']:.1f} °C")
  m3.metric("Humidity", f"{latest_telemetry['humidity (%)']:.0f}%")
  m4.metric("Wind Speed", f"{latest_telemetry['wind (km/h)']:.1f} km/h")

  st.markdown("---")
  st.markdown("### 🛡️ System Capabilities")
  c_a, c_b = st.columns(2)
  with c_a:
    st.markdown("""
       * **Barometric Anomaly Detection:** Monitors 3-hour drop deltas ($\Delta P$) to detect incoming extreme weather fronts or cyclonic systems.
       * **Client-Side Satellite GPS:** Pins real-time coordinates using native browser HTML5 Geolocation without server tracking.
       """)
    with c_b:
        st.markdown("""
  with c_b:
    st.markdown("""
       * **Off-Grid Telemetry Cache:** Provides continuous fallback telemetry data streams even during API interruptions.
        * **Emergency Map Display:** Interactive Leaflet map container hardcoded to maintain visibility across dynamic rerenders.
        * **XGBoost Inference Engine:** Real-time state classification (`NOMINAL`, `CAUTIONARY`, `DISASTER`) directly inside Streamlit.
       """)

# --- TAB 2: LIVE WEATHER & GPS MAP ---
elif st.session_state.current_tab == "📡 Live Weather & GPS Map":
    st.title("📡 Live Atmospheric Telemetry & GPS Station")
    
    preset_city = st.selectbox(
        "Station Location Presets", 
        ["Current Detected Station", "Miami, USA", "Reykjavik, Iceland", "Tokyo, Japan", "London, UK"]
    )
    if preset_city == "Miami, USA":
        st.session_state.lat, st.session_state.lon, st.session_state.city_name = 25.7617, -80.1918, "Miami, USA"
    elif preset_city == "Reykjavik, Iceland":
        st.session_state.lat, st.session_state.lon, st.session_state.city_name = 64.1466, -21.9426, "Reykjavik, Iceland"
    elif preset_city == "Tokyo, Japan":
        st.session_state.lat, st.session_state.lon, st.session_state.city_name = 35.6762, 139.6503, "Tokyo, Japan"
    elif preset_city == "London, UK":
        st.session_state.lat, st.session_state.lon, st.session_state.city_name = 51.5074, -0.1278, "London, UK"

    st.subheader(f"🗺️ Map Station: {st.session_state.city_name}")
    render_emergency_map_with_geolocator(st.session_state.lat, st.session_state.lon, st.session_state.city_name)

    st.markdown("---")
    st.subheader("📊 Live Telemetry Graph")
    
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    latest = df_raw.iloc[-1]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Surface Pressure", f"{latest['p (mbar)']:.1f} mbar")
    m2.metric("Temperature", f"{latest['temp (°C)']:.1f} °C")
    m3.metric("Humidity", f"{latest['humidity (%)']:.0f}%")
    m4.metric("Wind Speed", f"{latest['wind (km/h)']:.1f} km/h")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Surface Pressure (mbar)", "3-Hour Pressure Delta (mbar)"))
    fig.add_trace(go.Scatter(x=df_raw['time'], y=df_raw['p (mbar)'], name='Pressure', line=dict(color=accent_aqua, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_raw['time'], y=df_raw['delta_p_3h'], name='ΔP 3h', line=dict(color='#A855F7', width=2)), row=2, col=1)
    fig.update_layout(height=420, template=plot_template, margin=dict(l=20, r=20, t=40, b=20))
    
    st.plotly_chart(fig, use_container_width=True)
  st.title("📡 Live Atmospheric Telemetry & GPS Station")

  preset_city = st.selectbox(
      "Station Location Presets",
      [
          "Current Detected Station",
          "Miami, USA",
          "Reykjavik, Iceland",
          "Tokyo, Japan",
          "London, UK",
      ],
  )
  if preset_city == "Miami, USA":
    (
        st.session_state.lat,
        st.session_state.lon,
        st.session_state.city_name,
    ) = (25.7617, -80.1918, "Miami, USA")
  elif preset_city == "Reykjavik, Iceland":
    (
        st.session_state.lat,
        st.session_state.lon,
        st.session_state.city_name,
    ) = (64.1466, -21.9426, "Reykjavik, Iceland")
  elif preset_city == "Tokyo, Japan":
    (
        st.session_state.lat,
        st.session_state.lon,
        st.session_state.city_name,
    ) = (35.6762, 139.6503, "Tokyo, Japan")
  elif preset_city == "London, UK":
    (
        st.session_state.lat,
        st.session_state.lon,
        st.session_state.city_name,
    ) = (51.5074, -0.1278, "London, UK")

  st.subheader(f"🗺️ Map Station: {st.session_state.city_name}")
  render_emergency_map_with_geolocator(
      st.session_state.lat, st.session_state.lon, st.session_state.city_name
  )

  st.markdown("---")
  st.subheader("📊 Live Telemetry Graph")

  m1, m2, m3, m4 = st.columns(4)
  m1.metric("Surface Pressure", f"{latest_telemetry['p (mbar)']:.1f} mbar")
  m2.metric("Temperature", f"{latest_telemetry['temp (°C)']:.1f} °C")
  m3.metric("Humidity", f"{latest_telemetry['humidity (%)']:.0f}%")
  m4.metric("Wind Speed", f"{latest_telemetry['wind (km/h)']:.1f} km/h")

  fig = make_subplots(
      rows=2,
      cols=1,
      shared_xaxes=True,
      subplot_titles=(
          "Surface Pressure (mbar)",
          "3-Hour Pressure Delta (mbar)",
      ),
  )
  fig.add_trace(
      go.Scatter(
          x=df_raw["time"],
          y=df_raw["p (mbar)"],
          name="Pressure",
          line=dict(color=accent_aqua, width=2),
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=df_raw["time"],
          y=df_raw["delta_p_3h"],
          name="ΔP 3h",
          line=dict(color="#A855F7", width=2),
      ),
      row=2,
      col=1,
  )
  fig.update_layout(
      height=420,
      template=plot_template,
      margin=dict(l=20, r=20, t=40, b=20),
  )

  st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: COMPASS ---
elif st.session_state.current_tab == "🧭 Compass":
    st.title("🧭 Compass Navigation")
    st.write("Navigation module active.")
  st.title("🧭 Compass Navigation")
  st.write("Navigation module active.")

# --- TAB 4: ACTIVE LOG ---
elif st.session_state.current_tab == "📋 Active Log":
    st.title("📋 Telemetry Log")
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    st.dataframe(df_raw, use_container_width=True)
  st.title("📋 Telemetry Log")
  st.dataframe(df_raw, use_container_width=True)
