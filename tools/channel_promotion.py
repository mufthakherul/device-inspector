"""Release channel promotion planning utilities.

Implements Sprint 8 promotion semantics from nightly -> beta -> stable.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class PromotionPlan:
    tag: str
    source_channel: str
    target_channel: str
    recommendation: str


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def classify_release_channel(tag: str) -> str:
    stable = re.compile(r"^v\d+\.\d+\.\d+$")
    beta = re.compile(r"^v\d+\.\d+\.\d+-beta\.\d+$")
    alpha = re.compile(r"^v\d+\.\d+\.\d+-alpha\.\d+$")
    nightly = re.compile(r"^v\d+\.\d+\.\d+-nightly\.\d+$")

    if nightly.match(tag):
        return "nightly"
    if alpha.match(tag):
        return "alpha"
    if beta.match(tag):
        return "beta"
    if stable.match(tag):
        return "stable"

    raise ValueError(f"Unsupported release tag format: {tag}")


def build_promotion_plan(tag: str) -> PromotionPlan:
    channel = classify_release_channel(tag)

    if channel == "nightly":
        target = "beta"
        recommendation = (
            "Promote nightly build to beta after smoke and policy gates pass."
        )
    elif channel == "alpha":
        target = "beta"
        recommendation = "Promote alpha tag to beta after integration matrix is green."
    elif channel == "beta":
        target = "stable"
        recommendation = (
            "Promote beta tag to stable after release checklist and sign-off."
        )
    else:
        target = "stable"
        recommendation = "Already stable; publish and monitor post-release health."

    return PromotionPlan(
        tag=tag,
        source_channel=channel,
        target_channel=target,
        recommendation=recommendation,
    )


def to_payload(plan: PromotionPlan) -> dict:
    return {
        "generated_at": _now_iso(),
        "plan_version": "1.0.0",
        "tag": plan.tag,
        "source_channel": plan.source_channel,
        "target_channel": plan.target_channel,
        "recommendation": plan.recommendation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate channel promotion plan")
    parser.add_argument("--tag", required=True)
    parser.add_argument(
        "--output", default="docs-site/data/channel-promotion-plan.json"
    )
    args = parser.parse_args()

    plan = build_promotion_plan(args.tag)
    payload = to_payload(plan)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("[channel-promotion] plan generated")
    print(f"  tag: {plan.tag}")
    print(f"  source: {plan.source_channel}")
    print(f"  target: {plan.target_channel}")
    print(f"  output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
