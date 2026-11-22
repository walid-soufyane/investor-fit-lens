from investor_fit_lens import InvestorProfile, assess, load_sample_investments
from investor_fit_lens.presentation import (
    PLAIN_GOAL_LABELS,
    PLAIN_LIQUIDITY_LABELS,
    PLAIN_RISK_LABELS,
    RATING_HEADLINES,
    factor_icon,
    plain_reasons,
)
from investor_fit_lens.profile import GOAL_LABELS, LIQUIDITY_NEED_LABELS, RISK_TOLERANCE_LABELS
from investor_fit_lens.scoring import RATINGS

S = {s.id: s for s in load_sample_investments()}


def test_plain_labels_cover_every_option():
    assert set(PLAIN_RISK_LABELS) == set(RISK_TOLERANCE_LABELS)
    assert set(PLAIN_LIQUIDITY_LABELS) == set(LIQUIDITY_NEED_LABELS)
    assert set(PLAIN_GOAL_LABELS) == set(GOAL_LABELS)
    assert set(RATING_HEADLINES) == set(RATINGS)


def test_factor_icon_thresholds():
    assert [factor_icon(s) for s in (100, 80, 79, 40, 39, 0)] == ["✅", "✅", "⚠️", "⚠️", "❌", "❌"]


def test_plain_reasons_match_factor_scores_and_avoid_jargon():
    p = InvestorProfile(
        horizon_years=1, risk_tolerance=1, loss_capacity_pct=5, liquidity_need="high", goal="preservation"
    )
    for inv in S.values():
        a = assess(p, inv)
        reasons = plain_reasons(a)
        assert len(reasons) == 5
        assert [icon for icon, _ in reasons] == [factor_icon(f.score) for f in a.factors]
        for _, text in reasons:
            for jargon in ("stress decline", "allocation", "liquidity", "tolerance (", "weight"):
                assert jargon not in text.lower()


def test_plain_reasons_for_a_clear_mismatch():
    p = InvestorProfile(
        horizon_years=1,
        risk_tolerance=1,
        loss_capacity_pct=5,
        liquidity_need="high",
        goal="preservation",
        allocation_pct=50,
    )
    icons = [i for i, _ in plain_reasons(assess(p, S["crypto_asset"]))]
    assert icons.count("❌") >= 3
    text = " ".join(t for _, t in plain_reasons(assess(p, S["crypto_asset"])))
    assert "40.0% of your savings" in text and "keeping money safe" in text
