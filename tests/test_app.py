"""End-to-end tests of the Streamlit UI using Streamlit's built-in AppTest harness.

Skipped automatically when Streamlit is not installed (the scoring engine has no
Streamlit dependency and is covered by the other test files).
"""

from pathlib import Path

import pytest

from investor_fit_lens import InvestorProfile, assess, load_sample_investments, rank
from investor_fit_lens.presentation import comparison_rows, factor_rows, rating_badge_html

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def test_presentation_helpers():
    p = InvestorProfile(horizon_years=10, risk_tolerance=3, loss_capacity_pct=15, liquidity_need="low", goal="growth")
    samples = load_sample_investments()
    rows = factor_rows(assess(p, samples[0]))
    assert [r["Factor"] for r in rows] == [
        "Time horizon",
        "Risk tolerance",
        "Loss capacity",
        "Liquidity needs",
        "Goal alignment",
    ]
    table = comparison_rows(rank(p, samples))
    assert len(table) == len(samples) and {"Rating", "Fit score", "Critical flags"} <= set(table[0])
    assert "Good fit" in rating_badge_html("Good fit")


@pytest.fixture
def app():
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def _all_text(at) -> str:
    parts = [m.value for m in at.markdown] + [e.value for e in at.error] + [w.value for w in at.warning]
    parts += [i.value for i in at.info] + [s.value for s in at.success]
    return "\n".join(str(p) for p in parts)


def test_app_renders_default_assessment(app):
    text = _all_text(app)
    assert "Investor Fit Lens" in [t.value for t in app.title][0]
    assert "not provide personalized financial" in text
    assert any(lbl in text for lbl in ("Good fit", "Partial fit", "Weak fit", "Poor fit"))
    assert app.metric[0].label == "Fit score"


def test_changing_profile_changes_result(app):
    app.selectbox(key="investment").select("term_deposit_1y").run()
    app.radio(key="liquidity").set_value("high").run()
    assert not app.exception
    text = _all_text(app)
    assert "Poor fit" in text
    assert "Money may be locked when you need it" in text


def test_custom_investment_form(app):
    app.selectbox(key="investment").select("__custom__").run()
    app.text_input(key="c_name").input("Test product").run()
    app.slider(key="c_risk").set_value(5).run()
    assert not app.exception
    assert "Test product" in _all_text(app)


def test_preset_fills_profile(app):
    app.selectbox(key="preset").select("Cautious saver, short horizon").run()
    assert not app.exception
    assert app.radio(key="liquidity").value == "high"
    assert app.selectbox(key="goal").value == "preservation"
    assert app.slider(key="horizon").value == 2.0
