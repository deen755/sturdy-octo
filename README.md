# sturdy-octo
# AtmoSync Emergency Network

Early Warning System & Off-Grid Navigation MVP.

🔗 **Live Demo:** https://atmosyncen.streamlit.app

## ⚡ Progressive Web App (PWA) & Offline Telemetry Engine

AtmoSync EN combines a FastAPI/Vercel backend gateway with an offline-first Progressive Web App designed for emergency responders in degraded network environments.

### Key Architecture Highlights
* **Root-Scoped Service Worker (`/sw.js`):** Served directly from the application root to provide full-origin caching and network interception.
* **IndexedDB Offline Queue (`db.js`):** Automatically caches telemetry logs locally. If network connectivity drops, the UI seamlessly transitions to cached historical data.
* **True 3-Hour $\Delta P$ Threat Classification:** Scans local time-series records to compute pressure drops over a genuine 3-hour window ($\pm 45$ min tolerance) rather than adjacent 5-minute polls.
* **Fail-Safe API Gateway (`api/index.py`):** Passes live telemetry from Open-Meteo or returns a clean `503` upstream status to trigger client-side offline rendering without synthetic data injection.
