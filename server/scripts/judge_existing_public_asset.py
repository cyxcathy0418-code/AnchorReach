"""Judge an existing public acceptance asset without generating another image."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.schemas.consistency import ConsistencyCheckRequest
from app.schemas.structured_input import StructuredCampaignInput
from app.services import build_anchor_block
from app.services.consistency_service import ConsistencyService
from app.services.openai_vision_judge import OpenAIVisionJudge


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--asset-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--max-cost", type=float, required=True)
    args = parser.parse_args()

    load_dotenv(args.env_file, override=False)
    sample = json.loads(args.sample.read_text(encoding="utf-8"))
    campaign = StructuredCampaignInput.model_validate(sample["structured_input"])
    anchor_block = await build_anchor_block(campaign)
    request = ConsistencyCheckRequest(
        anchor_block=anchor_block,
        structured_input=campaign,
        generated_asset_url=args.asset_url,
        attempt_number=1,
        max_attempts=3,
        pass_threshold=sample["acceptance_policy"]["pass_threshold"],
        minimum_dimension_score=sample["acceptance_policy"][
            "minimum_dimension_score"
        ],
    )
    record = {
        "sample_id": sample["sample_id"],
        "asset_url": args.asset_url,
        "started_at": utc_now(),
        "judge_provider": "openai_responses_vision",
        "approved_judge_cap_usd": args.max_cost,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = await ConsistencyService(
            OpenAIVisionJudge(cost_limit_usd=args.max_cost)
        ).evaluate(request)
    except Exception as exc:
        record.update(
            {
                "status": "failed",
                "error": str(exc),
                "completed_at": utc_now(),
            }
        )
        args.output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    record.update(
        {
            "status": "passed" if result.report.passed else "below_threshold",
            "estimated_api_cost_usd": (
                result.report.judge_metadata.estimated_cost_usd
            ),
            "completed_at": utc_now(),
            "result": result.model_dump(mode="json"),
        }
    )
    args.output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": record["status"],
                "overall_score": record["result"]["report"]["overall_score"],
                "estimated_api_cost_usd": record["estimated_api_cost_usd"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
