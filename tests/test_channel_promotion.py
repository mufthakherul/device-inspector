from __future__ import annotations

import pytest

from tools.channel_promotion import build_promotion_plan, classify_release_channel


@pytest.mark.parametrize(
    ("tag", "channel"),
    [
        ("v1.2.3-nightly.4", "nightly"),
        ("v1.2.3-alpha.1", "alpha"),
        ("v1.2.3-beta.2", "beta"),
        ("v1.2.3", "stable"),
    ],
)
def test_classify_release_channel(tag: str, channel: str):
    assert classify_release_channel(tag) == channel


def test_build_promotion_plan_beta_to_stable():
    plan = build_promotion_plan("v2.0.0-beta.1")
    assert plan.source_channel == "beta"
    assert plan.target_channel == "stable"


def test_classify_release_channel_invalid_tag_raises():
    with pytest.raises(ValueError):
        classify_release_channel("release-foo")
