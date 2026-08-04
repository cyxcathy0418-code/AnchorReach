from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.structured_input import StructuredCampaignInput


FIXTURES = Path(__file__).parent / "fixtures"
CLIENT = TestClient(app)


def make_payload(
    *,
    category: str = "wireless earbuds",
    image: str | None = None,
    brand_name: str = "Northstar",
) -> dict:
    return {
        "product": {
            "category": category,
            "core_selling_points": ["40-hour battery", "active noise cancellation"],
            "images": [image or str(FIXTURES / "blue.ppm")],
            "brand_name": brand_name,
            "logo_url": str(FIXTURES / "green.ppm"),
            "primary_color": "#2455B4",
        },
        "target_markets": [
            {"market_code": "SG", "language": "en"},
            {"market_code": "DE", "language": "de"},
        ],
        "campaign_type": "poster",
    }


def test_schema_normalizes_codes_and_colors() -> None:
    payload = make_payload()
    payload["product"]["primary_color"] = "#aabbcc"
    payload["target_markets"][0] = {"market_code": "sg", "language": "EN"}

    parsed = StructuredCampaignInput.model_validate(payload)

    assert parsed.product.primary_color == "#AABBCC"
    assert parsed.target_markets[0].market_code == "SG"
    assert parsed.target_markets[0].language == "en"


@pytest.mark.parametrize(
    ("category", "brand_name", "image_name", "campaign_type"),
    [
        ("wireless earbuds", "Northstar", "blue.ppm", "poster"),
        ("skin-care serum", "Tidal", "green.ppm", "social_post"),
        ("travel tumbler", "Emberline", "coral.ppm", "ad_banner"),
    ],
)
def test_three_product_categories_return_anchor_blocks(
    category: str,
    brand_name: str,
    image_name: str,
    campaign_type: str,
) -> None:
    payload = make_payload(
        category=category,
        brand_name=brand_name,
        image=str(FIXTURES / image_name),
    )
    payload["campaign_type"] = campaign_type

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["structured_input"]["product"]["category"] == category
    assert result["anchor_block"]["visual_anchors"]["product_appearance"]
    assert result["anchor_block"]["visual_anchors"]["color_palette"] == ["#2455B4"]
    assert result["anchor_block"]["locked_attributes"] == [
        "product_appearance",
        "logo_reference",
        "color_palette",
    ]
    assert "ANCHOR_BLOCK" in result["agent_message"]


def test_missing_optional_logo_and_color_use_explicit_fallback() -> None:
    payload = make_payload(image=str(FIXTURES / "coral.ppm"))
    payload["product"].pop("logo_url")
    payload["product"].pop("primary_color")

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 200, response.text
    anchor = response.json()["anchor_block"]
    assert anchor["visual_anchors"]["logo_reference"] is None
    assert anchor["visual_anchors"]["color_palette"]
    assert anchor["extraction_metadata"]["color_source"] == "extracted_from_image"
    assert "logo_reference" not in anchor["locked_attributes"]


def test_missing_required_field_is_blocked_with_field_name() -> None:
    payload = make_payload()
    payload["product"].pop("category")

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "structured_input_validation_failed"
    assert error["fields"][0]["field"] == "product.category"


def test_unreachable_image_path_is_blocked() -> None:
    payload = make_payload(image="/definitely/missing/product.png")

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "anchor_extraction_failed"
    assert error["fields"][0]["field"] == "product.images.0"
    assert "does not exist" in error["fields"][0]["reason"]


def test_more_than_three_markets_is_blocked() -> None:
    payload = make_payload()
    payload["target_markets"] = [
        {"market_code": code, "language": "en"}
        for code in ["SG", "DE", "AE", "US"]
    ]

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 422
    fields = response.json()["error"]["fields"]
    assert fields[0]["field"] == "target_markets"
    assert "at most 3" in fields[0]["reason"]


def test_invalid_campaign_type_lists_allowed_values() -> None:
    payload = make_payload()
    payload["campaign_type"] = "video"

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 422
    field = response.json()["error"]["fields"][0]
    assert field["field"] == "campaign_type"
    assert "poster" in field["reason"]
    assert "social_post" in field["reason"]
    assert "ad_banner" in field["reason"]


def test_unusual_market_language_is_warning_not_blocker() -> None:
    payload = make_payload()
    payload["target_markets"] = [{"market_code": "DE", "language": "ja"}]

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 200
    warnings = response.json()["warnings"]
    assert warnings[0]["code"] == "unusual_market_language"


def test_empty_selling_points_are_rejected_by_schema() -> None:
    payload = make_payload()
    payload["product"]["core_selling_points"] = []

    with pytest.raises(ValidationError):
        StructuredCampaignInput.model_validate(payload)
