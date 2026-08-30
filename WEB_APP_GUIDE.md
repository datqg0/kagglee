# Kaggriculture Web Arena & Visualizer Guide

An interactive, in-browser AI battleground and visualizer for the **Kaggle Kaggriculture Competition**.

---

## 🌟 Key Features

1. **Head-to-Head Arena & Agent Management:**
   - Drag & drop or upload custom Python agents (`.py`).
   - Integrated live code editor to tweak heuristics and algorithms directly in the browser.
   - Built-in presets:
     - `main.py`: Grandmaster Melon Surge + Strawberry Factory.
     - `abc.py`: Adaptive Market Liquidation.
     - `starter.py`: Deterministic Carrot Loop baseline.
     - `random.py`: Random action exploration.
     - `pass.py`: No-op baseline.
   - Custom match configuration: Seeds and match lengths (720 turns = 30 days).

2. **Client-Side Simulation (Pyodide WebAssembly):**
   - 100% in-browser simulation executed via WebAssembly background Web Workers.
   - Simulates 720 turns in ~1.5 - 2 seconds with real-time day progression and live score tickers.
   - Zero backend server dependencies; compatible with free static hosting platforms like Vercel.

3. **Match Analytics & Visualizer:**
   - Winner Trophy Banner with net gold margins and runtime metrics.
   - Interactive HTML5 Canvas wealth growth chart comparing both players over 30 days.
   - Detailed statistics table: End balance, quadrants unlocked, harvests, market orders, farmhands hired, errors.
   - Official pixel-art visualizer with interactive board, playback controls, and turn scrubber.
   - Export match replays as standalone offline HTML files or raw JSON.

---

## 💻 Local Development

Run any standard local HTTP server:

```bash
# Python 3
python -m http.server 8000
```
Open **`http://localhost:8000`** in your browser.

---

## 🚀 Deploy to Vercel

### Option 1: Vercel CLI
```bash
npm install -g vercel
vercel
```

### Option 2: GitHub Integration
1. Push this repository to GitHub:
   ```bash
   git add .
   git commit -m "update web arena"
   git push
   ```
2. Go to [vercel.com/new](https://vercel.com/new) and import your repository.
3. Click **Deploy**. Vercel will automatically host it statically with zero build configuration needed.
