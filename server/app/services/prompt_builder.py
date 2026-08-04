"""Adapter from the AnchorReach phase-2 contract to the base agent chat input."""

from __future__ import annotations

import json

from app.schemas.structured_input import (
    AnchorBlock,
    LocalizationPlan,
    StructuredCampaignInput,
)


CAMPAIGN_LABELS = {
    "poster": "static poster",
    "social_post": "static social post",
    "ad_banner": "static advertising banner",
}


def build_agent_message(
    campaign: StructuredCampaignInput,
    anchor_block: AnchorBlock,
    localization_plan: LocalizationPlan,
) -> str:
    """Create a deterministic prompt without changing the upstream agent loop."""

    campaign_payload = campaign.model_dump(mode="json")
    anchor_payload = anchor_block.model_dump(mode="json")
    localization_payload = localization_plan.model_dump(mode="json")
    markets = ", ".join(
        f"{market.market_code} ({market.language})"
        for market in campaign.target_markets
    )
    campaign_label = CAMPAIGN_LABELS[campaign.campaign_type.value]

    return (
        "You are running the AnchorReach structured campaign workflow. "
        f"Create one {campaign_label} concept for each requested market: {markets}. "
        "Use the matching market brief in LOCALIZATION_PLAN for copy, typography, "
        "layout direction, visual hierarchy, and publication-review constraints. "
        "Create and label a separate static image asset for each market. "
        "Never present the compliance prompts as legal clearance. "
        "The AnchorBlock below is the source of truth: every attribute listed in "
        "locked_attributes must remain unchanged. Do not invent a logo when "
        "logo_reference is null. Use the product reference images when generating.\n\n"
        "STRUCTURED_CAMPAIGN_INPUT:\n"
        f"{json.dumps(campaign_payload, ensure_ascii=False, indent=2)}\n\n"
        "ANCHOR_BLOCK:\n"
        f"{json.dumps(anchor_payload, ensure_ascii=False, indent=2)}\n\n"
        "LOCALIZATION_PLAN:\n"
        f"{json.dumps(localization_payload, ensure_ascii=False, indent=2)}"
    )
