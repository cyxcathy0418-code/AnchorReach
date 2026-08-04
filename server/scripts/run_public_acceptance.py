"""Run the fixed AnchorReach public Phase-3 acceptance sample against MuAPI.

The runner preserves the upstream Design Agent plan/approve loop, rejects plans
that exceed the declared budget, runs the explainable vision judge, and writes a
sanitized evidence file. It never stores the API key.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.schemas.consistency import ConsistencyCheckRequest
from app.schemas.structured_input import StructuredCampaignInput
from app.services import build_agent_message, build_anchor_block, build_localization_plan
from app.services.consistency_service import ConsistencyService
from app.services.vision_judge import MuAPIVisionJudge


DEFAULT_CAP_USD = 0.20
JUDGE_RESERVE_USD = 0.01
MAX_IMAGE_PLAN_USD = 0.10
MAX_MODELLESS_PLAN_CREDITS = 10
POLL_SECONDS = 1.5
JOB_TIMEOUT_SECONDS = 240


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def money(value: float) -> float:
    return round(value + 1e-9, 6)


class AcceptanceRunner:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        cap_usd: float,
        prior_spend_usd: float,
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_url = f"{self.base_url}/api/v1/creative-agent"
        self.api_key = api_key
        self.cap_usd = cap_usd
        self.prior_spend_usd = prior_spend_usd
        self.starting_balance = 0.0
        self.session_id: str | None = None
        self.evidence: dict[str, Any] = {
            "stage": 3,
            "sample_id": "wikimedia-bottle-sg-social-v1",
            "started_at": utc_now(),
            "status": "running",
            "source_boundary": {
                "framework_baseline": "Anil-matcha/Open-AI-Design-Agent",
                "creative_lab_code_or_data_used": False,
            },
            "spend_policy": {
                "approved_cap_usd": cap_usd,
                "prior_failed_attempt_spend_usd": prior_spend_usd,
                "maximum_total_attempts": 3,
                "maximum_generation_nodes_per_plan": 1,
                "maximum_image_plan_estimate_usd": MAX_IMAGE_PLAN_USD,
                "judge_reserve_usd": JUDGE_RESERVE_USD,
            },
            "attempts": [],
        }

    @property
    def headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}

    async def balance(self, client: httpx.AsyncClient) -> float:
        response = await client.get(
            f"{self.base_url}/api/v1/account/balance",
            headers=self.headers,
        )
        response.raise_for_status()
        payload = response.json()
        candidates = [
            payload.get("balance"),
            payload.get("credits"),
            payload.get("usd_balance"),
        ]
        data = payload.get("data")
        if isinstance(data, dict):
            candidates.extend([data.get("balance"), data.get("credits")])
        for value in candidates:
            if value is not None:
                return float(value)
        raise RuntimeError(f"Balance response contained no recognized amount: {payload}")

    async def spent(self, client: httpx.AsyncClient) -> float:
        return money(
            self.prior_spend_usd
            + self.starting_balance
            - await self.balance(client)
        )

    async def assert_budget(
        self,
        client: httpx.AsyncClient,
        *,
        additional_usd: float,
        action: str,
    ) -> None:
        spent = await self.spent(client)
        projected = money(spent + additional_usd)
        if projected > self.cap_usd + 1e-9:
            raise RuntimeError(
                f"Budget guard stopped {action}: spent ${spent:.6f}, "
                f"additional estimate ${additional_usd:.6f}, "
                f"cap ${self.cap_usd:.2f}."
            )

    async def model_cost(
        self,
        client: httpx.AsyncClient,
        model: str,
        args: dict[str, Any] | None,
    ) -> float:
        response = await client.get(f"{self.base_url}/api/v1/models/{model}")
        response.raise_for_status()
        catalog = response.json()
        cost = float(catalog.get("cost") or 0.0)
        if catalog.get("dynamic_pricing") and catalog.get("estimate_endpoint"):
            estimate = await client.post(
                f"{self.base_url}{catalog['estimate_endpoint']}",
                json=args or {},
            )
            estimate.raise_for_status()
            cost = float(estimate.json()["cost"])
        return money(cost)

    async def create_session(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            f"{self.agent_url}/sessions",
            headers=self.headers,
            json={"name": "AnchorReach public acceptance 2026-08-04"},
        )
        response.raise_for_status()
        self.session_id = str(response.json()["id"])
        self.evidence["session_id"] = self.session_id
        return self.session_id

    async def register_reference(
        self,
        client: httpx.AsyncClient,
        *,
        url: str,
        prompt: str,
    ) -> dict[str, Any]:
        assert self.session_id
        source_response = await client.get(
            url,
            headers={
                "User-Agent": (
                    "AnchorReach/0.1 public acceptance validation "
                    "(local technical test)"
                )
            },
        )
        source_response.raise_for_status()
        filename = Path(httpx.URL(url).path).name or "reference.png"
        content_type = (
            source_response.headers.get("content-type", "").split(";")[0]
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )
        signed_response = await client.get(
            f"{self.base_url}/api/v1/get_upload_url",
            headers=self.headers,
            params={"filename": filename},
        )
        signed_response.raise_for_status()
        signed = signed_response.json()
        upload_response = await client.post(
            signed["url"],
            data=signed["fields"],
            files={"file": (filename, source_response.content, content_type)},
        )
        upload_response.raise_for_status()
        hosted_url = f"https://cdn.muapi.ai/{signed['fields']['key']}"
        response = await client.post(
            f"{self.agent_url}/sessions/{self.session_id}/assets",
            headers=self.headers,
            json={
                "url": hosted_url,
                "kind": "image",
                "source_tool": "upload",
                "prompt": prompt,
            },
        )
        response.raise_for_status()
        return response.json()

    async def reject(self, client: httpx.AsyncClient, job_id: str) -> None:
        response = await client.post(
            f"{self.agent_url}/jobs/{job_id}/reject",
            headers=self.headers,
            json={},
        )
        response.raise_for_status()

    async def approve(self, client: httpx.AsyncClient, job_id: str) -> None:
        response = await client.post(
            f"{self.agent_url}/jobs/{job_id}/approve",
            headers=self.headers,
            json={},
        )
        response.raise_for_status()

    async def validate_plan(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        nodes = plan.get("nodes")
        if not isinstance(nodes, list) or len(nodes) != 1:
            await self.reject(client, job_id)
            raise RuntimeError(
                "Budget guard rejected the plan because it did not contain exactly "
                "one generation node."
            )
        node = nodes[0]
        model = node.get("model")
        tool = node.get("tool")
        if tool not in {"edit_image", "generate_image"}:
            await self.reject(client, job_id)
            raise RuntimeError(
                f"Budget guard rejected unsupported plan tool '{tool}'."
            )
        agent_credits = node.get("est_credits", node.get("credits"))
        if isinstance(model, str) and model:
            estimate = await self.model_cost(client, model, node.get("args"))
            estimate_source = "live_model_catalog"
        else:
            if (
                not isinstance(agent_credits, (int, float))
                or agent_credits > MAX_MODELLESS_PLAN_CREDITS
            ):
                await self.reject(client, job_id)
                raise RuntimeError(
                    "Budget guard rejected a model-less plan whose estimated credits "
                    f"were missing or greater than {MAX_MODELLESS_PLAN_CREDITS}."
                )
            # The live Design Agent sometimes defers model routing until execution.
            # Reserve the full per-image ceiling declared in our prompt instead of
            # inventing a credits-to-USD conversion that MuAPI does not document.
            estimate = MAX_IMAGE_PLAN_USD
            estimate_source = "declared_conservative_ceiling"
        if estimate > MAX_IMAGE_PLAN_USD:
            await self.reject(client, job_id)
            raise RuntimeError(
                f"Budget guard rejected model '{model or 'deferred'}' at ${estimate:.6f}."
            )
        await self.assert_budget(
            client,
            additional_usd=money(estimate + JUDGE_RESERVE_USD),
            action=f"plan approval for {model or 'deferred model routing'}",
        )
        await self.approve(client, job_id)
        return {
            "title": plan.get("title"),
            "tool": tool,
            "model": model,
            "catalog_estimate_usd": estimate,
            "estimate_source": estimate_source,
            "node_estimated_credits": agent_credits,
            "agent_total_credits": plan.get("total_credits"),
            "approved": True,
        }

    async def run_agent_turn(
        self,
        client: httpx.AsyncClient,
        *,
        message: str,
        attempt_number: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert self.session_id
        await self.assert_budget(
            client,
            additional_usd=JUDGE_RESERVE_USD,
            action="agent planning",
        )
        balance_before = await self.balance(client)
        response = await client.post(
            f"{self.agent_url}/sessions/{self.session_id}/chat",
            headers=self.headers,
            json={"message": message, "model": "gpt-5-mini"},
        )
        response.raise_for_status()
        job_id = str(response.json()["job_id"])
        cursor = 0
        plan_record: dict[str, Any] | None = None
        generated_assets: list[dict[str, Any]] = []
        deadline = time.monotonic() + JOB_TIMEOUT_SECONDS

        while time.monotonic() < deadline:
            await asyncio.sleep(POLL_SECONDS)
            poll_response = await client.get(
                f"{self.agent_url}/jobs/{job_id}/events",
                headers=self.headers,
                params={"since": cursor, "limit": 200},
            )
            poll_response.raise_for_status()
            poll = poll_response.json()
            cursor = int(poll.get("cursor") or cursor)
            for event in poll.get("events") or []:
                event_type = event.get("type")
                payload = event.get("payload") or {}
                if event_type == "plan_propose" and plan_record is None:
                    plan_record = await self.validate_plan(client, job_id, payload)
                if event_type == "tool_result" and isinstance(payload.get("asset"), dict):
                    asset = payload["asset"]
                    if asset.get("kind") == "image" and asset.get("url"):
                        generated_assets.append(asset)
            if poll.get("done"):
                if poll.get("status") == "failed":
                    raise RuntimeError(f"Agent job failed: {poll.get('error')}")
                break
        else:
            raise RuntimeError(f"Agent job {job_id} exceeded {JOB_TIMEOUT_SECONDS}s")

        if plan_record is None:
            raise RuntimeError("Agent completed without a plan_propose event.")
        if not generated_assets:
            assets_response = await client.get(
                f"{self.agent_url}/sessions/{self.session_id}/assets",
                headers=self.headers,
            )
            assets_response.raise_for_status()
            generated_assets = [
                asset
                for asset in assets_response.json()
                if asset.get("kind") == "image" and asset.get("source_tool") != "upload"
            ]
        if not generated_assets:
            raise RuntimeError("Agent returned no generated image asset.")

        balance_after = await self.balance(client)
        turn_record = {
            "attempt_number": attempt_number,
            "job_id": job_id,
            "plan": plan_record,
            "generation_balance_before_usd": balance_before,
            "generation_balance_after_usd": balance_after,
            "generation_actual_usd": money(balance_before - balance_after),
            "asset": generated_assets[-1],
        }
        return generated_assets[-1], turn_record

    async def run(
        self,
        *,
        sample_path: Path,
    ) -> dict[str, Any]:
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        campaign = StructuredCampaignInput.model_validate(sample["structured_input"])
        anchor_block = await build_anchor_block(campaign)
        localization_plan = build_localization_plan(campaign)
        agent_message = build_agent_message(campaign, anchor_block, localization_plan)
        product_url = campaign.product.images[0]
        logo_url = campaign.product.logo_url

        timeout = httpx.Timeout(180.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            self.starting_balance = await self.balance(client)
            self.evidence["starting_balance_usd"] = self.starting_balance
            await self.create_session(client)
            product_asset = await self.register_reference(
                client,
                url=product_url,
                prompt="Locked product reference for AnchorReach acceptance",
            )
            logo_asset = None
            if logo_url:
                logo_asset = await self.register_reference(
                    client,
                    url=logo_url,
                    prompt="Locked logo reference for AnchorReach acceptance",
                )
            self.evidence["registered_references"] = {
                "product": product_asset,
                "logo": logo_asset,
            }

            message = (
                agent_message
                + "\n\nCOST_AND_OUTPUT_CONSTRAINTS:\n"
                + "- Generate exactly one static square social image; no video, audio, "
                + "upscale, or extra variants.\n"
                + "- Use the lowest-cost suitable image-edit model with a public cost "
                + "of at most USD 0.05 per generation.\n"
                + f"- Use {product_asset['asset_label']} as the product reference.\n"
                + (
                    f"- Use {logo_asset['asset_label']} as the logo reference.\n"
                    if logo_asset
                    else ""
                )
                + "- Propose the one-node plan and wait for approval before generating."
            )

            service = ConsistencyService(
                MuAPIVisionJudge(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            )
            final_result = None
            for attempt in range(1, 4):
                asset, attempt_record = await self.run_agent_turn(
                    client,
                    message=message,
                    attempt_number=attempt,
                )
                await self.assert_budget(
                    client,
                    additional_usd=JUDGE_RESERVE_USD,
                    action="vision judge",
                )
                judge_balance_before = await self.balance(client)
                request = ConsistencyCheckRequest(
                    anchor_block=anchor_block,
                    structured_input=campaign,
                    generated_asset_url=asset["url"],
                    attempt_number=attempt,
                    max_attempts=3,
                    pass_threshold=sample["acceptance_policy"]["pass_threshold"],
                    minimum_dimension_score=sample["acceptance_policy"][
                        "minimum_dimension_score"
                    ],
                )
                result = await service.evaluate(request)
                judge_balance_after = await self.balance(client)
                attempt_record["judge_actual_usd"] = money(
                    judge_balance_before - judge_balance_after
                )
                attempt_record["consistency"] = result.model_dump(mode="json")
                self.evidence["attempts"].append(attempt_record)
                final_result = result
                if result.report.passed or not result.should_regenerate:
                    break
                spent_now = await self.spent(client)
                next_attempt_ceiling = money(
                    spent_now + MAX_IMAGE_PLAN_USD + JUDGE_RESERVE_USD
                )
                if next_attempt_ceiling > self.cap_usd + 1e-9:
                    self.evidence["regeneration_blocked"] = {
                        "reason": "approved_budget_cap",
                        "spent_so_far_usd": spent_now,
                        "next_attempt_ceiling_usd": next_attempt_ceiling,
                    }
                    break
                message = (
                    result.regeneration_instruction
                    + "\n\nGenerate exactly one corrected static image using the same "
                    + "registered product and logo references. Use a model costing no "
                    + "more than USD 0.05. Propose a one-node plan and wait for approval."
                )

            ending_balance = await self.balance(client)
            self.evidence["ending_balance_usd"] = ending_balance
            self.evidence["actual_total_spend_usd"] = money(
                self.prior_spend_usd + self.starting_balance - ending_balance
            )
            self.evidence["completed_at"] = utc_now()
            self.evidence["final_result"] = (
                final_result.model_dump(mode="json") if final_result else None
            )
            self.evidence["status"] = (
                "passed" if final_result and final_result.report.passed else "completed_below_threshold"
            )
            if self.evidence["actual_total_spend_usd"] > self.cap_usd + 1e-9:
                raise RuntimeError("Actual spend exceeded the declared cap.")
            return self.evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--budget-cap", type=float, default=DEFAULT_CAP_USD)
    parser.add_argument("--prior-spend", type=float, default=0.0)
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    load_dotenv(args.env_file, override=False)
    api_key = os.getenv("MU_API_KEY")
    if not api_key:
        raise RuntimeError("MU_API_KEY is missing from the supplied environment file.")
    runner = AcceptanceRunner(
        base_url=os.getenv("API_SUFFIX", "https://api.muapi.ai"),
        api_key=api_key,
        cap_usd=args.budget_cap,
        prior_spend_usd=args.prior_spend,
    )
    try:
        evidence = await runner.run(sample_path=args.sample)
    except Exception as exc:
        runner.evidence["status"] = "failed"
        runner.evidence["failed_at"] = utc_now()
        runner.evidence["error"] = str(exc)
        evidence = runner.evidence
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "attempts": len(evidence["attempts"]),
                "actual_total_spend_usd": evidence["actual_total_spend_usd"],
                "final_score": evidence["final_result"]["report"]["overall_score"],
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
