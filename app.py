import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="AtmoSync Emergency Network", layout="wide", initial_sidebar_state="collapsed")

# --- Helper: IP/GPS Location Lookup ---
def get_user_location():
    try:
        res = requests.get('https://ipapi.co/json/', timeout=3).json()
        return res.get('latitude', 25.7617), res.get('longitude', -80.1918), res.get('city', 'Live Location (Detected)')
    except Exception:
        return 25.7617, -80.1918, "Miami, USA (Default)"

# Session State Initialization
if 'lat' not in st.session_state:
    lat, lon, city = get_user_location()
    st.session_state.lat, st.session_state.lon, st.session_state.city_name = lat, lon, city

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "📡 Live Weather & GPS Map"

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

if 'disaster_mode_sim' not in st.session_state:
    st.session_state.disaster_mode_sim = False

# Dynamic Theme & Palette Definitions
if st.session_state.dark_mode:
    bg_color = "#0B0F19"
    card_bg = "#111827"
    text_color = "#FFFFFF"
    accent_aqua = "#00F0FF"
    plot_template = "plotly_dark"
    toggle_bg = "#111827"
    toggle_border = "#00F0FF"
    toggle_icon = "☀️"
else:
    bg_color = "#F4F7FB"
    card_bg = "#FFFFFF"
    text_color = "#0F172A"
    accent_aqua = "#0284C7"
    plot_template = "plotly_white"
    toggle_bg = "#FFFFFF"
    toggle_border = "#0284C7"
    toggle_icon = "🌙"

# Inject Global Adaptive CSS
st.markdown(f"""
    <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color} !important;
        }}
        h1, h2, h3, h4, h5, h6, p, label, span, div {{
            color: {text_color} !important;
        }}
        div.stButton > button[key="btn_theme_toggle_header"] {{
            border-radius: 50% !important;
            background-color: {toggle_bg} !important;
            border: 2px solid {toggle_border} !important;
            font-size: 1.3rem !important;
            height: 44px !important;
            width: 44px !important;
            float: right !important;
        }}
        div.stButton > button {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid rgba(0, 240, 255, 0.3) !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 700 !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- Header ---
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.markdown(f"""
        <div style="margin-bottom: 12px;">
            <h1 style="margin: 0; color: {accent_aqua}; font-weight: 900; font-size: 2.3rem;">⚡ AtmoSync Emergency Network</h1>
            <div style="font-size: 1.05rem; color: {accent_aqua}; font-weight: 600;">Early Warning System & Off-Grid Navigation</div>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    if st.button(toggle_icon, key="btn_theme_toggle_header"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# --- Navigation Bar ---
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("🏠 Home", key="nav_btn_home", use_container_width=True):
        st.session_state.current_tab = "🏠 Home"
        st.rerun()
with nav_col2:
    if st.button("📡 Live Weather & GPS Map", key="nav_btn_map", use_container_width=True):
        st.session_state.current_tab = "📡 Live Weather & GPS Map"
        st.rerun()
with nav_col3:
    if st.button("🧭 Compass", key="nav_btn_compass", use_container_width=True):
        st.session_state.current_tab = "🧭 Compass"
        st.rerun()
with nav_col4:
    if st.button("📋 Active Log", key="nav_btn_log", use_container_width=True):
        st.session_state.current_tab = "📋 Active Log"
        st.rerun()

st.markdown("---")
selected_tab = st.session_state.current_tab

@st.cache_data(ttl=300)
def fetch_pressure_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=surface_pressure,temperature_2m,relative_humidity_2m,wind_speed_10m&past_days=7"
    res = requests.get(url, timeout=5)
    if res.status_code != 200:
        return None
    data = res.json()['hourly']
    df = pd.DataFrame({
        'time': pd.to_datetime(data['time']),
        'p (mbar)': data['surface_pressure'],
        'temp (°C)': data['temperature_2m'],
        'humidity (%)': data['relative_humidity_2m'],
        'wind (km/h)': data['wind_speed_10m']
    })
    df['delta_p_3h'] = df['p (mbar)'].diff(3)
    df['dp_dt'] = df['delta_p_3h'] / 3.0
    return df.dropna().reset_index(drop=True)

# Helper function to render standalone Leaflet Map
def render_emergency_map(lat, lon, location_name):
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ height: 450px; width: 100%; border-radius: 12px; border: 2px solid {accent_aqua}; }}
            body {{ margin: 0; padding: 0; background: {card_bg}; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{lat}, {lon}], 12);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }}).addTo(map);
            L.marker([{lat}, {lon}]).addTo(map)
                .bindPopup('<b>Station: {location_name}</b><br>Lat: {lat}, Lon: {lon}')
                .openPopup();
        </script>
    </body>
    </html>
    """
    components.html(map_html, height=470)

# --- TAB 2: LIVE WEATHER & GPS MAP ---
if selected_tab == "📡 Live Weather & GPS Map":
    st.title("📡 Live Telemetry & Emergency Map")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("📍 Detect My Location"):
            lat, lon, city = get_user_location()
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = lat, lon, city
            st.rerun()
    with c2:
        preset_city = st.selectbox(
            "Select Station", 
            ["Current Detected Location", "Miami, USA", "Reykjavik, Iceland", "Tokyo, Japan", "London, UK"]
        )
        if preset_city == "Miami, USA":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 25.7617, -80.1918, "Miami, USA"
        elif preset_city == "Reykjavik, Iceland":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 64.1466, -21.9426, "Reykjavik, Iceland"
        elif preset_city == "Tokyo, Japan":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 35.6762, 139.6503, "Tokyo, Japan"
        elif preset_city == "London, UK":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 51.5074, -0.1278, "London, UK"

    # 1. ALWAYS RENDER MAP FIRST
    st.subheader(f"🗺️ Emergency Map Station: {st.session_state.city_name}")
    render_emergency_map(st.session_state.lat, st.session_state.lon, st.session_state.city_name)

    # 2. RENDER TELEMETRY METRICS & GRAPHS
    st.markdown("---")
    st.subheader("📊 Atmospheric Telemetry")
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    if df_raw is not None:
        latest = df_raw.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Surface Pressure", f"{latest['p (mbar)']:.1f} mbar")
        m2.metric("Temperature", f"{latest['temp (°C)']:.1f} °C")
        m3.metric("Humidity", f"{latest['humidity (%)']:.0f}%")
        m4.metric("Wind Speed", f"{latest['wind (km/h)']:.1f} km/h")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_raw['time'], y=df_raw['p (mbar)'], mode='lines', name='Pressure (mbar)', line=dict(color=accent_aqua)))
        fig.update_layout(height=350, template=plot_template, title="7-Day Historical Surface Pressure")
        st.plotly_chart(fig, use_container_width=True)

elif selected_tab == "🏠 Home":
    st.title("🏠 AtmoSync Home")
    st.write("System online. Select '📡 Live Weather & GPS Map' from the top navigation to view the station map.")

elif selected_tab == "🧭 Compass":
    st.title("🧭 Compass Navigation")
    st.write("Compass active.")

elif selected_tab == "📋 Active Log":
    st.title("📋 Telemetry Log")
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    if df_raw is not None:
        st.dataframe(df_raw, use_container_width=True)
