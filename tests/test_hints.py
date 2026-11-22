from investor_fit_lens import InvestorProfile, assess, improvement_hints, load_sample_investments

SAMPLES = {s.id: s for s in load_sample_investments()}


def profile(**kw):
    base = dict(horizon_years=20, risk_tolerance=5, loss_capacity_pct=50, liquidity_need="low", goal="growth")
    base.update(kw)
    return InvestorProfile(**base)


def test_no_hints_for_clean_fit():
    assert improvement_hints(assess(profile(), SAMPLES["global_equity_index"])) == []


def test_each_mismatch_produces_a_hint():
    p = profile(
        horizon_years=2,
        risk_tolerance=2,
        loss_capacity_pct=5,
        liquidity_need="high",
        goal="preservation",
        allocation_pct=40,
    )
    hints = " ".join(improvement_hints(assess(p, SAMPLES["single_stock"])))
    assert "at least 10 years" in hints
    assert "risk tolerance of 5/5" in hints
    assert "7.1% or less" in hints  # 5 / 70 * 100
    assert "stated goal" in hints
    assert "10% of the portfolio" in hints


def test_hint_allocation_actually_clears_loss_factor():
    p = profile(loss_capacity_pct=10, allocation_pct=50)
    a = assess(p, SAMPLES["crypto_asset"])
    reduced = assess(
        profile(loss_capacity_pct=10, allocation_pct=a.max_allocation_within_loss_capacity_pct), SAMPLES["crypto_asset"]
    )
    assert next(f for f in reduced.factors if f.key == "loss").score == 100


def test_short_term_product_hint():
    hints = improvement_hints(assess(profile(), SAMPLES["leveraged_etf_3x"]))
    assert any("short holding periods" in h for h in hints)
