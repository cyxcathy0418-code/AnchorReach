"""Phase-4 market presets and publication-review prompts.

The presets shape the creative brief. They do not decide legal compliance and
must never be treated as a substitute for market-specific professional review.
"""

from __future__ import annotations

from copy import deepcopy

from app.schemas.structured_input import (
    LocalizationPlan,
    MarketLocalizationBrief,
    StructuredCampaignInput,
)


PRESET_VERSION = "market_presets_v1"
PRESET_REVIEWED_ON = "2026-08-04"


MARKET_PRESETS: dict[str, dict] = {
    "US": {
        "market_name": "United States",
        "locale": "en-US",
        "copy_guidance": [
            "Use natural US English with a concise, benefit-first hierarchy.",
            "Use a specific call to action that matches the supplied campaign facts.",
        ],
        "visual_guidance": [
            "Use a left-to-right layout with a clear headline, product, proof, and call-to-action hierarchy.",
            "Keep qualification text readable rather than placing it in low-contrast fine print.",
        ],
        "required_adaptations": [
            "Use US spelling; convert units or currency only when the campaign supplies verified values.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Substantiate objective performance, health, environmental, origin, and comparison claims before publication.",
            "Keep necessary disclosures clear, conspicuous, close to the claim, and in the same language as the ad.",
            "Disclose endorsements, reviews, or material connections when they are used.",
        ],
        "source_references": [
            {
                "title": "Advertising and Marketing",
                "authority": "U.S. Federal Trade Commission",
                "url": "https://www.ftc.gov/business-guidance/advertising-marketing",
            },
            {
                "title": "Advertising FAQs: A Guide for Small Business",
                "authority": "U.S. Federal Trade Commission",
                "url": "https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business",
            },
        ],
    },
    "DE": {
        "market_name": "Germany",
        "locale": "de-DE",
        "copy_guidance": [
            "Use natural German with a precise value proposition and a consistent formal or informal register.",
            "Prefer concrete product information over unsupported superlatives or urgency.",
        ],
        "visual_guidance": [
            "Use a left-to-right grid and reserve extra width for longer German words.",
            "Keep price qualifications and offer conditions visually adjacent to the relevant claim.",
        ],
        "required_adaptations": [
            "Use German spelling and locale conventions; insert EUR prices only when verified values are supplied.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Check that required product and offer information is accurate, clear, and understandable.",
            "If a consumer price is shown, review taxes, calculable delivery charges, and other mandatory price information.",
            "For a price reduction, verify the applicable prior-price requirement, including the EU 30-day reference rule.",
        ],
        "source_references": [
            {
                "title": "Unfair commercial practices",
                "authority": "European Union — Your Europe",
                "url": "https://europa.eu/youreurope/citizens/consumers/unfair-treatment/unfair-commercial-practices/index_en.htm",
            },
            {
                "title": "Unfair pricing",
                "authority": "European Union — Your Europe",
                "url": "https://europa.eu/youreurope/citizens/consumers/unfair-treatment/unfair-pricing/index_en.htm",
            },
        ],
    },
    "JP": {
        "market_name": "Japan",
        "locale": "ja-JP",
        "copy_guidance": [
            "Use concise, natural Japanese rather than a literal translation of the source copy.",
            "Use a polite and credible tone; keep the primary benefit and call to action easy to scan.",
        ],
        "visual_guidance": [
            "Use Japanese-capable typography and deliberate line breaks; avoid splitting short semantic units.",
            "Maintain a clear reading order even when denser supporting information is needed.",
        ],
        "required_adaptations": [
            "Use Japanese punctuation and locale conventions; insert JPY prices only when verified values are supplied.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Review quality, performance, and price claims for representations that could make the offer appear materially better than it is.",
            "Keep objective superiority or advantage claims supported by retained evidence.",
            "Identify sponsored or incentivized recommendations as advertising when applicable.",
        ],
        "source_references": [
            {
                "title": "Establishing Trusted Representation",
                "authority": "Consumer Affairs Agency, Government of Japan",
                "url": "https://www.caa.go.jp/en/policy/representation/",
            },
        ],
    },
    "KR": {
        "market_name": "South Korea",
        "locale": "ko-KR",
        "copy_guidance": [
            "Use concise, natural Korean with a direct product benefit and clear call to action.",
            "Avoid translating source-language idioms when a locally natural phrase is available.",
        ],
        "visual_guidance": [
            "Use Hangul-capable typography, readable spacing, and controlled line breaks.",
            "Keep comparison bases and qualification text visible next to the claim they modify.",
        ],
        "required_adaptations": [
            "Use Korean locale conventions; insert KRW prices only when verified values are supplied.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Review for false or exaggerated, deceptive, unfairly comparative, or slanderous advertising.",
            "Retain objective support and applicable test conditions for factual performance claims.",
            "Disclose material benefits connected to endorsements or influencer content when applicable.",
        ],
        "source_references": [
            {
                "title": "Regulation on Unfair Labeling and Advertising",
                "authority": "Korea Fair Trade Commission",
                "url": "https://www.ftc.go.kr/eng/contents.do?key=557",
            },
            {
                "title": "Labeling and Advertising — Laws and Guidelines",
                "authority": "Korea Fair Trade Commission",
                "url": "https://www.ftc.go.kr/eng/selectBbsNttList.do?bordCd=847&key=577",
            },
        ],
    },
    "AE": {
        "market_name": "United Arab Emirates",
        "locale": "ar-AE",
        "copy_guidance": [
            "For Arabic, use natural Modern Standard Arabic with a concise value proposition and respectful tone.",
            "Do not mix Arabic and English fragments unless the reading order is explicitly controlled.",
        ],
        "visual_guidance": [
            "Use a right-to-left primary layout for Arabic while keeping Latin brand marks in their original form.",
            "Mirror text hierarchy and directional UI cues, but never mirror product images or logos.",
        ],
        "required_adaptations": [
            "Use Arabic locale conventions; insert AED prices only when verified values are supplied.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Check that product information and labels are clear and that the displayed price matches the verified offer.",
            "Remove misleading prices, false product data, and unsupported performance claims.",
            "Obtain market and sector review for regulated categories or promotions before publication.",
        ],
        "source_references": [
            {
                "title": "Consumer protection",
                "authority": "Official Platform of the UAE Government",
                "url": "https://u.ae/en/information-and-services/justice-safety-and-the-law/consumer-protection",
            },
        ],
    },
}


CROSS_MARKET_RULES = [
    "Create a separate static asset for each requested market; do not combine markets into one design.",
    "Preserve every AnchorBlock locked attribute, including product appearance, logo reference, and color palette.",
    "Do not invent prices, discounts, test results, certifications, endorsements, availability, guarantees, or health claims.",
    "Keep qualifiers and disclosures readable, close to the claim, and in the same language as the market copy.",
    "Treat every compliance item as a human publication-review prompt, not as automated legal clearance.",
]


def _text_direction(language: str) -> str:
    return "rtl" if language.split("-")[0].lower() in {"ar", "fa", "he", "ur"} else "ltr"


def _fallback_preset(market_code: str, language: str) -> dict:
    return {
        "market_name": market_code,
        "locale": f"{language}-{market_code}",
        "copy_guidance": [
            f"Use fluent {language} copy and preserve the meaning of the verified selling points.",
            "Use a concise value proposition and a clear call to action.",
        ],
        "visual_guidance": [
            "Use a layout that follows the requested language direction and leaves room for translated copy.",
            "Keep qualifications readable and adjacent to the relevant claim.",
        ],
        "required_adaptations": [
            "Apply local currency, units, or formats only when verified values are supplied.",
            "Keep brand names and every locked visual anchor unchanged.",
        ],
        "compliance_review": [
            "Obtain local review for claims, prices, promotions, disclosures, regulated categories, and platform rules before publication.",
        ],
        "source_references": [],
    }


def build_localization_plan(campaign: StructuredCampaignInput) -> LocalizationPlan:
    """Build deterministic per-market creative and publication-review briefs."""

    briefs: list[MarketLocalizationBrief] = []
    for target in campaign.target_markets:
        configured = MARKET_PRESETS.get(target.market_code)
        preset = deepcopy(configured or _fallback_preset(target.market_code, target.language))
        base_language = target.language.split("-")[0].lower()
        locale = preset["locale"]
        if locale.split("-")[0].lower() != base_language:
            locale = f"{target.language}-{target.market_code}"

        briefs.append(
            MarketLocalizationBrief(
                market_code=target.market_code,
                market_name=preset["market_name"],
                language=target.language,
                locale=locale,
                text_direction=_text_direction(target.language),
                preset_status="supported" if configured else "fallback",
                copy_guidance=preset["copy_guidance"],
                visual_guidance=preset["visual_guidance"],
                required_adaptations=preset["required_adaptations"],
                compliance_review=preset["compliance_review"],
                source_references=preset["source_references"],
            )
        )

    return LocalizationPlan(
        preset_version=PRESET_VERSION,
        reviewed_on=PRESET_REVIEWED_ON,
        markets=briefs,
        cross_market_rules=CROSS_MARKET_RULES,
        disclaimer=(
            "Publication-review prompts are informational guardrails, not legal advice or "
            "automated clearance. A qualified reviewer must verify the final asset, offer, "
            "product category, platform policy, and current market rules before publication."
        ),
    )
