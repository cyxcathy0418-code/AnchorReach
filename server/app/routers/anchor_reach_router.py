"""Local phase-2 endpoints that run before requests reach MuAPI."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.structured_input import (
    StructuredCampaignInput,
    StructuredInputResult,
    ValidationWarning,
)
from app.services import (
    AnchorExtractionError,
    build_agent_message,
    build_anchor_block,
    build_localization_plan,
)


router = APIRouter()


MARKET_LANGUAGE_HINTS: dict[str, set[str]] = {
    "AE": {"ar", "en"},
    "BR": {"pt"},
    "DE": {"de"},
    "FR": {"fr"},
    "GB": {"en"},
    "ID": {"id"},
    "JP": {"ja"},
    "KR": {"ko"},
    "MX": {"es"},
    "SA": {"ar"},
    "SG": {"en", "zh", "ms", "ta"},
    "TH": {"th"},
    "US": {"en"},
    "VN": {"vi"},
}


def _market_language_warnings(
    campaign: StructuredCampaignInput,
) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []
    for index, market in enumerate(campaign.target_markets):
        expected = MARKET_LANGUAGE_HINTS.get(market.market_code)
        base_language = market.language.split("-")[0].lower()
        if expected and base_language not in expected:
            warnings.append(
                ValidationWarning(
                    field=f"target_markets.{index}.language",
                    code="unusual_market_language",
                    message=(
                        f"Language '{market.language}' is unusual for "
                        f"market '{market.market_code}'. Accepted as a warning only."
                    ),
                )
            )
    return warnings


def _market_preset_warnings(
    campaign: StructuredCampaignInput,
) -> list[ValidationWarning]:
    supported = set(MARKET_LANGUAGE_HINTS) & {"US", "DE", "JP", "KR", "AE"}
    return [
        ValidationWarning(
            field=f"target_markets.{index}.market_code",
            code="market_preset_fallback",
            message=(
                f"Market '{market.market_code}' has no curated phase-4 preset. "
                "A generic localization brief will be used and local publication review is required."
            ),
        )
        for index, market in enumerate(campaign.target_markets)
        if market.market_code not in supported
    ]


@router.post("/structured-input", response_model=StructuredInputResult)
async def validate_structured_input(
    campaign: StructuredCampaignInput,
) -> StructuredInputResult | JSONResponse:
    try:
        anchor_block = await build_anchor_block(campaign)
    except AnchorExtractionError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "anchor_extraction_failed",
                    "message": "Structured input was rejected; generation did not start.",
                    "fields": [
                        {
                            "field": exc.field,
                            "reason": exc.reason,
                            "type": "image_validation_error",
                        }
                    ],
                }
            },
        )

    localization_plan = build_localization_plan(campaign)
    return StructuredInputResult(
        structured_input=campaign,
        anchor_block=anchor_block,
        localization_plan=localization_plan,
        warnings=[
            *_market_language_warnings(campaign),
            *_market_preset_warnings(campaign),
        ],
        agent_message=build_agent_message(campaign, anchor_block, localization_plan),
    )
