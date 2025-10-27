"""
FastAPI main application for BlinkTalk backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, calibration, frame, translation, vocabulary
from .middleware import RequestIDMiddleware, ErrorHandlingMiddleware

app = FastAPI(
    title="BlinkTalk API",
    description="Backend API for blink-based communication system",
    version="1.0.0"
)

# Add request ID middleware for better debugging and tracing
app.add_middleware(RequestIDMiddleware)

# Add error handling middleware for standardized error responses
app.add_middleware(ErrorHandlingMiddleware)

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
app.include_router(vocabulary.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
