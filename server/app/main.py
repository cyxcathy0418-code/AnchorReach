import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import anchor_reach_router, consistency_router, creative_agent_router

app = FastAPI(title="AnchorReach Creative Agent API", version="2.0.0")

app.include_router(creative_agent_router.router, prefix="/api/v1/creative-agent", tags=["creative-agent"])
app.include_router(creative_agent_router.app_router, prefix="/api/v1", tags=["app"])
app.include_router(anchor_reach_router.router, prefix="/api/v1/anchor-reach", tags=["anchor-reach"])
app.include_router(consistency_router.router, prefix="/api/v1/anchor-reach", tags=["anchor-reach"])


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    fields = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        fields.append(
            {
                "field": ".".join(location) or "request",
                "reason": error.get("msg", "Invalid value"),
                "type": error.get("type", "validation_error"),
            }
        )
    is_consistency_request = request.url.path.endswith("/consistency-check")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": (
                    "consistency_request_validation_failed"
                    if is_consistency_request
                    else "structured_input_validation_failed"
                ),
                "message": (
                    "Consistency request was rejected; no score was produced."
                    if is_consistency_request
                    else "Structured input was rejected; generation did not start."
                ),
                "fields": fields,
            }
        },
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Creative Agent Proxy API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
