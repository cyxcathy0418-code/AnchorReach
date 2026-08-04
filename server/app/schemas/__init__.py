"""Pydantic schemas owned by the local AnchorReach application."""

from .structured_input import (
    AnchorBlock,
    CampaignType,
    LocalizationPlan,
    LocalizationReference,
    MarketLocalizationBrief,
    ProductInput,
    StructuredCampaignInput,
    StructuredInputResult,
    TargetMarket,
)
from .consistency import (
    AnchorDimension,
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyDimensionResult,
    ConsistencyJudgeMetadata,
    ConsistencyReport,
    JudgeAssessment,
    JudgeDimensionAssessment,
)

__all__ = [
    "AnchorBlock",
    "CampaignType",
    "LocalizationPlan",
    "LocalizationReference",
    "MarketLocalizationBrief",
    "ProductInput",
    "StructuredCampaignInput",
    "StructuredInputResult",
    "TargetMarket",
    "AnchorDimension",
    "ConsistencyCheckRequest",
    "ConsistencyCheckResult",
    "ConsistencyDimensionResult",
    "ConsistencyJudgeMetadata",
    "ConsistencyReport",
    "JudgeAssessment",
    "JudgeDimensionAssessment",
]
