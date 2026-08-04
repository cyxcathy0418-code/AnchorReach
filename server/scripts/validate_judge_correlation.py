"""Calculate reproducible human-vs-model judge correlations from separate CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.services.judge_validation import DimensionScores, validate_judge_correlation


REQUIRED_COLUMNS = {"sample_id", "product_appearance", "logo_reference", "color_palette"}


def load_scores(path: Path) -> dict[str, DimensionScores]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        scores: dict[str, DimensionScores] = {}
        for row_number, row in enumerate(reader, start=2):
            sample_id = (row.get("sample_id") or "").strip()
            if not sample_id:
                raise ValueError(f"{path}:{row_number} has no sample_id")
            if sample_id in scores:
                raise ValueError(f"{path}:{row_number} duplicates sample_id '{sample_id}'")
            logo_value = (row.get("logo_reference") or "").strip()
            scores[sample_id] = DimensionScores(
                product_appearance=float(row["product_appearance"]),
                logo_reference=float(logo_value) if logo_value else None,
                color_palette=float(row["color_palette"]),
            )
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-samples", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    result = validate_judge_correlation(
        load_scores(args.human),
        load_scores(args.model),
        threshold=args.threshold,
        minimum_samples=args.minimum_samples,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
