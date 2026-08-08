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
st.set_page_config(page_title="AtmoSync Emergency Network", layout="wide")

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
    st.session_state.current_tab = "🏠 Home"

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

if 'disaster_mode_sim' not in st.session_state:
    st.session_state.disaster_mode_sim = False

if 'manual_heading' not in st.session_state:
    st.session_state.manual_heading = 42

# Dynamic Theme & Palette Definitions
if st.session_state.dark_mode:
    bg_color = "#0B0F19"
    card_bg = "#111827"
    text_color = "#FFFFFF"
    accent_aqua = "#00F0FF"
    plot_template = "plotly_dark"
    toggle_bg = "#1F2937"
    toggle_border = "#00F0FF"
    toggle_icon = "☀️"
else:
    bg_color = "#F4F7FB"
    card_bg = "#FFFFFF"
    text_color = "#0F172A"
    accent_aqua = "#0284C7"
    plot_template = "plotly_white"
    toggle_bg = "#FFF3E0"
    toggle_border = "#FF9800"
    toggle_icon = "🌙"

# --- Top Header & Adaptive Theme Toggle Button ---
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.markdown(f"<h2 style='margin: 0; color: {accent_aqua}; font-weight: 800;'>⚡ AtmoSync EN</h2>", unsafe_allow_html=True)
with header_col2:
    if st.button(toggle_icon, key="btn_theme_toggle_header", help="Toggle Light/Dark Theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

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

        /* Hero Banner */
        .hero-banner {{
            background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
            padding: 20px;
            border-radius: 12px;
            color: #FFFFFF !important;
            text-align: center;
            margin-top: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 198, 255, 0.3);
        }}
        .slogan-title {{
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
            color: #FFFFFF !important;
        }}
        .slogan-sub {{
            font-size: 1.1rem;
            opacity: 0.95;
            margin-top: 6px;
            color: #FFFFFF !important;
        }}

        /* Adaptive Theme Button */
        div[data-testid="stColumn"]:nth-child(2) button[key="btn_theme_toggle_header"] {{
            width: 48px !important;
            height: 48px !important;
            border-radius: 50% !important;
            background-color: {toggle_bg} !important;
            border: 2px solid {toggle_border} !important;
            font-size: 1.4rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 !important;
            margin-left: auto !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            transition: all 0.2s ease-in-out !important;
        }}
        
        div[data-testid="stColumn"]:nth-child(2) button[key="btn_theme_toggle_header"]:hover {{
            transform: scale(1.1) !important;
            box-shadow: 0 0 14px {toggle_border} !important;
        }}

        /* Universal Buttons */
        div.stButton > button {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: {text_color} !important;
            border: 1px solid rgba(0, 240, 255, 0.3) !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease-in-out;
        }}

        div.stButton > button:hover {{
            background-color: rgba(0, 240, 255, 0.2) !important;
            border-color: {accent_aqua} !important;
            color: {accent_aqua} !important;
        }}

        div[data-testid="stMetricValue"] {{
            color: {accent_aqua} !important;
            font-weight: 800;
        }}
    </style>
""", unsafe_allow_html=True)

# --- Hero Banner ---
st.markdown("""
    <div class="hero-banner">
        <div class="slogan-title">AtmoSync Emergency Network</div>
        <div class="slogan-sub">⚡ Resilience Redefined — Real-Time Atmospheric Telemetry & Disaster Detection</div>
    </div>
""", unsafe_allow_html=True)

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

# --- Helper: Fetch Live Atmospheric Telemetry ---
@st.cache_data(ttl=300)
def fetch_pressure_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=surface_pressure&past_days=7"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()['hourly']
    df = pd.DataFrame({'time': pd.to_datetime(data['time']), 'p (mbar)': data['surface_pressure']})
    df['delta_p_3h'] = df['p (mbar)'].diff(3)
    df['dp_dt'] = df['delta_p_3h'] / 3.0
    return df.dropna().reset_index(drop=True)

# --- Dual-State Machine Logic ---
def apply_dual_state_machine(df, inject_disaster=False, static_threshold=-2.0, recovery_threshold=-0.5, recovery_window=3):
    df_mod = df.copy()
    if inject_disaster and len(df_mod) >= 5:
        df_mod.iloc[-5:, df_mod.columns.get_loc('p (mbar)')] -= 15.0
        df_mod.iloc[-5:, df_mod.columns.get_loc('delta_p_3h')] = -6.5
        df_mod.iloc[-5:, df_mod.columns.get_loc('dp_dt')] = -2.16

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_mod[['delta_p_3h', 'dp_dt']])
    iso = IsolationForest(contamination=0.01, random_state=42)
    df_mod['is_ml_anomaly'] = iso.fit_predict(X_scaled) == -1

    states, current_state, counter = [], 'NOMINAL', 0
    for idx, row in df_mod.iterrows():
        if current_state == 'NOMINAL':
            if row['is_ml_anomaly'] and (row['delta_p_3h'] <= static_threshold):
                current_state = 'DISASTER'
                counter = 0
        elif current_state == 'DISASTER':
            if row['delta_p_3h'] > recovery_threshold:
                counter += 1
                if counter >= recovery_window:
                    current_state = 'NOMINAL'
                    counter = 0
            else:
                counter = 0
        states.append(current_state)
    df_mod['system_state'] = states
    return df_mod

# --- Helper: Render Real Magnetometer + Fallback Manual Compass ---
def render_compass_component(base_heading):
    compass_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: {card_bg};
                color: {text_color};
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                border: 2px solid #FF0055;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 0 25px rgba(255, 0, 85, 0.25);
            }}

            .badge {{
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                margin-top: 4px;
            }}
            .badge-live {{ background: rgba(0, 240, 255, 0.2); color: #00F0FF; border: 1px solid #00F0FF; }}
            .badge-manual {{ background: rgba(255, 165, 0, 0.2); color: #FFA500; border: 1px solid #FFA500; }}

            .compass-container {{
                position: relative;
                width: 210px;
                height: 210px;
                margin: 12px 0;
                cursor: grab;
            }}
            .compass-container:active {{
                cursor: grabbing;
            }}

            .compass-dial {{
                width: 100%;
                height: 100%;
                border-radius: 50%;
                border: 4px solid #FF0055;
                background: radial-gradient(circle, rgba(17,24,39,0.95) 0%, rgba(11,15,25,1) 100%);
                position: relative;
                transition: transform 0.1s cubic-bezier(0.1, 0.8, 0.3, 1);
                box-shadow: 0 0 20px rgba(255, 0, 85, 0.4);
            }}

            .cardinal {{
                position: absolute;
                font-weight: 800;
                font-size: 1.1rem;
            }}

            .north {{ top: 8px; left: 50%; transform: translateX(-50%); color: #FF0055; }}
            .south {{ bottom: 8px; left: 50%; transform: translateX(-50%); color: {accent_aqua}; }}
            .east {{ right: 12px; top: 50%; transform: translateY(-50%); color: {text_color}; }}
            .west {{ left: 12px; top: 50%; transform: translateY(-50%); color: {text_color}; }}

            .needle {{
                position: absolute;
                top: 50%;
                left: 50%;
                width: 6px;
                height: 94px;
                margin-top: -47px;
                margin-left: -3px;
                background: linear-gradient(to bottom, #FF0055 50%, #00F0FF 50%);
                clip-path: polygon(50% 0%, 100% 50%, 65% 50%, 65% 100%, 35% 100%, 35% 50%, 0% 50%);
            }}

            .heading-text {{
                font-size: 1.3rem;
                font-weight: 800;
                color: #00F0FF;
                margin-top: 4px;
            }}

            .ctrl-btn {{
                background: rgba(255, 0, 85, 0.15);
                color: #FFFFFF;
                border: 1px solid #FF0055;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                cursor: pointer;
                font-size: 0.8rem;
                margin-top: 8px;
                transition: all 0.2s;
            }}

            .ctrl-btn:hover {{
                background: #FF0055;
                box-shadow: 0 0 10px rgba(255, 0, 85, 0.5);
            }}

            .manual-controls {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 6px;
                margin-top: 10px;
                width: 100%;
                max-width: 220px;
            }}

            .slider-heading {{
                width: 100%;
                accent-color: #FF0055;
            }}

            .evac-notice {{
                font-size: 0.88rem;
                opacity: 0.9;
                margin-top: 8px;
            }}
        </style>
    </head>
    <body>

        <h3 style="margin: 0; color: #FF0055;">🧭 MAGNETOMETER COMPASS</h3>
        <div id="sensorStatusBadge" class="badge badge-manual">📡 Laptop/Manual Dial Mode</div>

        <div class="compass-container" id="compassContainer">
            <div class="compass-dial" id="compassDial">
                <div class="cardinal north">N</div>
                <div class="cardinal east">E</div>
                <div class="cardinal south">S</div>
                <div class="cardinal west">W</div>
                <div class="needle"></div>
            </div>
        </div>

        <div class="heading-text" id="headingLabel">HEADING: {base_heading}° (NE)</div>

        <button class="ctrl-btn" id="sensorBtn" onclick="requestSensorPermission()">📡 Enable Hardware Magnetometer</button>

        <div class="manual-controls">
            <span style="font-size: 0.75rem; opacity: 0.8;">Manual Dial Adjustment (Mouse/Touch Drag):</span>
            <input type="range" min="0" max="360" value="{base_heading}" class="slider-heading" id="headingSlider" oninput="onSliderMove(this.value)">
        </div>

        <div class="evac-notice">Evacuation Vector: <b>42° NORTH-EAST (1.8 km)</b></div>

        <script>
            var dial = document.getElementById('compassDial');
            var container = document.getElementById('compassContainer');
            var label = document.getElementById('headingLabel');
            var badge = document.getElementById('sensorStatusBadge');
            var sensorBtn = document.getElementById('sensorBtn');
            var slider = document.getElementById('headingSlider');

            var currentHeading = {base_heading};
            var isHardwareActive = false;

            function getDirectionLabel(heading) {{
                heading = (heading % 360 + 360) % 360;
                if (heading >= 337.5 || heading < 22.5) return "NORTH";
                if (heading >= 22.5 && heading < 67.5) return "NORTH-EAST";
                if (heading >= 67.5 && heading < 112.5) return "EAST";
                if (heading >= 112.5 && heading < 157.5) return "SOUTH-EAST";
                if (heading >= 157.5 && heading < 202.5) return "SOUTH";
                if (heading >= 202.5 && heading < 247.5) return "SOUTH-WEST";
                if (heading >= 247.5 && heading < 292.5) return "WEST";
                if (heading >= 292.5 && heading < 337.5) return "NORTH-WEST";
                return "NORTH";
            }}

            function renderHeading(deg) {{
                var norm = (deg % 360 + 360) % 360;
                var rounded = Math.round(norm);
                dial.style.transform = 'rotate(' + (-deg) + 'deg)';
                label.innerText = "HEADING: " + rounded + "° (" + getDirectionLabel(rounded) + ")";
                slider.value = rounded;
            }}

            function onSliderMove(val) {{
                if (isHardwareActive) return;
                currentHeading = parseFloat(val);
                renderHeading(currentHeading);
            }}

            // Mouse / Touch Dragging Simulation for Non-Sensor Hardware (Laptops)
            var isDragging = false;
            var startX = 0;

            container.addEventListener('mousedown', function(e) {{
                if (isHardwareActive) return;
                isDragging = true;
                startX = e.clientX;
            }});

            window.addEventListener('mousemove', function(e) {{
                if (!isDragging || isHardwareActive) return;
                var deltaX = e.clientX - startX;
                startX = e.clientX;
                currentHeading = (currentHeading + deltaX * 0.5) % 360;
                renderHeading(currentHeading);
            }});

            window.addEventListener('mouseup', function() {{ isDragging = false; }});

            // Hardware Orientation Listener (Magnetometer / Gyroscope)
            function handleOrientation(event) {{
                var compassHeading = null;

                if (event.webkitCompassHeading !== undefined && event.webkitCompassHeading !== null) {{
                    // iOS Devices
                    compassHeading = event.webkitCompassHeading;
                }} else if (event.alpha !== null) {{
                    // Android & standard HTML5 Magnetometer / Gyroscope
                    compassHeading = (360 - event.alpha) % 360;
                }}

                if (compassHeading !== null) {{
                    isHardwareActive = true;
                    badge.innerText = "⚡ REAL MAGNETOMETER ACTIVE";
                    badge.className = "badge badge-live";
                    sensorBtn.style.display = 'none';
                    renderHeading(compassHeading);
                }}
            }}

            function requestSensorPermission() {{
                if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {{
                    DeviceOrientationEvent.requestPermission().then(function(response) {{
                        if (response === 'granted') {{
                            window.addEventListener('deviceorientation', handleOrientation, true);
                        }} else {{
                            alert('Sensor permission denied. Using manual/drag mode.');
                        }}
                    }}).catch(console.error);
                }} else if ('DeviceOrientationEvent' in window) {{
                    window.addEventListener('deviceorientationabsolute', handleOrientation, true);
                    window.addEventListener('deviceorientation', handleOrientation, true);
                }} else {{
                    alert('Magnetometer sensor unavailable on this device (Standard for Laptops). Use the slider or drag the dial.');
                }}
            }}

            // Auto-detect if device naturally emits orientation on load
            window.addEventListener('deviceorientation', function(e) {{
                if (e.alpha !== null || e.webkitCompassHeading !== undefined) {{
                    handleOrientation(e);
                }}
            }}, {{ once: true }});

            // Initial render
            renderHeading(currentHeading);
        </script>

    </body>
    </html>
    """
    components.html(compass_html, height=480)

# -----------------------------------------------------------------------------
# TAB 1: HOME
# -----------------------------------------------------------------------------
if selected_tab == "🏠 Home":
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("🌐 Core Architecture & Mission")
        st.write("""
        AtmoSync EN monitors localized barometric pressure trends in real time to detect severe weather drops before disaster strikes.
        By pairing an **Isolation Forest ML model** with an automated **Dual-State Machine (Nominal ↔ Disaster)**,
        the system eliminates false alarms while ensuring instantaneous alerting during critical pressure drops.
        """)
        
        st.subheader("🚨 Survival Engine Control")
        st.session_state.disaster_mode_sim = st.toggle(
            "🔴 Direct Disaster Mode (Compass Survival Override)", 
            value=st.session_state.disaster_mode_sim,
            key="disaster_toggle_home"
        )
        if st.session_state.disaster_mode_sim:
            st.error("⚠️ **DISASTER SURVIVAL MODE ACTIVE:** Graphs disabled. Interactive survival compass engaged.")
        else:
            st.success("✅ Nominal Mode Active: Baseline telemetry charts loaded.")

    with col_b:
        st.subheader("📡 Station Status")
        st.metric("State Machine Core", "ACTIVE", "Latency < 10ms")
        st.metric("Survival Engine Mode", "DISASTER MODE" if st.session_state.disaster_mode_sim else "NOMINAL")
        st.metric("Active Station", st.session_state.city_name)

# -----------------------------------------------------------------------------
# TAB 2: LIVE WEATHER & GPS MAP
# -----------------------------------------------------------------------------
elif selected_tab == "📡 Live Weather & GPS Map":
    st.title("📡 Live Atmospheric Telemetry & GPS Station")
    
    # Navigation & Disaster Mode Controls
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("📍 Refresh Station GPS", key="btn_refresh_location_map"):
            lat, lon, city = get_user_location()
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = lat, lon, city
            st.success(f"Located: {city}")
            st.rerun()
    with c2:
        preset_city = st.selectbox(
            "Choose Station Location Preset", 
            ["Current Live Location", "Miami (Storm Zone)", "Reykjavik (High Delta)", "Tokyo", "London"],
            key="preset_city_select"
        )
        if preset_city == "Current Live Location":
            lat, lon, city = get_user_location()
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = lat, lon, city
        elif preset_city == "Miami (Storm Zone)":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 25.7617, -80.1918, "Miami, USA"
        elif preset_city == "Reykjavik (High Delta)":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 64.1466, -21.9426, "Reykjavik, Iceland"
        elif preset_city == "Tokyo":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 35.6762, 139.6503, "Tokyo, Japan"
        elif preset_city == "London":
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = 51.5074, -0.1278, "London, UK"
    with c3:
        st.session_state.disaster_mode_sim = st.toggle(
            "🔴 Disaster Survival Mode", 
            value=st.session_state.disaster_mode_sim,
            key="disaster_toggle_map"
        )

    # Fetch Telemetry
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    if df_raw is not None:
        df_proc = apply_dual_state_machine(df_raw, inject_disaster=st.session_state.disaster_mode_sim)
        latest_state = df_proc['system_state'].iloc[-1]

        # DISASTER MODE: INTERACTIVE CONTROLLED COMPASS
        if latest_state == 'DISASTER' or st.session_state.disaster_mode_sim:
            st.error(f"🚨 CRITICAL ALARM: DISASTER SURVIVAL MODE ENGAGED FOR {st.session_state.city_name.upper()}")
            
            heading_angle = st.slider("🧭 Set Baseline Center Heading (°)", 0, 360, 42, step=1, key="compass_angle_slider")
            render_compass_component(heading_angle)

            surv_c1, surv_c2, surv_c3 = st.columns(3)
            surv_c1.metric("Emergency Evac Vector", "42° NE", "Safe Altitude: +120m")
            surv_c2.metric("Barometric Drop Rate", f"{df_proc['dp_dt'].iloc[-1]:.2f} mbar/h", "CRITICAL")
            surv_c3.metric("Emergency Beacon Signal", "BROADCASTING", "Frequency 433 MHz")
            
        else:
            # NOMINAL MODE: standard charts and metrics
            st.success(f"✅ NOMINAL MONITORING MODE: {st.session_state.city_name}")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Current Location", st.session_state.city_name)
            m2.metric("Barometric Pressure", f"{df_proc['p (mbar)'].iloc[-1]:.2f} mbar")
            m3.metric("3-Hour ΔP Drop", f"{df_proc['delta_p_3h'].iloc[-1]:.2f} mbar")
            m4.metric("Disaster Events (7 Days)", (df_proc['system_state'] == 'DISASTER').sum())

            st.markdown("---")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Barometric Pressure Baseline (mbar)", "3-Hour Pressure Delta & ML Anomaly Flags"))
            fig.add_trace(go.Scatter(x=df_proc['time'], y=df_proc['p (mbar)'], name='Pressure', line=dict(color=accent_aqua)), row=1, col=1)
            
            disaster_pts = df_proc[df_proc['system_state'] == 'DISASTER']
            fig.add_trace(go.Scatter(x=disaster_pts['time'], y=disaster_pts['p (mbar)'], mode='markers', name='Disaster State', marker=dict(color='red', size=9)), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df_proc['time'], y=df_proc['delta_p_3h'], name='ΔP 3h', line=dict(color='#A855F7')), row=2, col=1)
            
            fig.update_layout(height=450, template=plot_template)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # --- Live GPS Map Container ---
        st.subheader("🗺️ Emergency Navigation Station Map")
        cur_lat = st.session_state.lat
        cur_lon = st.session_state.lon
        city_name = st.session_state.city_name
        marker_color = "#FF0055" if (latest_state == 'DISASTER' or st.session_state.disaster_mode_sim) else "#00F0FF"

        maplibre_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Emergency Map</title>
            <script src="https://unpkg.com/maplibre-gl@4.0.0/dist/maplibre-gl.js"></script>
            <link href="https://unpkg.com/maplibre-gl@4.0.0/dist/maplibre-gl.css" rel="stylesheet" />
            <style>
                html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
                #map {{ position: absolute; top: 0; bottom: 0; width: 100%; height: 100%; border-radius: 12px; }}
            </style>
        </head>
        <body>

        <div id="map"></div>

        <script>
            var initialLon = {cur_lon};
            var initialLat = {cur_lat};

            const map = new maplibregl.Map({{
                container: 'map',
                style: {{
                    'version': 8,
                    'sources': {{
                        'osm-tiles': {{
                            'type': 'raster',
                            'tiles': [
                                'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'
                            ],
                            'tileSize': 256,
                            'attribution': '&copy; OpenStreetMap'
                        }}
                    }},
                    'layers': [
                        {{
                            'id': 'osm-tiles-layer',
                            'type': 'raster',
                            'source': 'osm-tiles',
                            'minzoom': 0,
                            'maxzoom': 19
                        }}
                    ]
                }},
                center: [initialLon, initialLat],
                zoom: 12
            }});

            map.addControl(new maplibregl.NavigationControl());

            var marker = new maplibregl.Marker({{ color: '{marker_color}' }})
                .setLngLat([initialLon, initialLat])
                .setPopup(new maplibregl.Popup().setHTML("<b>Station: {city_name}</b><br>State: {'SURVIVAL MODE' if st.session_state.disaster_mode_sim else latest_state}"))
                .addTo(map);

            if ('geolocation' in navigator) {{
                navigator.geolocation.watchPosition(
                    function(position) {{
                        var liveLat = position.coords.latitude;
                        var liveLon = position.coords.longitude;

                        marker.setLngLat([liveLon, liveLat]);
                        map.flyTo({{ center: [liveLon, liveLat], zoom: 13 }});
                    }},
                    function(err) {{ console.warn(err.message); }},
                    {{ enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }}
                );
            }}
        </script>

        </body>
        </html>
        """
        components.html(maplibre_html, height=480)

# -----------------------------------------------------------------------------
# TAB 3: COMPASS NAVIGATION
# -----------------------------------------------------------------------------
elif selected_tab == "🧭 Compass":
    st.title("🧭 Dedicated Emergency Compass Navigation")
    st.write("Real-time magnetometer orientation telemetries (mobile devices) or manual dial/slider interaction (laptops).")
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.subheader("⚙️ Directional Controls")
        heading_angle = st.slider("Set Baseline Heading (°)", 0, 360, 42, step=1, key="standalone_compass_slider")
        
        st.markdown("---")
        st.subheader("📍 Waypoint Vectors")
        st.metric("Primary Evacuation Zone", "42° NE", "1.8 km target")
        st.metric("High-Ground Shelter", "128° SE", "+240m elevation")
        st.metric("Medical Relay Node", "295° NW", "0.9 km distance")

    with col_c2:
        render_compass_component(heading_angle)

# -----------------------------------------------------------------------------
# TAB 4: ACTIVE LOG
# -----------------------------------------------------------------------------
elif selected_tab == "📋 Active Log":
    st.title("📋 Telemetry Event & Anomaly Log")
    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    if df_raw is not None:
        df_proc = apply_dual_state_machine(df_raw, inject_disaster=st.session_state.disaster_mode_sim)
        log_data = df_proc[(df_proc['system_state'] == 'DISASTER') | (df_proc['is_ml_anomaly'])]
        st.dataframe(log_data[['time', 'p (mbar)', 'delta_p_3h', 'dp_dt', 'is_ml_anomaly', 'system_state']], use_container_width=True)
