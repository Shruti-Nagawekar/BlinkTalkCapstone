"""
FastAPI main application for BlinkTalk backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, calibration, frame, translation

app = FastAPI(
    title="BlinkTalk API",
    description="Backend API for blink-based communication system",
    version="1.0.0"
)

# Add CORS middleware for Swift app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(calibration.router)
app.include_router(frame.router, prefix="/api", tags=["frame"])
app.include_router(translation.router, prefix="/api", tags=["translation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
