"""Contracts for AnchorReach phase-3 consistency evaluation."""

from __future__ import annotations

from enum import Enum
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.schemas.structured_input import AnchorBlock, StructuredCampaignInput


DEFAULT_PASS_THRESHOLD = 80.0
DEFAULT_MINIMUM_DIMENSION_SCORE = 60.0
DEFAULT_MAX_ATTEMPTS = 3


class AnchorDimension(str, Enum):
    PRODUCT_APPEARANCE = "product_appearance"
    LOGO_REFERENCE = "logo_reference"
    COLOR_PALETTE = "color_palette"


class LogoHardFailureCode(str, Enum):
    CORE_COLOR_CHANGED = "core_color_changed"
    MARK_STRUCTURE_CHANGED = "mark_structure_changed"
    BRAND_WORDING_CHANGED = "brand_wording_changed"
    REFERENCE_MARK_MISSING = "reference_mark_missing"
    INVENTED_BRAND_MARK = "invented_brand_mark"


class JudgeDimensionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(min_length=1, max_length=6)
    discrepancies: list[str] = Field(default_factory=list, max_length=6)
    hard_failure_codes: list[LogoHardFailureCode] = Field(
        default_factory=list,
        max_length=5,
    )
    hard_failure_reasons: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_hard_failure_evidence(self) -> "JudgeDimensionAssessment":
        if bool(self.hard_failure_codes) != bool(self.hard_failure_reasons):
            raise ValueError(
                "hard_failure_codes and hard_failure_reasons must either both be empty "
                "or both contain values"
            )
        return self


class JudgeAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_appearance: JudgeDimensionAssessment
    logo_reference: JudgeDimensionAssessment | None = None
    color_palette: JudgeDimensionAssessment
    summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_logo_only_hard_failures(self) -> "JudgeAssessment":
        for name, assessment in (
            ("product_appearance", self.product_appearance),
            ("color_palette", self.color_palette),
        ):
            if assessment.hard_failure_codes:
                raise ValueError(
                    f"{name} cannot contain logo-specific hard failure codes"
                )
        return self


class ConsistencyCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_block: AnchorBlock
    generated_asset_url: str
    structured_input: StructuredCampaignInput | None = None
    attempt_number: int = Field(default=1, ge=1)
    max_attempts: int = Field(default=DEFAULT_MAX_ATTEMPTS, ge=1, le=5)
    pass_threshold: float = Field(default=DEFAULT_PASS_THRESHOLD, ge=0, le=100)
    minimum_dimension_score: float = Field(
        default=DEFAULT_MINIMUM_DIMENSION_SCORE,
        ge=0,
        le=100,
    )

    @field_validator("generated_asset_url")
    @classmethod
    def validate_generated_asset_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must be a non-empty HTTP(S) URL or local file path")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        if "://" in value:
            raise ValueError("only HTTP(S) URLs or local file paths are supported")
        return value

    @model_validator(mode="after")
    def validate_attempt_range(self) -> "ConsistencyCheckRequest":
        if self.attempt_number > self.max_attempts:
            raise ValueError("attempt_number cannot exceed max_attempts")
        return self


class ConsistencyDimensionResult(BaseModel):
    dimension: AnchorDimension
    score: float = Field(ge=0, le=100)
    raw_judge_score: float = Field(ge=0, le=100)
    weight: float = Field(gt=0, le=1)
    passed: bool
    hard_gate_triggered: bool
    hard_failure_codes: list[LogoHardFailureCode]
    hard_failure_reasons: list[str]
    evidence: list[str]
    discrepancies: list[str]


class ConsistencyJudgeMetadata(BaseModel):
    provider: Literal["muapi_openrouter_vision", "openai_responses_vision"]
    model: str
    evaluated_at: str
    latency_ms: int = Field(ge=0)
    reference_images_used: list[str] = Field(min_length=2, max_length=4)
    generated_asset_url: str
    raw_response_sha256: str
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    configured_cost_limit_usd: float | None = Field(default=None, ge=0)


class ConsistencyReport(BaseModel):
    report_id: str
    scoring_policy_version: Literal["logo_hard_gate_v2"] = "logo_hard_gate_v2"
    attempt_number: int
    overall_score: float = Field(ge=0, le=100)
    pass_threshold: float
    minimum_dimension_score: float
    passed: bool
    dimensions: list[ConsistencyDimensionResult] = Field(min_length=1, max_length=3)
    summary: str
    judge_metadata: ConsistencyJudgeMetadata


class ConsistencyCheckResult(BaseModel):
    report: ConsistencyReport
    should_regenerate: bool
    attempts_remaining: int = Field(ge=0)
    regeneration_instruction: str | None
