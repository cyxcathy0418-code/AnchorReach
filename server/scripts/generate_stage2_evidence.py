"""Generate reproducible phase-2 acceptance evidence from the real local API."""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVER_ROOT.parent
FIXTURES = Path("tests/fixtures")
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "stage2_acceptance_evidence.json"
sys.path.insert(0, str(SERVER_ROOT))

from app.main import app  # noqa: E402


def payload(
    *,
    category: str,
    brand_name: str,
    image_name: str,
    campaign_type: str,
) -> dict:
    return {
        "product": {
            "category": category,
            "core_selling_points": ["durable construction", "designed for daily use"],
            "images": [str(FIXTURES / image_name)],
            "brand_name": brand_name,
            "logo_url": str(FIXTURES / "green.ppm"),
            "primary_color": "#2455B4",
        },
        "target_markets": [
            {"market_code": "SG", "language": "en"},
            {"market_code": "DE", "language": "de"},
        ],
        "campaign_type": campaign_type,
    }


def call(client: TestClient, case_name: str, request_payload: dict) -> dict:
    response = client.post(
        "/api/v1/anchor-reach/structured-input",
        json=request_payload,
    )
    return {
        "case": case_name,
        "status_code": response.status_code,
        "request": request_payload,
        "response": response.json(),
    }


def main() -> None:
    os.chdir(SERVER_ROOT)
    client = TestClient(app)

    normal_requests = [
        (
            "normal_wireless_earbuds",
            payload(
                category="wireless earbuds",
                brand_name="Northstar",
                image_name="blue.ppm",
                campaign_type="poster",
            ),
        ),
        (
            "normal_skin_care_serum",
            payload(
                category="skin-care serum",
                brand_name="Tidal",
                image_name="green.ppm",
                campaign_type="social_post",
            ),
        ),
        (
            "normal_travel_tumbler",
            payload(
                category="travel tumbler",
                brand_name="Emberline",
                image_name="coral.ppm",
                campaign_type="ad_banner",
            ),
        ),
    ]

    fallback_request = payload(
        category="travel tumbler",
        brand_name="Emberline",
        image_name="coral.ppm",
        campaign_type="poster",
    )
    fallback_request["product"].pop("logo_url")
    fallback_request["product"].pop("primary_color")

    missing_category = copy.deepcopy(normal_requests[0][1])
    missing_category["product"].pop("category")

    missing_image = copy.deepcopy(normal_requests[0][1])
    missing_image["product"]["images"] = ["/definitely/missing/product.png"]

    too_many_markets = copy.deepcopy(normal_requests[0][1])
    too_many_markets["target_markets"] = [
        {"market_code": code, "language": "en"}
        for code in ["SG", "DE", "AE", "US"]
    ]

    invalid_campaign = copy.deepcopy(normal_requests[0][1])
    invalid_campaign["campaign_type"] = "video"

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "POST /api/v1/anchor-reach/structured-input via FastAPI TestClient",
        "creative_lab_code_or_data_used": False,
        "normal_paths": [call(client, name, data) for name, data in normal_requests],
        "fallback_path": call(client, "fallback_no_logo_or_primary_color", fallback_request),
        "blocking_paths": [
            call(client, "missing_required_category", missing_category),
            call(client, "unreachable_image_path", missing_image),
            call(client, "more_than_three_markets", too_many_markets),
            call(client, "invalid_campaign_type", invalid_campaign),
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
