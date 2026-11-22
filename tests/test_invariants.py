"""Invariants the scoring rules must respect for every sample investment.

A more favourable profile (longer horizon within a product's design, higher risk
tolerance, more loss capacity, smaller allocation, lower liquidity need) must never
produce a lower score or a worse rating.
"""

import dataclasses
import itertools

import pytest

from investor_fit_lens import InvestorProfile, assess, load_sample_investments
from investor_fit_lens.scoring import RATINGS

SAMPLES = load_sample_investments()
BASE = InvestorProfile(
    horizon_years=5, risk_tolerance=3, loss_capacity_pct=15, liquidity_need="medium", goal="balanced", allocation_pct=20
)


def _rank(a):
    return RATINGS.index(a.rating)


def _assert_non_decreasing(inv, field, values):
    results = [assess(dataclasses.replace(BASE, **{field: v}), inv) for v in values]
    scores = [r.score for r in results]
    ranks = [_rank(r) for r in results]
    assert scores == sorted(scores), (inv.id, field, scores)
    assert ranks == sorted(ranks), (inv.id, field, [r.rating for r in results])


@pytest.mark.parametrize("inv", [s for s in SAMPLES if s.max_suggested_holding_years is None], ids=lambda s: s.id)
def test_longer_horizon_never_hurts(inv):
    _assert_non_decreasing(inv, "horizon_years", [0, 0.5, 1, 2, 3, 5, 7, 10, 20, 40])


@pytest.mark.parametrize("inv", SAMPLES, ids=lambda s: s.id)
def test_higher_risk_tolerance_never_hurts(inv):
    _assert_non_decreasing(inv, "risk_tolerance", [1, 2, 3, 4, 5])


@pytest.mark.parametrize("inv", SAMPLES, ids=lambda s: s.id)
def test_more_loss_capacity_never_hurts(inv):
    _assert_non_decreasing(inv, "loss_capacity_pct", [0, 1, 5, 10, 20, 40, 60, 100])


@pytest.mark.parametrize("inv", SAMPLES, ids=lambda s: s.id)
def test_smaller_allocation_never_hurts(inv):
    _assert_non_decreasing(inv, "allocation_pct", [100, 60, 40, 25, 15, 10, 5, 1])


@pytest.mark.parametrize("inv", SAMPLES, ids=lambda s: s.id)
def test_lower_liquidity_need_never_hurts(inv):
    _assert_non_decreasing(inv, "liquidity_need", ["high", "medium", "low"])


def test_scores_bounded_and_rating_never_better_than_score_band():
    grid = itertools.product([0, 3, 15], [1, 3, 5], [0, 10, 50], ["high", "low"], ["preservation", "growth"], [5, 50])
    for (h, r, lc, liq, goal, alloc), inv in itertools.product(grid, SAMPLES):
        a = assess(InvestorProfile(h, r, lc, liq, goal, alloc), inv)
        assert 0 <= a.score <= 100
        assert _rank(a) <= RATINGS.index(a.score_rating)
