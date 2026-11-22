import json
from importlib import resources

import pytest

from investor_fit_lens import GOAL_LABELS, InvestorProfile, load_sample_investments, sample_data_notice
from investor_fit_lens.cli import main
from investor_fit_lens.investments import Investment


@pytest.mark.parametrize(
    "kw",
    [
        {"horizon_years": -1},
        {"risk_tolerance": 0},
        {"risk_tolerance": 6},
        {"loss_capacity_pct": 120},
        {"liquidity_need": "sometimes"},
        {"goal": "get rich"},
        {"allocation_pct": 0},
    ],
)
def test_invalid_profiles_rejected(kw):
    base = dict(horizon_years=5, risk_tolerance=3, loss_capacity_pct=10, liquidity_need="low", goal="growth")
    base.update(kw)
    with pytest.raises(ValueError):
        InvestorProfile(**base)


def test_sample_investments_load_and_are_labelled_illustrative():
    samples = load_sample_investments()
    assert len(samples) >= 10
    assert len({s.id for s in samples}) == len(samples)
    assert all(s.illustrative for s in samples)
    assert all(set(s.goal_fit) == set(GOAL_LABELS) for s in samples)
    notice = sample_data_notice().lower()
    assert "illustrative" in notice and "not live" in notice


def test_sample_file_is_generic():
    """Samples describe generic investment types: no 4-digit years that could imply the figures are current."""
    import re

    raw = resources.files("investor_fit_lens").joinpath("data/sample_investments.json").read_text("utf-8")
    assert not re.search(r"\b(19|20)\d{2}\b", raw)
    assert json.loads(raw)["notice"].startswith("ILLUSTRATIVE")


def test_invalid_investment_rejected():
    with pytest.raises(ValueError):
        Investment(
            id="x",
            name="x",
            category="x",
            description="",
            risk_level=7,
            stress_drawdown_pct=10,
            liquidity="high",
            min_horizon_years=1,
            goal_fit={"growth": 50},
        )


def test_cli_rank_and_detail(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Good fit" in out
    assert "not provide personalized financial" in out
    assert main(["demo", "--investment", "term_deposit_1y", "--liquidity", "high"]) == 0
    out = capsys.readouterr().out
    assert "[CRITICAL] Money may be locked" in out
    assert main(["demo", "--investment", "nope"]) == 2
