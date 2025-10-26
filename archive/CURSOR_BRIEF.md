BlinkTalkCapstone — Cursor Brief
Project intent (read me first)

We’re building a new codebase that takes inspiration from the legacy BlinkTalk implementation but changes the core logic from Morse decoding to a custom sequence→word mapping stored in sequences_v1.json.
Do not copy/paste legacy code. Reuse ideas/structure only.

Repository layout
BlinkTalkCapstone/
  OldBlinkTalk/            # legacy reference only (read-only for inspiration)
    FinalBT.py
    ServerBT.py
    SharedFrame.py
    RunBlinkTalk.py
    HomePage.swift
    User.swift
    CameraView.swift
    TranslationResultView.swift
    ... (any other legacy files)
  py/                      # NEW python backend
    api/                   # FastAPI app, routers, models
    core/                  # sequence engine, calibration, buffers
    tests/                 # pytest unit/integration tests
  sw/                      # NEW Swift frontend (SwiftUI)
    App/                   # app entry & navigation
    Views/                 # screens
    Services/              # network/config
  docs/
    CURSOR_BRIEF.md        # (this file)
  flowcharts.txt           # design notes to respect
  tickets.csv              # ignore for now
  sequences_v1.json        # NEW: sequence→word map (source of truth)

Non-negotiables / rules

Use OldBlinkTalk only as a guide to replicate behavior where helpful; no direct copy.

Replace Morse with custom sequences: we match blink patterns (short/long + gaps) to one word from sequences_v1.json.

Keep network API small and explicit. JSON in/out only. Timeouts + clear errors.

Unit tests for EAR/blink classification, gap detection, sequence parsing, JSON mapping.

Python: FastAPI + uvicorn; Swift: SwiftUI.

Code style: Python (black, ruff, isort), Swift (SwiftFormat defaults).

sequences_v1.json — initial schema

Create at repo root: sequences_v1.json

{
  "$schema_version": "1.0",
  "meta": {
    "units": {
      "short_max_ms": 350,
      "long_min_ms": 351,
      "long_max_ms": 900
    },
    "gaps": {
      "symbol_gap_max_ms": 450,
      "word_gap_min_ms": 1100
    },
    "notes": "Short/Long durations and gap thresholds may be overridden by calibration."
  },
  "vocab": [
    { "word": "yes",      "pattern": "S S" },
    { "word": "no",       "pattern": "L"   },
    { "word": "thirsty",  "pattern": "S L" },
    { "word": "hungry",   "pattern": "L S" },
    { "word": "pain",     "pattern": "S S L" },
    { "word": "tired",    "pattern": "L L" },
    { "word": "light",    "pattern": "S S S" },
    { "word": "temp",     "pattern": "S L L" },
    { "word": "bored",    "pattern": "L S S" },
    { "word": "feelings", "pattern": "L L S" }
  ]
}


Convention:

S = short blink, L = long blink.

Symbols are separated by a symbol gap.

A word gap indicates end of the word (we’re single-word MVP).

Cursor: when implementing the engine, support calibration overrides that update the thresholds in memory.

APIs (new)

POST /api/calibration/set { "profile": "slow" | "medium" | "custom" } → store server-side active profile

POST /api/calibration/custom { "short_max_ms": int, "long_min_ms": int, "long_max_ms": int, "symbol_gap_max_ms": int, "word_gap_min_ms": int } → set custom calibration thresholds

POST /api/frame { frame_b64: string, user: string } → ingest frame; engine updates live state

GET /api/translation → { "output": "yes" | "" } (one word or empty if not ready)

GET /api/health → { status: "ok" }

(Later) POST /api/calibration/save { "name": "string" } → persist thresholds

(Later) POST /api/calibration/load { "name": "string" } → load thresholds

Swift app flow (new)

Home → Calibration → Camera → Result

CalibrationView: choose slow/medium/custom (POST set), with custom allowing manual threshold input, then push Camera.

CameraView: stream frames → backend; poll /api/translation every 2s with a 10s overall timeout; on non-empty output, navigate to ResultView.

ResultView: show the final single word.

Legacy inspiration (read-only)

EAR computation, camera streaming, and server orchestration ideas exist in OldBlinkTalk/*.py and OldBlinkTalk/*.swift.

We will not decode Morse; we will reuse the notion of short/long blinks and gaps but drive them via sequences_v1.json and calibration.

9-Week Plan (Cursor: create code for each week)

For each week below, read OldBlinkTalk/ for references, follow flowcharts.txt, and implement new code under py/ and sw/. Provide diffs, tests, and a short “how to run”.

Week 1 — Bootstrap & scaffolding

Create py/api (FastAPI app, router stubs), py/core (engine stubs), py/tests.

Implement /api/health.

Add sequences_v1.json and loader utility.

Swift: app skeleton + 4 screens + basic navigation (no networking yet).

Tooling: Makefile (setup, run, test, fmt), pyproject.toml (black, ruff, isort), SwiftFormat config.

Acceptance

make run starts uvicorn on localhost:8011 (configurable).

make test runs pytest (even if only 1–2 smoke tests).

Swift builds and can navigate between screens.

Week 2 — Frame plumbing & buffer

Implement py/core/frame_buffer.py with a thread-safe latest-frame buffer (inspired by OldBlinkTalk’s SharedFrame).

Add POST /api/frame (accept base64 JPEG, decode, push into buffer).

Swift: CameraView sends frames at ~5–10 FPS with backpressure (skip if request in flight).

Acceptance

Local round-trip frame ingest verified (log frame sizes).

Swift can start/stop streaming without crashes; timeouts handled.

Week 3 — Blink detection primitives

Implement EAR calculation (dlib or mediapipe; abstract behind EyeTracker interface for testability).

Implement BlinkClassifier that turns EAR time series into events: ShortBlink, LongBlink, and emits symbol gaps & word gaps based on thresholds.

Unit tests with synthetic EAR traces.

Acceptance

Deterministic tests: given input timestamps + EARs → expected S/L and gaps.

Week 4 — Sequence engine (replace Morse)

Implement SequenceEngine that accumulates S/L tokens until a word gap, then matches against sequences_v1.json (closest match if off-by-one symbol allowed; start with exact match, add tolerance later).

Expose GET /api/translation that returns the last completed word (then clears it).

Add basic logging around classification & matching.

Acceptance

Simulated events produce correct word from JSON in unit tests.

Manual test: curl translation after sending a canned sequence → word.

Week 5 — Calibration (profiles, overrides, custom)

Implement calibration profiles (slow, medium, custom) that tweak short_max_ms, long_min/max_ms, symbol_gap_max_ms, word_gap_min_ms.

POST /api/calibration/set to switch active profile server-side.

POST /api/calibration/custom to set custom threshold values.

(Plumbing only) create stubs for save/load named calibrations (file I/O to add Week 8).

Acceptance

Switching profiles measurably changes classification thresholds (covered by tests).

Custom calibration allows users to set their own threshold values.

Week 6 — Swift networking & UX glue

Swift: Networking layer (base URL, timeouts, JSON decoding).

CalibrationView posts selected profile; CameraView streams frames; polling /api/translation every 2s with a 10s overall timeout (retry banner + cancel).

Auto-navigate to ResultView on non-empty output.

Acceptance

End-to-end local demo: pick profile → blink (or simulate) → see word.

Week 7 — Vocabulary UI & resilience

Swift: simple screen to show supported sequences_v1.json words.

Backend: add /api/vocab to return JSON vocab list (read from file).

Hardening: guard against missing camera, network errors, partial frames.

Acceptance

Vocab list renders; transient errors show friendly messages; app recovers.

Week 8 — Calibration save/load & tuning

Implement POST /api/calibration/save and POST /api/calibration/load with JSON files under py/core/calibration/.

Add quick stats logging (avg EAR, blink durations).

Tune defaults after 2–3 user trials.

Acceptance

Named calibrations persist and restore; logs show calibrated thresholds.

Week 9 — Polish & delivery

Logging: structured logs with request IDs.

Error handling: consistent JSON errors; Swift alert banners with retry.

Documentation: README for dev setup; short demo script; update flowcharts.txt if changed.

Final dry run: 10–15 min demo path recorded.

Acceptance

“Definition of Done” for MVP met: single word selected from vocab, reliably displayed.

What Cursor should do when prompted

Read this CURSOR_BRIEF.md, flowcharts.txt, and scan OldBlinkTalk/ for ideas.

For each week, create/modify files only in py/ and sw/ (and sequences_v1.json / docs).

Propose diffs + tests + run instructions.

Keep changes small and explain tradeoffs.