"""
Middleware for request tracking and error handling.
"""
import logging
import uuid
import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests for better tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Calculate request processing time
        start_time = time.time()
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        # Log request
        logger.info(
            f"[{request.method}] {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Process Time: {process_time:.3f}s - "
            f"Request ID: {request_id}"
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for standardized error handling across the application."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", "unknown")
            
            # Log the error
            logger.error(
                f"Unhandled exception: {exc} - Request ID: {request_id} - "
                f"Path: {request.url.path} - Method: {request.method}",
                exc_info=True
            )
            
            # Return standardized error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": str(exc),
                    "request_id": request_id,
                    "path": request.url.path
                },
                headers={"X-Request-ID": request_id}
            )


def add_request_id_header(request: Request) -> str:
    """Helper function to get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")

