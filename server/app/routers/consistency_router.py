"""Phase-3 consistency scoring endpoint for generated static assets."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.consistency import ConsistencyCheckRequest, ConsistencyCheckResult
from app.services.consistency_service import ConsistencyService
from app.services.openai_vision_judge import OpenAIVisionJudge
from app.services.vision_judge import MuAPIVisionJudge, VisionJudgeError


router = APIRouter()


def get_consistency_service() -> ConsistencyService:
    provider = os.getenv("ANCHORREACH_JUDGE_PROVIDER", "openai").strip().lower()
    if provider == "muapi":
        return ConsistencyService(MuAPIVisionJudge())
    return ConsistencyService(OpenAIVisionJudge())


@router.post("/consistency-check", response_model=ConsistencyCheckResult)
async def consistency_check(
    request: ConsistencyCheckRequest,
    service: ConsistencyService = Depends(get_consistency_service),
) -> ConsistencyCheckResult | JSONResponse:
    try:
        return await service.evaluate(request)
    except VisionJudgeError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": (
                        f"{exc.message} No consistency score was fabricated and "
                        "automatic regeneration did not start."
                    ),
                    "fields": [],
                }
            },
        )
