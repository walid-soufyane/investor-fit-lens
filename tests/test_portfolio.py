import pytest

from investor_fit_lens import Holding, InvestorProfile, assess_portfolio, load_sample_investments

S = {s.id: s for s in load_sample_investments()}


def profile(**kw):
    base = dict(horizon_years=15, risk_tolerance=3, loss_capacity_pct=20, liquidity_need="low", goal="balanced")
    base.update(kw)
    return InvestorProfile(**base)


def test_combined_loss_weighted_risk_and_cash_remainder():
    pa = assess_portfolio(
        profile(),
        [Holding(S["global_equity_index"], 30), Holding(S["short_gov_bond_fund"], 50)],
    )
    assert pa.total_allocation_pct == 80
    assert pa.combined_stress_loss_pct == pytest.approx(50 * 0.30 + 6 * 0.50)  # 18%
    assert pa.weighted_risk_level == pytest.approx((4 * 30 + 2 * 50 + 1 * 20) / 100)
    assert pa.flags == []
    assert "20% treated as cash" in pa.summary()
    assert sum(pa.rating_counts.values()) == 2


def test_each_holding_assessed_with_its_own_allocation():
    pa = assess_portfolio(profile(), [Holding(S["crypto_asset"], 5), Holding(S["single_stock"], 40)])
    allocs = [a.profile.allocation_pct for a in pa.holdings]
    assert allocs == [5, 40]


def test_portfolio_level_flags():
    pa = assess_portfolio(
        profile(loss_capacity_pct=10, liquidity_need="high", risk_tolerance=2),
        [Holding(S["single_stock"], 40), Holding(S["private_real_estate_fund"], 30), Holding(S["crypto_asset"], 30)],
    )
    titles = {f.title for f in pa.flags}
    assert {
        "Combined potential loss exceeds your capacity",
        "Portfolio riskier than your tolerance",
        "Locked money with high liquidity needs",
        "Concentrated single holding",
    } <= titles
    assert pa.flags[0].severity == "critical"
    assert "weak or poor individual fit" in pa.summary()


@pytest.mark.parametrize(
    "holdings",
    [
        [],
        [Holding(S["savings_account"], 60), Holding(S["savings_account"], 10)],
        [Holding(S["savings_account"], 0)],
        [Holding(S["savings_account"], 70), Holding(S["balanced_fund"], 40)],
    ],
)
def test_invalid_portfolios(holdings):
    with pytest.raises(ValueError):
        assess_portfolio(profile(), holdings)


def test_cli_portfolio(capsys):
    from investor_fit_lens.cli import main

    args = ["portfolio", "--horizon", "15", "--risk", "3", "--loss-capacity", "20", "--liquidity", "low"]
    assert main([*args, "--holding", "global_equity_index=30", "--holding", "short_gov_bond_fund=50"]) == 0
    out = capsys.readouterr().out
    assert "20% treated as cash" in out and "Global equity index fund" in out
    assert main([*args, "--holding", "nope=10"]) == 2
    assert main([*args, "--holding", "savings_account=abc"]) == 2
    assert main([*args, "--holding", "savings_account=80", "--holding", "balanced_fund=40"]) == 2
    assert main(["portfolio", "--risk", "9", "--holding", "savings_account=10"]) == 2
