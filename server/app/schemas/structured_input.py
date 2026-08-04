"""Strict input and output contracts for AnchorReach phases 2 and 4."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]
LanguageCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$",
    ),
]


def _validate_image_source(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must be a non-empty URL or local file path")

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        if not parsed.netloc:
            raise ValueError("must be a valid HTTP(S) URL")
        return value

    if "://" in value:
        raise ValueError("only HTTP(S) URLs or local file paths are supported")
    return value


class CampaignType(str, Enum):
    POSTER = "poster"
    SOCIAL_POST = "social_post"
    AD_BANNER = "ad_banner"


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: NonEmptyString
    core_selling_points: list[NonEmptyString] = Field(min_length=1)
    images: list[str] = Field(min_length=1)
    brand_name: NonEmptyString
    logo_url: str | None = None
    primary_color: HexColor | None = None

    @field_validator("images")
    @classmethod
    def validate_images(cls, values: list[str]) -> list[str]:
        return [_validate_image_source(value) for value in values]

    @field_validator("logo_url")
    @classmethod
    def validate_logo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_image_source(value)

    @field_validator("primary_color")
    @classmethod
    def normalize_primary_color(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class TargetMarket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    market_code: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z]{2}$")]
    language: LanguageCode

    @field_validator("market_code")
    @classmethod
    def normalize_market_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        parts = value.replace("_", "-").split("-")
        return "-".join([parts[0].lower(), *parts[1:]])


class StructuredCampaignInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: ProductInput
    target_markets: list[TargetMarket] = Field(min_length=1, max_length=3)
    campaign_type: CampaignType

    @field_validator("target_markets")
    @classmethod
    def reject_duplicate_markets(cls, values: list[TargetMarket]) -> list[TargetMarket]:
        market_codes = [market.market_code for market in values]
        if len(market_codes) != len(set(market_codes)):
            raise ValueError("target markets must be unique within one campaign")
        return values


class VisualAnchors(BaseModel):
    product_appearance: str
    logo_reference: str | None
    color_palette: list[HexColor] = Field(min_length=1)


class ExtractionMetadata(BaseModel):
    source_images_used: list[str] = Field(min_length=1)
    color_source: Literal["primary_color_field", "extracted_from_image"]
    extraction_timestamp: str
    appearance_extraction_method: Literal["deterministic_image_metadata"]


class AnchorBlock(BaseModel):
    visual_anchors: VisualAnchors
    locked_attributes: list[
        Literal["product_appearance", "logo_reference", "color_palette"]
    ]
    extraction_metadata: ExtractionMetadata


class ValidationWarning(BaseModel):
    field: str
    code: str
    message: str


class LocalizationReference(BaseModel):
    title: str
    authority: str
    url: str


class MarketLocalizationBrief(BaseModel):
    market_code: str
    market_name: str
    language: str
    locale: str
    text_direction: Literal["ltr", "rtl"]
    preset_status: Literal["supported", "fallback"]
    copy_guidance: list[str] = Field(min_length=1)
    visual_guidance: list[str] = Field(min_length=1)
    required_adaptations: list[str] = Field(min_length=1)
    compliance_review: list[str] = Field(min_length=1)
    source_references: list[LocalizationReference]


class LocalizationPlan(BaseModel):
    preset_version: str
    reviewed_on: str
    markets: list[MarketLocalizationBrief] = Field(min_length=1, max_length=3)
    cross_market_rules: list[str] = Field(min_length=1)
    disclaimer: str


class StructuredInputResult(BaseModel):
    structured_input: StructuredCampaignInput
    anchor_block: AnchorBlock
    localization_plan: LocalizationPlan
    warnings: list[ValidationWarning]
    agent_message: str
