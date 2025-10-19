# BlinkTalk Capstone

A blink-based communication system that maps custom sequences to words, replacing traditional Morse code with a more intuitive pattern-based approach.

## Project Structure

```
BlinkTalkCapstone/
├── py/                      # Python backend (FastAPI)
│   ├── api/                 # FastAPI app, routers, models
│   ├── core/                # sequence engine, calibration, buffers
│   ├── tests/               # pytest unit/integration tests
│   └── sequences_v1.json    # sequence→word mapping
├── sw/                      # Swift frontend (SwiftUI) - handled by partner

```

## Quick Start

### Backend Setup

1. **Setup environment:**
   ```bash
   make setup
   ```

2. **Start the API server:**
   ```bash
   make run
   ```
   Server will be available at `http://localhost:8011`

3. **Run tests:**
   ```bash
   make test
   ```

4. **Format code:**
   ```bash
   make fmt
   ```

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/calibration/set` - Set calibration profile
- `POST /api/frame` - Send camera frame data
- `GET /api/translation` - Get translation result

### Development

The project follows a 9-week development plan. Currently implementing Week 1 features:

- ✅ FastAPI app structure with router stubs
- ✅ Core engine stubs for sequence processing
- ✅ Sequences vocabulary loader
- ✅ Basic test suite
- ✅ Development tooling (black, ruff, isort, pytest)

## Week 1 Acceptance Criteria

- [x] `make run` starts uvicorn on localhost:8011
- [x] `make test` runs pytest with smoke tests
- [x] FastAPI app structure with health endpoint
- [x] Sequences vocabulary loading from JSON
- [x] Development tooling configured

## Next Steps (Week 2)

- Frame buffer implementation
- Camera frame ingestion endpoint
- Thread-safe frame processing

