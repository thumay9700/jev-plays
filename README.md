# jev-plays 🎮⚡

> Autonomous game-playing agent framework powered by **TypeSafe AI's Jev** — a high-speed "System One" probabilistic decision model.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-purple.svg)]()

---

## ⚡ What is Jev? (System 1 vs. System 2)

Most AI gaming agents today use traditional Large Language Models (GPT-4, Claude, Gemini). While smart, LLMs are **System 2** thinkers: they take 2 to 5 seconds to generate text token-by-token, hallucinate syntax, and cost hundreds of dollars for a single game playthrough.

**Jev** (released by TypeSafe AI) is a **System One** model. Built for raw instinct and reaction speed:
- **No text generation:** Outputs typed, probabilistic structured data in a single parallel pass.
- **Ultra-low latency:** 50ms – 150ms per decision.
- **Core Primitives:**
  - `Choice`: Categorical decision with confidence & probability distributions.
  - `Noul`: Calibrated true/false probability judgments.
  - `Score`: Rubric-based spectrum evaluations.
- **Ultra-low cost:** ~$1 to beat an entire 30-hour RPG vs $200+ with traditional LLMs.

`jev-plays` connects Jev to classic retro games via emulators (starting with **PyBoy** for the Game Boy), extracting internal memory directly into structured schemas.

---

## 🗺️ Roadmap & YouTube Video Series

This repository is designed modularly to support a continuous YouTube video series testing Jev against legendary games:

- [x] **Video #1: Pokémon Red (Game Boy)** — Can pure instinct beat the Elite Four and Champion Blue?
- [ ] **Video #2: Super Mario Bros (NES)** — Split-second obstacle avoidance and platforming reflexes.
- [ ] **Video #3: The Legend of Zelda: Link's Awakening (Game Boy)** — Spatial navigation and dungeon boss battles.
- [ ] **Video #4: Mega Man 2 (NES)** — Robot Master boss weakness choices and frame-tight reactions.
- [ ] **Video #5: Chrono Trigger (SNES)** — Complex JRPG turn-based team strategy and combo tech.

---

## 🏗️ Architecture

```
jev-plays/
├── jev_plays/
│   ├── cli.py                  # Multi-game CLI entrypoint
│   ├── core/
│   │   ├── base_agent.py       # Abstract BaseAgent interface
│   │   ├── base_game.py        # Abstract BaseGame emulator interface
│   │   ├── jev_client.py       # TypeSafe SDK wrapper + smart mock engine
│   │   └── telemetry.py        # Live metrics tracker (latency, HUD, cost)
│   └── games/
│       └── pokemon_red/
│           ├── ram_map.py       # Gen 1 Game Boy RAM offsets
│           ├── state.py         # Memory parser into Pydantic models
│           ├── tactics.py       # In-battle Choice, Noul, Score schemas
│           ├── navigator.py     # Kanto waypoint manager & pathing
│           ├── agent.py         # PokemonRedAgent orchestrator
│           └── game.py          # PyBoy emulator wrapper
└── tests/                       # Unit test suite (pytest)
```

---

## 🚀 Quickstart

### 1. Installation

Clone the repository and set up a virtual environment using `uv` (or `venv`):

```bash
git clone https://github.com/thumay9700/jev-plays.git
cd jev-plays

# Create virtual environment and install dependencies
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env.example` to `.env`:

```bash
cp env.example .env
```

Add your TypeSafe AI API key:
```bash
export TYPESAFE_API_KEY="your-typesafe-api-key"
```

### 3. Provide the ROM File

Place your legally obtained **`PokemonRed.gb`** ROM in the root directory (or specify its location with `--rom`).

---

## 🕹️ Running the Bot

### Offline Mock Mode (Zero API Cost)
Test the emulator, memory reading, and state transitions locally without spending any API credits:

```bash
python -m jev_plays.main --game pokemon_red --mock-jev --speed 0
```

### High-Speed Headless Run (Uncapped Emulation)
Run at maximum CPU speed (10x–50x speed) without opening an SDL2 window:

```bash
python -m jev_plays.main --game pokemon_red --headless --speed 0
```

### Visual 60 FPS Run (For Recording & Streaming)
Run at standard Game Boy speed (1x) with an on-screen window for OBS capture:

```bash
python -m jev_plays.main --game pokemon_red --speed 1
```

---

## 📊 Live HUD & Stream Telemetry

`jev-plays` automatically writes real-time decision telemetry to `hud_overlay.json` on every tick:

```json
{
  "model": "TypeSafe Jev (System 1)",
  "total_calls": 412,
  "latest_latency_ms": 68.4,
  "avg_latency_ms": 74.2,
  "latest_confidence": 98.6,
  "cost_usd": "$0.124",
  "latest_decisions": {
    "battle_action": { "type": "choice", "value": "fight", "confidence": 0.99 },
    "selected_move": { "type": "choice", "value": "Flamethrower", "confidence": 0.98 },
    "should_heal": { "type": "noul", "value": false },
    "wipe_risk": { "type": "score", "value": 0, "confidence": 0.95 }
  }
}
```

This file can be pointed to by an OBS Browser Source or HTML overlay to render a cyberpunk / esports-style AI Brain HUD in your YouTube video!

---

## 🧪 Running Tests

Verify the entire test suite:

```bash
pytest -v
```

---

## 📜 License

MIT License. See `LICENSE` for details.
*(Pokémon and Game Boy are trademarks of Nintendo / Creatures Inc. / GAME FREAK inc.)*
