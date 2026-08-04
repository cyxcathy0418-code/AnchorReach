from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


FIXTURES = Path(__file__).parent / "fixtures"
CLIENT = TestClient(app)


def make_payload(market_code: str, language: str) -> dict:
    return {
        "product": {
            "category": "reusable bottle",
            "core_selling_points": ["double-wall insulation", "leak-resistant lid"],
            "images": [str(FIXTURES / "blue.ppm")],
            "brand_name": "Northstar",
            "logo_url": str(FIXTURES / "green.ppm"),
            "primary_color": "#2455B4",
        },
        "target_markets": [
            {"market_code": market_code, "language": language},
        ],
        "campaign_type": "social_post",
    }


@pytest.mark.parametrize(
    ("market_code", "language", "locale", "direction"),
    [
        ("US", "en", "en-US", "ltr"),
        ("DE", "de", "de-DE", "ltr"),
        ("JP", "ja", "ja-JP", "ltr"),
        ("KR", "ko", "ko-KR", "ltr"),
        ("AE", "ar", "ar-AE", "rtl"),
    ],
)
def test_curated_market_presets_are_returned(
    market_code: str,
    language: str,
    locale: str,
    direction: str,
) -> None:
    response = CLIENT.post(
        "/api/v1/anchor-reach/structured-input",
        json=make_payload(market_code, language),
    )

    assert response.status_code == 200, response.text
    result = response.json()
    brief = result["localization_plan"]["markets"][0]
    assert brief["market_code"] == market_code
    assert brief["locale"] == locale
    assert brief["text_direction"] == direction
    assert brief["preset_status"] == "supported"
    assert brief["copy_guidance"]
    assert brief["visual_guidance"]
    assert brief["compliance_review"]
    assert brief["source_references"]
    assert "LOCALIZATION_PLAN" in result["agent_message"]
    assert "Do not invent prices" in result["agent_message"]


def test_three_market_plan_preserves_requested_order() -> None:
    payload = make_payload("US", "en")
    payload["target_markets"] = [
        {"market_code": "US", "language": "en"},
        {"market_code": "JP", "language": "ja"},
        {"market_code": "AE", "language": "ar"},
    ]

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    assert [market["market_code"] for market in result["localization_plan"]["markets"]] == [
        "US",
        "JP",
        "AE",
    ]
    assert "Create a separate static asset" in result["agent_message"]


def test_uae_english_switches_to_ltr_without_losing_preset() -> None:
    response = CLIENT.post(
        "/api/v1/anchor-reach/structured-input",
        json=make_payload("AE", "en"),
    )

    assert response.status_code == 200, response.text
    brief = response.json()["localization_plan"]["markets"][0]
    assert brief["preset_status"] == "supported"
    assert brief["locale"] == "en-AE"
    assert brief["text_direction"] == "ltr"


def test_unknown_market_uses_visible_fallback_warning() -> None:
    response = CLIENT.post(
        "/api/v1/anchor-reach/structured-input",
        json=make_payload("SG", "en"),
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["localization_plan"]["markets"][0]["preset_status"] == "fallback"
    assert any(warning["code"] == "market_preset_fallback" for warning in result["warnings"])


def test_duplicate_markets_are_rejected_before_generation() -> None:
    payload = make_payload("US", "en")
    payload["target_markets"] = [
        {"market_code": "US", "language": "en"},
        {"market_code": "us", "language": "en"},
    ]

    response = CLIENT.post("/api/v1/anchor-reach/structured-input", json=payload)

    assert response.status_code == 422
    field = response.json()["error"]["fields"][0]
    assert field["field"] == "target_markets"
    assert "unique" in field["reason"]


def test_localization_plan_labels_compliance_as_human_review() -> None:
    response = CLIENT.post(
        "/api/v1/anchor-reach/structured-input",
        json=make_payload("US", "en"),
    )

    assert response.status_code == 200, response.text
    plan = response.json()["localization_plan"]
    assert "not legal advice" in plan["disclaimer"]
    assert any("human publication-review" in rule for rule in plan["cross_market_rules"])
