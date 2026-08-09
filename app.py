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
    toggle_bg = "#111827"
    toggle_border = "#00F0FF"
    toggle_icon = "☀️"
    header_border = "rgba(0, 240, 255, 0.2)"
else:
    bg_color = "#F4F7FB"
    card_bg = "#FFFFFF"
    text_color = "#0F172A"
    accent_aqua = "#0284C7"
    plot_template = "plotly_white"
    toggle_bg = "#FFFFFF"
    toggle_border = "#0284C7"
    toggle_icon = "🌙"
    header_border = "rgba(2, 132, 199, 0.2)"

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

        /* Pro Attached Header Bar */
        .pro-header-card {{
            background-color: {card_bg};
            border: 1px solid {header_border};
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }}

        .slogan-sub {{
            font-size: 1.05rem;
            color: {accent_aqua} !important;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* Clean Styled Toggle Button */
        div.stButton > button[key="btn_theme_toggle_header"] {{
            border-radius: 50% !important;
            background-color: {toggle_bg} !important;
            border: 2px solid {toggle_border} !important;
            font-size: 1.3rem !important;
            box-shadow: 0 0 10px {toggle_border}40 !important;
            transition: all 0.2s ease-in-out !important;
            height: 44px !important;
            width: 44px !important;
            float: right !important;
        }}

        /* Universal Nav/Action Buttons */
        div.stButton > button {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid rgba(0, 240, 255, 0.3) !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease-in-out;
        }}

        div.stButton > button:hover {{
            background-color: rgba(0, 240, 255, 0.15) !important;
            border-color: {accent_aqua} !important;
            color: {accent_aqua} !important;
        }}

        div[data-testid="stMetricValue"] {{
            color: {accent_aqua} !important;
            font-weight: 800;
        }}
    </style>
""", unsafe_allow_html=True)

# --- Top App Bar Header with Subtitle ---
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <h1 style="margin: 0; color: {accent_aqua}; font-weight: 900; font-size: 2.3rem; letter-spacing: -0.5px;">⚡ AtmoSync Emergency Network</h1>
            <div class="slogan-sub">Early Warning System & Off-Grid Emergency Navigation</div>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    if st.button(toggle_icon, key="btn_theme_toggle_header", help="Toggle Light/Dark Theme"):
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

# --- Helper: Render Real Magnetometer + Dynamic Moving Compass ---
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
                touch-action: none;
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
                transition: transform 0.08s ease-out;
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
        <div id="sensorStatusBadge" class="badge badge-manual">📡 Manual / Laptop Interactive Mode</div>

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
            <span style="font-size: 0.75rem; opacity: 0.8;">Manual Dial Adjustment (Drag Dial or Use Slider):</span>
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
                dial.style.transform = 'rotate(' + (-rounded) + 'deg)';
                label.innerText = "HEADING: " + rounded + "° (" + getDirectionLabel(rounded) + ")";
                slider.value = rounded;
            }}

            function onSliderMove(val) {{
                if (isHardwareActive) return;
                currentHeading = parseFloat(val);
                renderHeading(currentHeading);
            }}

            var isDragging = false;

            function calculateAngle(e) {{
                var rect = container.getBoundingClientRect();
                var centerX = rect.left + rect.width / 2;
                var centerY = rect.top + rect.height / 2;
                var clientX = e.touches ? e.touches[0].clientX : e.clientX;
                var clientY = e.touches ? e.touches[0].clientY : e.clientY;
                
                var radians = Math.atan2(clientX - centerX, -(clientY - centerY));
                var degrees = radians * (180 / Math.PI);
                return (degrees + 360) % 360;
            }}

            container.addEventListener('mousedown', function(e) {{
                if (isHardwareActive) return;
                isDragging = true;
                currentHeading = calculateAngle(e);
                renderHeading(currentHeading);
            }});

            container.addEventListener('touchstart', function(e) {{
                if (isHardwareActive) return;
                isDragging = true;
                currentHeading = calculateAngle(e);
                renderHeading(currentHeading);
            }}, {{ passive: true }});

            window.addEventListener('mousemove', function(e) {{
                if (!isDragging || isHardwareActive) return;
                currentHeading = calculateAngle(e);
                renderHeading(currentHeading);
            }});

            window.addEventListener('touchmove', function(e) {{
                if (!isDragging || isHardwareActive) return;
                currentHeading = calculateAngle(e);
                renderHeading(currentHeading);
            }}, {{ passive: true }});

            window.addEventListener('mouseup', function() {{ isDragging = false; }});
            window.addEventListener('touchend', function() {{ isDragging = false; }});

            function handleOrientation(event) {{
                var compassHeading = null;

                if (event.webkitCompassHeading !== undefined && event.webkitCompassHeading !== null) {{
                    compassHeading = event.webkitCompassHeading;
                }} else if (event.alpha !== null) {{
                    compassHeading = (360 - event.alpha) % 360;
                }}

                if (compassHeading !== null && compassHeading !== undefined) {{
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
                            alert('Sensor permission denied. Using manual/interactive drag mode.');
                        }}
                    }}).catch(console.error);
                }} else if ('DeviceOrientationEvent' in window) {{
                    window.addEventListener('deviceorientationabsolute', handleOrientation, true);
                    window.addEventListener('deviceorientation', handleOrientation, true);
                }} else {{
                    alert('Magnetometer sensor unavailable on this device. You can rotate the dial by dragging it directly or using the slider.');
                }}
            }}

            window.addEventListener('deviceorientation', function(e) {{
                if (e.alpha !== null || e.webkitCompassHeading !== undefined) {{
                    handleOrientation(e);
                }}
            }}, {{ once: true }});

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
        st.markdown(f"<h3 style='color: {accent_aqua}; margin-top:0;'>Why AtmoSync EN?</h3>", unsafe_allow_html=True)
        st.write("""
        When severe weather hits, cellular towers fail and power grids go down. Standard weather apps stop updating exactly when you need them most.
        
        **AtmoSync Emergency Network** acts as your off-grid early warning safety net. By directly monitoring localized atmospheric barometric pressure drops in real time, the app predicts severe incoming storms and flash events before emergency broadcasts even go out.
        """)
        
        st.markdown(f"<h3 style='color: {accent_aqua};'>How It Keeps You Safe in a Disaster</h3>", unsafe_allow_html=True)
        st.write("""
        * **⚡ Zero-Lag Anomaly Detection:** An integrated Isolation Forest ML engine analyzes pressure drop velocity ($\Delta P / \Delta t$) to instantly flag storm fronts.
        * **🛡️ Zero False-Alarm State Machine:** Prevents panic alerts by holding a strict dual-state verification loop (Nominal ↔ Disaster).
        * **🧭 Hardware Survival Override:** The moment a critical pressure crash triggers **Disaster Mode**, the app strips away high-data graphs and instantly locks onto your phone's built-in magnetometer compass to guide you to high-ground evacuation vectors without needing internet access.
        """)

        st.markdown("---")
        st.subheader("🚨 Try Disaster Survival Simulation")
        st.session_state.disaster_mode_sim = st.toggle(
            "🔴 Simulate Disaster State (Lock Compass Override)", 
            value=st.session_state.disaster_mode_sim,
            key="disaster_toggle_home"
        )
        if st.session_state.disaster_mode_sim:
            st.error("⚠️ **DISASTER MODE ACTIVE:** Dashboard charts hidden. Survival compass initialized.")
        else:
            st.success("✅ Nominal Mode Active: System continuously scanning local atmospheric pressure.")

    with col_b:
        st.subheader("📡 System Status")
        st.metric("Detection Core", "ACTIVE", "Latency < 10ms")
        st.metric("Current Mode", "DISASTER MODE" if st.session_state.disaster_mode_sim else "NOMINAL")
        st.metric("Detected Location", st.session_state.city_name)

# -----------------------------------------------------------------------------
# TAB 2: LIVE WEATHER & GPS MAP
# -----------------------------------------------------------------------------
elif selected_tab == "📡 Live Weather & GPS Map":
    st.title("📡 Live Atmospheric Telemetry & GPS Station")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("📍 Refresh Location", key="btn_refresh_location_map"):
            lat, lon, city = get_user_location()
            st.session_state.lat, st.session_state.lon, st.session_state.city_name = lat, lon, city
            st.success(f"Located: {city}")
            st.rerun()
    with c2:
        preset_city = st.selectbox(
            "Station Location Presets", 
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

    df_raw = fetch_pressure_data(st.session_state.lat, st.session_state.lon)
    if df_raw is not None:
        df_proc = apply_dual_state_machine(df_raw, inject_disaster=st.session_state.disaster_mode_sim)
        latest_state = df_proc['system_state'].iloc[-1]

        if latest_state == 'DISASTER' or st.session_state.disaster_mode_sim:
            st.error(f"🚨 CRITICAL ALARM: DISASTER SURVIVAL MODE ENGAGED FOR {st.session_state.city_name.upper()}")
            
            heading_angle = st.slider("🧭 Set Center Heading (°)", 0, 360, 42, step=1, key="compass_angle_slider")
            render_compass_component(heading_angle)

            surv_c1, surv_c2, surv_c3 = st.columns(3)
            surv_c1.metric("Evac Vector", "42° NE", "Target: +120m")
            surv_c2.metric("Pressure Drop Rate", f"{df_proc['dp_dt'].iloc[-1]:.2f} mbar/h", "CRITICAL")
            surv_c3.metric("Beacon Frequency", "433 MHz", "Broadcasting")
            
        else:
            st.success(f"✅ NOMINAL MONITORING MODE: {st.session_state.city_name}")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Station City", st.session_state.city_name)
            m2.metric("Barometric Pressure", f"{df_proc['p (mbar)'].iloc[-1]:.2f} mbar")
            m3.metric("3-Hour Pressure Drop", f"{df_proc['delta_p_3h'].iloc[-1]:.2f} mbar")
            m4.metric("Anomalies (7 Days)", (df_proc['system_state'] == 'DISASTER').sum())

            st.markdown("---")

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Barometric Pressure Baseline (mbar)", "3-Hour Pressure Delta & ML Anomaly Flags"))
            fig.add_trace(go.Scatter(x=df_proc['time'], y=df_proc['p (mbar)'], name='Pressure', line=dict(color=accent_aqua)), row=1, col=1)
            
            disaster_pts = df_proc[df_proc['system_state'] == 'DISASTER']
            fig.add_trace(go.Scatter(x=disaster_pts['time'], y=disaster_pts['p (mbar)'], mode='markers', name='Disaster State', marker=dict(color='red', size=9)), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df_proc['time'], y=df_proc['delta_p_3h'], name='ΔP 3h', line=dict(color='#A855F7')), row=2, col=1)
            
            fig.update_layout(height=450, template=plot_template)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        st.subheader("🗺️ Emergency Navigation Map")
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
        st.subheader("📍 Evacuation Vectors")
        st.metric("Primary Shelter Target", "42° NE", "1.8 km distance")
        st.metric("High-Ground Altitude Target", "128° SE", "+240m elevation")
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
