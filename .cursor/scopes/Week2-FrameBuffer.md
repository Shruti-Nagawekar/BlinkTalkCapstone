## Week 2 — Frame Plumbing & Buffer (Spec)

### Purpose & User Problem
- **Purpose**: Enable the backend to accept camera frames from the Swift app and safely expose the latest frame to downstream processing (blink detection in later weeks).
- **User problem**: Provide reliable, low-latency ingestion so users can stream blinks without UI freezes or backend contention.

### Success Criteria
- **API**: `POST /api/frame` accepts base64 JPEG and returns JSON `{ "ok": true, "bytes": <int> }` on success; rejects invalid input with clear error.
- **Buffer**: Thread-safe latest-frame buffer with overwrite semantics (drop older frames when a new one arrives).
- **Logging**: On ingest, log decoded size and basic diagnostics (at info/debug level).
- **Tests**: Unit tests cover buffer thread-safety semantics and basic endpoint validation.
- **Run**: `make run` exposes endpoint; manual curl with a small JPEG base64 succeeds; sizes logged.

### Scope (This Week)
- Implement `py/core/frame_buffer.py`:
  - A class `LatestFrameBuffer` with methods: `set(frame_bytes: bytes, meta: dict | None)`, `get() -> tuple[bytes | None, dict]`, `clear()`.
  - Non-blocking writes; reads return the latest snapshot; internal monotonic version counter.
  - Lightweight metadata support (timestamp, user, size).
- Implement `POST /api/frame` in `py/api/routers/frame.py`:
  - Request model: `{ "frame_b64": str, "user": str }`.
  - Decode base64 → bytes; minimal validation (JPEG magic optional); push to buffer with metadata.
  - Return JSON `{ ok: true, bytes: int }`.
- Wire buffer as a singleton dependency within the FastAPI app module scope.
- Add unit tests under `py/tests/`:
  - Buffer concurrency semantics (multi-writer overwrite, single-reader latest view).
  - API validation: missing fields, bad base64 → 422/400; happy path returns byte count.

### Out of Scope (This Week)
- Blink/EAR detection, classification, and translation logic.
- Persistence or streaming of historical frames.
- Authentication, rate limiting, or storage quotas.

### Constraints & Considerations
- **Throughput**: Camera sends ~5–10 FPS; network and decoding must avoid backpressure: client should skip if request in flight (handled in Swift Week 6) while server simply overwrites latest.
- **Thread Safety**: Use `threading.Lock()` or `RLock()` around internal state; keep critical sections minimal.
- **Memory**: Store only the latest frame to bound memory usage.
- **Error Handling**: Clear JSON errors; avoid leaking internal traces by default.
- **CORS**: Already enabled globally.

### API Contract
- Path: `POST /api/frame`
- Request JSON:
  - `frame_b64` (string, required): base64-encoded JPEG bytes.
  - `user` (string, required): opaque user identifier for logs/metadata.
- Response 200 JSON:
  - `ok` (bool)
  - `bytes` (int): decoded frame length in bytes
  - Optional: `message` on soft warnings
- Errors:
  - 400: invalid base64 or empty payload
  - 422: validation errors (missing fields)

### Design: LatestFrameBuffer
- Internal state: `{ frame: bytes | None, meta: dict, version: int }` guarded by a lock.
- `set(bytes, meta)`: acquire lock, assign, increment version, release.
- `get()`: acquire lock, copy references (bytes are immutable), return `(frame, meta.copy())` to avoid external mutation.
- `clear()`: reset to `None` with version increment.
- Provide simple metrics via metadata (e.g., `received_at` monotonic/time, `size_bytes`, `user`).

### Testing Plan
- Unit tests for buffer:
  - Initial state is empty.
  - After N sets, `get()` returns the last value and metadata.
  - Concurrent writers: final state equals the last write (simulate with threads).
- API tests (FastAPI TestClient):
  - Happy path: valid small JPEG base64 → 200; `bytes` matches decoded length.
  - Missing `frame_b64` or `user` → 422.
  - Malformed base64 → 400.
- Enhanced health tests:
  - Verify FastAPI app configuration and communication.
  - Test CORS headers are present.
  - Validate JSON response format and content-type.

### Acceptance (Week 2)
- Local round-trip verified: posting a base64 JPEG logs frame size; buffer updated.
- Swift can start/stop streaming without crashes (server side tolerant); timeouts handled later in Swift.

### Implementation Notes
- Keep the buffer module independent of FastAPI for testability.
- Prefer standard library only for Week 2; no external imaging libs required.
- Optional JPEG magic check: ensure bytes start with `\xFF\xD8` and end with `\xFF\xD9`; log a warning if not, but do not hard-fail unless bytes are empty.

### Open Questions
- Should we cap maximum accepted frame size (e.g., 1.5 MB) to avoid abuse? Default proposal: 2 MB with 413 response.
- Should we include a simple rolling counter of dropped/overwritten frames for diagnostics?


