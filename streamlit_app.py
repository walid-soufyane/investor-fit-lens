"""Investor Fit Lens: Streamlit interface.

Run with:  streamlit run streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from investor_fit_lens import (
    DISCLAIMER,
    GOAL_LABELS,
    LIQUIDITY_NEED_LABELS,
    PROFILE_PRESETS,
    RISK_TOLERANCE_LABELS,
    Investment,
    InvestorProfile,
    assess,
    improvement_hints,
    load_sample_investments,
    rank,
    sample_data_notice,
)
from investor_fit_lens.presentation import RATING_MEANINGS, comparison_rows, factor_rows, rating_badge_html

CUSTOM_ID = "__custom__"

st.set_page_config(page_title="Investor Fit Lens", page_icon="🔎", layout="wide")


@st.cache_data
def _samples() -> list[Investment]:
    return load_sample_investments()


def _apply_preset() -> None:
    preset = PROFILE_PRESETS.get(st.session_state.get("preset", ""))
    if preset:
        st.session_state["horizon"] = float(preset["horizon_years"])
        st.session_state["risk"] = preset["risk_tolerance"]
        st.session_state["loss"] = int(preset["loss_capacity_pct"])
        st.session_state["liquidity"] = preset["liquidity_need"]
        st.session_state["goal"] = preset["goal"]
        st.session_state["allocation"] = int(preset["allocation_pct"])


PROFILE_DEFAULTS = {"horizon": 10.0, "risk": 3, "loss": 15, "liquidity": "low", "goal": "growth", "allocation": 10}


def profile_sidebar() -> InvestorProfile:
    # Widget values live in session state so presets can update them without conflicting defaults.
    for key, value in PROFILE_DEFAULTS.items():
        st.session_state.setdefault(key, value)
    st.sidebar.header("Your profile")
    st.sidebar.caption("Every result is relative to these answers. Change them to see how the fit moves.")
    st.sidebar.selectbox(
        "Start from an example profile (optional)",
        ["", *PROFILE_PRESETS],
        format_func=lambda v: v or "Custom (enter my own answers)",
        key="preset",
        on_change=_apply_preset,
        help="Example situations to explore quickly. They are illustrations, not recommendations.",
    )
    horizon = st.sidebar.slider(
        "Investment horizon (years)",
        0.0,
        40.0,
        step=0.5,
        key="horizon",
        help="How long this money can stay invested before you expect to need it.",
    )
    risk = st.sidebar.select_slider(
        "Risk tolerance",
        options=list(RISK_TOLERANCE_LABELS),
        format_func=lambda v: f"{v} - {RISK_TOLERANCE_LABELS[v].split(':')[0]}",
        key="risk",
        help="How comfortable you are with swings in value (willingness).",
    )
    st.sidebar.caption(RISK_TOLERANCE_LABELS[risk])
    loss = st.sidebar.slider(
        "Loss capacity (% of total portfolio)",
        0,
        60,
        key="loss",
        help="The largest one-year decline of your TOTAL portfolio you could absorb without changing your "
        "plans (ability, not willingness).",
    )
    liquidity = st.sidebar.radio(
        "Liquidity needs",
        options=list(LIQUIDITY_NEED_LABELS),
        format_func=lambda v: LIQUIDITY_NEED_LABELS[v],
        key="liquidity",
    )
    goal = st.sidebar.selectbox("Investment goal", options=list(GOAL_LABELS), format_func=GOAL_LABELS.get, key="goal")
    allocation = st.sidebar.slider(
        "Share of portfolio for this investment (%)",
        1,
        100,
        key="allocation",
        help="Used to translate the investment's potential decline into a portfolio-level loss.",
    )
    return InvestorProfile(
        horizon_years=horizon,
        risk_tolerance=risk,
        loss_capacity_pct=float(loss),
        liquidity_need=liquidity,
        goal=goal,
        allocation_pct=float(allocation),
    )


def custom_investment_form() -> Investment:
    st.caption("Describe the investment with your own assumptions. Nothing is looked up or verified.")
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name", "My investment", key="c_name")
    risk = c1.slider("Risk level (1 = very low, 5 = very high)", 1, 5, 3, key="c_risk")
    drawdown = c2.slider("Plausible severe decline (%)", 0, 100, 30, key="c_dd")
    liquidity = c2.selectbox("Liquidity", ["high", "medium", "low"], key="c_liq")
    horizon = c3.slider("Suggested minimum horizon (years)", 0, 20, 5, key="c_hz")
    complexity = c3.selectbox("Complexity", ["low", "medium", "high"], key="c_cx")
    diversified = c3.checkbox("Diversified (many holdings)", value=True, key="c_div")
    st.markdown("**How typically does this investment serve each goal?** (0 = not at all, 100 = a core use)")
    cols = st.columns(len(GOAL_LABELS))
    goal_fit = {
        g: float(col.slider(label, 0, 100, 50, 5, key=f"c_goal_{g}"))
        for col, (g, label) in zip(cols, GOAL_LABELS.items(), strict=True)
    }
    return Investment(
        id=CUSTOM_ID,
        name=name or "My investment",
        category="Custom",
        description="User-described investment.",
        risk_level=risk,
        stress_drawdown_pct=float(drawdown),
        liquidity=liquidity,
        min_horizon_years=float(horizon),
        goal_fit=goal_fit,
        complexity=complexity,
        diversified=diversified,
        illustrative=False,
    )


def show_assessment(profile: InvestorProfile, inv: Investment) -> None:
    a = assess(profile, inv)
    left, right = st.columns([2, 1])
    with left:
        st.markdown(rating_badge_html(a.rating), unsafe_allow_html=True)
        st.markdown(f"#### {inv.name}")
        st.write(a.summary())
        st.caption(RATING_MEANINGS[a.rating])
    with right:
        st.metric("Fit score", f"{a.score:.0f} / 100")
        st.caption(
            "An ordinal summary of rule-based judgements. Not a probability or a return forecast; "
            "differences of a few points are not meaningful."
        )

    st.subheader("How each factor contributed")
    for f in a.factors:
        c1, c2 = st.columns([1, 3])
        c1.markdown(f"**{f.label}**  \n{f.score:.0f}/100 · weight {f.weight:.0%}")
        c2.progress(int(round(f.score)) / 100, text=f.explanation)

    st.subheader("Risk flags")
    if not a.flags:
        st.success("No flags raised for this profile.")
    for fl in a.flags:
        text = f"**{fl.title}.** {fl.detail}"
        if fl.cap:
            text += f" *(Caps the rating at {fl.cap}.)*"
        {"critical": st.error, "warning": st.warning, "info": st.info}[fl.severity](text)

    st.subheader("What would change the picture")
    st.write(
        f"In an illustrative severe decline of {inv.stress_drawdown_pct:g}%, a {profile.allocation_pct:g}% "
        f"allocation would cost about **{a.portfolio_stress_loss_pct:.1f}%** of your total portfolio. "
        f"Keeping the allocation at or below **{a.max_allocation_within_loss_capacity_pct:.0f}%** would keep that "
        f"illustrative loss within the {profile.loss_capacity_pct:g}% you said you could absorb."
    )
    hints = improvement_hints(a)
    if hints:
        st.markdown("**What the rules respond to:**")
        st.markdown("\n".join(f"- {h}" for h in hints))
        st.caption("These explain the scoring, not advice to change your situation to suit a product.")
    with st.expander("Factor details as a table"):
        st.dataframe(pd.DataFrame(factor_rows(a)), hide_index=True, use_container_width=True)

    with st.expander("Investment characteristics used"):
        if inv.illustrative:
            st.caption("Illustrative sample: generic assumptions, not live or current data.")
        st.write(inv.description)
        st.json(
            {
                "category": inv.category,
                "risk_level (1-5)": inv.risk_level,
                "illustrative severe decline (%)": inv.stress_drawdown_pct,
                "liquidity": inv.liquidity,
                "suggested minimum horizon (years)": inv.min_horizon_years,
                "complexity": inv.complexity,
                "diversified": inv.diversified,
                "goal fit (0-100)": inv.goal_fit,
            }
        )


def main() -> None:
    st.title("🔎 Investor Fit Lens")
    st.markdown(
        "**Is this investment a good fit for *this* investor?** Enter a profile, pick an investment, and see a "
        "transparent, rule-based fit rating with the reasons behind it. No investment is treated as "
        "universally good or bad: the same product can fit one person and not another."
    )
    st.info(DISCLAIMER, icon="ℹ️")

    profile = profile_sidebar()
    samples = _samples()
    tab_assess, tab_compare, tab_method = st.tabs(["Assess an investment", "Compare all samples", "Methodology"])

    with tab_assess:
        options = [s.id for s in samples] + [CUSTOM_ID]
        names = {s.id: f"{s.name}  ·  illustrative sample" for s in samples} | {
            CUSTOM_ID: "Describe my own investment..."
        }
        choice = st.selectbox("Investment", options, index=5, format_func=names.get, key="investment")
        inv = custom_investment_form() if choice == CUSTOM_ID else next(s for s in samples if s.id == choice)
        st.divider()
        show_assessment(profile, inv)

    with tab_compare:
        st.caption(sample_data_notice())
        st.write("All sample investments assessed against the current profile, sorted by rating and score.")
        df = pd.DataFrame(comparison_rows(rank(profile, samples)))
        st.dataframe(df, hide_index=True, use_container_width=True)

    with tab_method:
        path = Path(__file__).parent / "docs" / "METHODOLOGY.md"
        st.markdown(path.read_text("utf-8") if path.exists() else "See docs/METHODOLOGY.md in the repository.")

    st.caption(sample_data_notice())


main()
