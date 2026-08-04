from __future__ import annotations

import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
MODEL_PATH = PROJECT_ROOT / "docs" / "commercial" / "phase5_unit_economics.json"


def load_model() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def test_cost_scenarios_reproduce_observed_assumptions() -> None:
    model = load_model()
    observed = model["observed_costs"]
    scenarios = model["cost_scenarios"]
    attempt = (
        observed["muapi_generation_request_usd"]
        + observed["openai_judge_estimated_usd"]
    )

    assert scenarios["verified_asset_first_pass_usd"] == round(attempt, 6)
    assert scenarios["verified_asset_one_correction_usd"] == round(2 * attempt, 6)
    assert scenarios["verified_asset_three_attempt_cap_usd"] == round(3 * attempt, 6)
    assert scenarios["three_market_campaign_first_pass_usd"] == round(3 * attempt, 6)
    assert scenarios["three_market_campaign_three_attempt_cap_usd"] == round(
        9 * attempt,
        6,
    )


def test_anchor_credit_charges_cover_each_provider_action() -> None:
    model = load_model()
    observed = model["observed_costs"]
    policy = model["anchor_credit_policy"]
    reserve = policy["reserve_usd_per_credit"]

    assert policy["generation_request_credits"] == math.ceil(
        observed["muapi_generation_request_usd"] / reserve
    )
    assert policy["judge_request_credits"] == math.ceil(
        observed["openai_judge_estimated_usd"] / reserve
    )
    assert policy["verified_asset_first_pass_credits"] == (
        policy["generation_request_credits"] + policy["judge_request_credits"]
    )
    assert policy["verified_asset_three_attempt_cap_credits"] == (
        3 * policy["verified_asset_first_pass_credits"]
    )
    assert policy["three_market_campaign_three_attempt_cap_credits"] == (
        3 * policy["verified_asset_three_attempt_cap_credits"]
    )


def test_paid_package_variable_cost_margins_are_reproducible() -> None:
    model = load_model()
    reserve = model["anchor_credit_policy"]["reserve_usd_per_credit"]

    for package in model["packages"]:
        if "variable_cost_gross_margin" not in package:
            continue
        expected_reserve = round(package["included_anchor_credits"] * reserve, 6)
        expected_profit = round(package["price_usd"] - expected_reserve, 6)
        expected_margin = round(expected_profit / package["price_usd"], 6)

        assert package["maximum_provider_reserve_usd"] == expected_reserve
        assert package["variable_cost_gross_profit_usd"] == expected_profit
        assert package["variable_cost_gross_margin"] == expected_margin


def test_business_claims_remain_explicitly_unvalidated() -> None:
    model = load_model()

    assert model["status"] == "cost_derived_pricing_hypothesis_not_demand_validated"
    assert model["observed_costs"]["sample_count"] == 1
    assert any("No package has been tested" in claim for claim in model["claim_limits"])
    team = next(package for package in model["packages"] if package["id"] == "team")
    assert team["availability"] == "post_mvp_hypothesis"
    assert team["requires_unbuilt_features"]
