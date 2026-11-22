import dataclasses

import pytest

from investor_fit_lens import WEIGHTS, InvestorProfile, assess, load_sample_investments, rank, rating_for_score
from investor_fit_lens.investments import Investment
from investor_fit_lens.scoring import (
    max_allocation_within_capacity,
    portfolio_stress_loss,
    score_goal,
    score_horizon,
    score_liquidity,
    score_loss,
    score_risk,
)


def make_profile(**kw):
    base = dict(
        horizon_years=10,
        risk_tolerance=3,
        loss_capacity_pct=20,
        liquidity_need="low",
        goal="balanced",
        allocation_pct=20,
    )
    base.update(kw)
    return InvestorProfile(**base)


def make_investment(**kw):
    base = dict(
        id="test",
        name="Test fund",
        category="Test",
        description="",
        risk_level=3,
        stress_drawdown_pct=30,
        liquidity="high",
        min_horizon_years=5,
        goal_fit={"preservation": 30, "income": 50, "balanced": 90, "growth": 70, "speculation": 10},
    )
    base.update(kw)
    return Investment(**base)


def titles(assessment):
    return {f.title for f in assessment.flags}


# ---------------------------------------------------------------- factor rules


def test_horizon_rule():
    inv = make_investment(min_horizon_years=8)
    assert score_horizon(make_profile(horizon_years=8), inv)[0] == 100
    score, _, flags = score_horizon(make_profile(horizon_years=6), inv)
    assert score == 75 and flags[0].severity == "warning"
    score, _, flags = score_horizon(make_profile(horizon_years=2), inv)
    assert score == 25 and flags[0].severity == "critical" and flags[0].cap == "Weak fit"
    assert score_horizon(make_profile(horizon_years=0), make_investment(min_horizon_years=0))[0] == 100


def test_horizon_too_long_for_short_term_product():
    inv = make_investment(min_horizon_years=0, max_suggested_holding_years=0.1)
    score, _, flags = score_horizon(make_profile(horizon_years=5), inv)
    assert score == 30 and flags[0].cap == "Weak fit"


@pytest.mark.parametrize(
    ("tolerance", "expected", "cap"), [(5, 100, None), (3, 100, None), (2, 60, "Partial fit"), (1, 25, "Partial fit")]
)
def test_risk_rule_steps(tolerance, expected, cap):
    score, _, flags = score_risk(make_profile(risk_tolerance=tolerance), make_investment(risk_level=3))
    assert score == expected
    assert (flags[0].cap if flags else None) == cap


def test_risk_gap_three_is_critical():
    score, _, flags = score_risk(make_profile(risk_tolerance=1), make_investment(risk_level=4))
    assert score == 0 and flags[0].severity == "critical" and flags[0].cap == "Poor fit"


def test_loss_capacity_math():
    profile = make_profile(loss_capacity_pct=10, allocation_pct=20)
    inv = make_investment(stress_drawdown_pct=40)
    assert portfolio_stress_loss(profile, inv) == pytest.approx(8.0)
    assert score_loss(profile, inv)[0] == 100
    over = make_profile(loss_capacity_pct=10, allocation_pct=30)  # 12% loss -> ratio 1.2 -> 80
    score, _, flags = score_loss(over, inv)
    assert score == pytest.approx(80) and flags[0].severity == "warning"
    assert max_allocation_within_capacity(over, inv) == pytest.approx(25.0)
    way_over = make_profile(loss_capacity_pct=5, allocation_pct=50)  # 20% loss -> ratio 4
    score, _, flags = score_loss(way_over, inv)
    assert score == 0 and flags[0].cap == "Weak fit"


def test_loss_with_zero_capacity_and_zero_drawdown():
    assert score_loss(make_profile(loss_capacity_pct=0), make_investment(stress_drawdown_pct=0))[0] == 100
    score, _, flags = score_loss(make_profile(loss_capacity_pct=0), make_investment(stress_drawdown_pct=10))
    assert score == 0 and flags[0].severity == "critical"
    assert max_allocation_within_capacity(make_profile(), make_investment(stress_drawdown_pct=0)) == 100


def test_liquidity_matrix_and_lockup_flag():
    locked = make_investment(liquidity="low")
    score, _, flags = score_liquidity(make_profile(liquidity_need="high"), locked)
    assert score == 0 and flags[0].cap == "Poor fit"
    assert score_liquidity(make_profile(liquidity_need="low"), locked)[0] == 90
    assert score_liquidity(make_profile(liquidity_need="high"), make_investment(liquidity="high"))[0] == 100


def test_goal_rule_and_mismatch_cap():
    inv = make_investment()
    assert score_goal(make_profile(goal="balanced"), inv)[0] == 90
    score, _, flags = score_goal(make_profile(goal="speculation"), inv)
    assert score == 10 and flags[0].cap == "Partial fit"


# ---------------------------------------------------------------- composite


def test_score_is_weighted_average_of_factors():
    a = assess(make_profile(), make_investment())
    assert sum(f.weight for f in a.factors) == pytest.approx(1.0)
    assert a.score == pytest.approx(sum(f.score * f.weight for f in a.factors), abs=0.05)
    assert {f.key: f.weight for f in a.factors} == pytest.approx(WEIGHTS)


def test_perfect_match_is_good_fit_without_flags():
    a = assess(make_profile(), make_investment())
    assert a.score == pytest.approx(97.5)
    assert a.rating == "Good fit" and not a.is_capped
    assert [f for f in a.flags if f.severity != "info"] == []


@pytest.mark.parametrize(
    ("score", "rating"),
    [
        (100, "Good fit"),
        (75, "Good fit"),
        (74.9, "Partial fit"),
        (55, "Partial fit"),
        (35, "Weak fit"),
        (34.9, "Poor fit"),
        (0, "Poor fit"),
    ],
)
def test_rating_bands(score, rating):
    assert rating_for_score(score) == rating


def test_critical_flag_caps_high_score():
    # Everything fits except money may be needed within a year and the product is locked.
    profile = make_profile(liquidity_need="high", horizon_years=10)
    a = assess(profile, make_investment(liquidity="low"))
    assert a.score >= 75
    assert a.score_rating == "Good fit" and a.rating == "Poor fit" and a.is_capped
    assert "caps the rating" in a.summary()


def test_concentration_flag_and_cap():
    inv = make_investment(diversified=False, stress_drawdown_pct=10)
    assert "Concentration" not in titles(assess(make_profile(allocation_pct=10), inv))
    moderate = assess(make_profile(allocation_pct=20), inv)
    assert "Concentration" in titles(moderate) and moderate.rating == "Good fit"
    heavy = assess(make_profile(allocation_pct=40, loss_capacity_pct=50), inv)
    assert heavy.rating == "Partial fit"


def test_complexity_and_notes_become_flags():
    inv = make_investment(complexity="high", notes=("Note A",))
    a = assess(make_profile(), inv)
    assert "Complex product" in titles(a)
    assert any(f.severity == "info" and f.detail == "Note A" for f in a.flags)
    assert [f.severity for f in a.flags] == sorted(
        [f.severity for f in a.flags], key=["critical", "warning", "info"].index
    )


def test_lower_allocation_never_reduces_fit():
    inv = make_investment(risk_level=5, stress_drawdown_pct=80)
    profile = make_profile(risk_tolerance=5, loss_capacity_pct=10, goal="growth")
    scores = [assess(dataclasses.replace(profile, allocation_pct=x), inv).score for x in (50, 25, 10, 5)]
    assert scores == sorted(scores)


def test_custom_weights_validated_and_normalized():
    weights = {k: 1 for k in WEIGHTS}
    a = assess(make_profile(), make_investment(), weights=weights)
    assert all(f.weight == pytest.approx(0.2) for f in a.factors)
    with pytest.raises(ValueError):
        assess(make_profile(), make_investment(), weights={"risk": 1})
    with pytest.raises(ValueError):
        assess(make_profile(), make_investment(), weights={k: 0 for k in WEIGHTS})


# ---------------------------------------------------------------- scenarios on sample data


@pytest.fixture(scope="module")
def samples():
    return {s.id: s for s in load_sample_investments()}


def test_conservative_short_horizon_investor(samples):
    p = make_profile(horizon_years=2, risk_tolerance=1, loss_capacity_pct=5, liquidity_need="high", goal="preservation")
    assert assess(p, samples["savings_account"]).rating == "Good fit"
    assert assess(p, samples["term_deposit_1y"]).rating == "Poor fit"  # locked, money may be needed
    assert assess(p, samples["crypto_asset"]).rating == "Poor fit"
    assert assess(p, samples["global_equity_index"]).rating == "Poor fit"


def test_long_horizon_growth_investor(samples):
    p = make_profile(
        horizon_years=25, risk_tolerance=4, loss_capacity_pct=25, liquidity_need="low", goal="growth", allocation_pct=30
    )
    assert assess(p, samples["global_equity_index"]).rating == "Good fit"
    assert assess(p, samples["savings_account"]).rating == "Partial fit"  # safe, but off-goal
    assert assess(p, samples["crypto_asset"]).rating in {"Partial fit", "Weak fit", "Poor fit"}
    assert assess(p, samples["leveraged_etf_3x"]).rating in {"Weak fit", "Poor fit"}


def test_rank_orders_by_rating_then_score(samples):
    p = make_profile()
    ranked = rank(p, list(samples.values()))
    keys = [(["Poor fit", "Weak fit", "Partial fit", "Good fit"].index(a.rating), a.score) for a in ranked]
    assert keys == sorted(keys, reverse=True)
    assert len(ranked) == len(samples)


def test_markdown_report_contents(samples):
    from investor_fit_lens.presentation import assessment_markdown

    p = make_profile(liquidity_need="high", horizon_years=1)
    md = assessment_markdown(assess(p, samples["private_real_estate_fund"]))
    assert md.startswith("# Investor Fit Lens report: Private real estate fund")
    assert "**Rating:** Poor fit" in md
    assert "| Liquidity needs | 0 |" in md
    assert "CRITICAL: Money may be locked" in md
    assert "illustrative sample" in md and "not provide personalized financial" in md


def test_rank_passes_custom_weights(samples):
    goal_only = {k: (1.0 if k == "goal" else 0.0) for k in WEIGHTS}
    ranked = rank(make_profile(goal="speculation"), list(samples.values()), weights=goal_only)
    assert ranked[0].score == max(s.goal_fit["speculation"] for s in samples.values())


def test_side_by_side_rows(samples):
    from investor_fit_lens.presentation import side_by_side_rows

    p = make_profile()
    a, b = assess(p, samples["savings_account"]), assess(p, samples["balanced_fund"])
    rows = side_by_side_rows(a, b)
    assert [r[""] for r in rows][:3] == ["Rating", "Fit score", "Time horizon"]
    assert len(rows) == 2 + 5 + 1
    assert rows[1]["Difference"] == f"{b.score - a.score:+.0f}"
    with pytest.raises(ValueError):
        side_by_side_rows(a, assess(make_profile(goal="growth"), samples["balanced_fund"]))
