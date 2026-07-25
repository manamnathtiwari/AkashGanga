# AkashGanga

**Plate-solve your astrophotos.** Upload a photo of the night sky and AkashGanga maps it — identifying galaxies, nebulae, and prominent stars by name.

Built on the free [nova.astrometry.net](https://nova.astrometry.net) API. No API costs.

---

## Project layout

```
AkashGanga/
├── backend/   Python / FastAPI  (the API server)
└── app/       Flutter           (Android + iOS mobile app)
```

---

## Backend — quick start (5 minutes)

### 1. Prerequisites
- Python 3.11+  (Python 3.14 works, tested)
- No other system tools needed for dev

### 2. Create a free astrometry.net API key
1. Register at **https://nova.astrometry.net** (click *Sign In* → create account)
2. Go to **My Profile** → copy the API key

### 3. Configure the server
```bash
cd AkashGanga/backend
cp .env.example .env
# Open .env and paste your API key:
#   AKASHGANGA_ASTROMETRY_API_KEY=your_key_here
```
Leave `AKASHGANGA_SOLVER_BACKEND=mock` to run without a real key (returns fake results for testing).

### 4. Install and run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Server is live at **http://localhost:8000**
Interactive API docs: **http://localhost:8000/docs**

### 5. Run tests
```bash
pytest -q
```
Expected: **9 passed**.

---

## Flutter app — quick start

### 1. Install Flutter
```bash
# macOS (Homebrew)
brew install --cask flutter

# Or follow the official guide:
# https://docs.flutter.dev/get-started/install/macos
```
Verify: `flutter doctor`

### 2. Run the app
```bash
cd AkashGanga/app
flutter pub get

# Android emulator (make sure one is running in Android Studio / AVD Manager):
flutter run

# Specific device:
flutter run -d <device_id>
```

### 3. Connecting the app to your backend
- **Android emulator**: backend at `http://10.0.2.2:8000/api` (automatic)
- **Physical device / other**: pass the machine's LAN IP:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://192.168.1.X:8000/api
  ```

---

## Features (v1)

| Feature | Status |
|---------|--------|
| Email/password accounts + JWT auth | ✅ |
| Upload from phone gallery | ✅ |
| Capture with phone camera | ✅ |
| Submit by image URL | ✅ |
| Blind plate solving (astrometry.net API) | ✅ |
| Interactive pan/zoom viewer | ✅ |
| Overlay: galaxies, nebulae (NGC/IC/Messier) | ✅ |
| Overlay: named prominent stars (Vega, Betelgeuse, …) | ✅ |
| Tap object → detail sheet | ✅ |
| Calibration bar (RA/Dec, pixel scale, position angle) | ✅ |
| History/gallery of solved images | ✅ |
| Offline cache (last solved images work without network) | ✅ |
| Dark night-sky UI | ✅ |

---

## Switching to the real solver
Once you've added your astrometry.net API key to `.env`, set:
```
AKASHGANGA_SOLVER_BACKEND=astrometry_net
```
and restart the server. Solving typically takes 30 seconds to a few minutes depending on the image.

## Self-hosting the solver (future Phase 6)
The backend has a `SolverBackend` interface in `app/solver/base.py`. To run `solve-field` locally instead of using the web API, implement `app/solver/local_engine.py` and return it from `app/solver/factory.py`. No app changes needed.
"# AkashGanga" 
