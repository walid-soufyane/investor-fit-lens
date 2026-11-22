"""Investor Fit Lens: Streamlit interface.

Run with:  streamlit run streamlit_app.py

The page is organised for people with no finance background: six plain
questions, one investment, and a verdict explained in everyday words. The
technical breakdown (scores, weights, assumptions) is one click away.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from investor_fit_lens import (
    DISCLAIMER,
    GOAL_LABELS,
    PROFILE_PRESETS,
    WEIGHTS,
    Holding,
    Investment,
    InvestorProfile,
    assess,
    assess_portfolio,
    improvement_hints,
    load_sample_investments,
    rank,
    sample_data_notice,
)
from investor_fit_lens.presentation import (
    PLAIN_GOAL_LABELS,
    PLAIN_LIQUIDITY_LABELS,
    PLAIN_RISK_LABELS,
    RATING_COLORS,
    RATING_HEADLINES,
    assessment_markdown,
    comparison_rows,
    factor_rows,
    plain_reasons,
    side_by_side_rows,
)
from investor_fit_lens.scoring import FACTOR_LABELS

CUSTOM_ID = "__custom__"
PROFILE_DEFAULTS = {"horizon": 10.0, "risk": 3, "loss": 15, "liquidity": "low", "goal": "growth", "allocation": 10}

st.set_page_config(page_title="Investor Fit Lens", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
      .block-container {max-width: 1100px; padding-top: 2rem;}
      .ifl-sub {font-size: 1.15rem; opacity: 0.85; margin-top: -0.6rem;}
      .ifl-step {border-radius: 12px; padding: 0.8rem 1rem; background: rgba(9,105,218,0.07); height: 100%;}
      .ifl-step b {font-size: 1.05rem;}
      .ifl-verdict {border-radius: 14px; padding: 1.2rem 1.4rem; margin: 0.4rem 0 1rem 0;
                    border-left: 10px solid var(--c); background: color-mix(in srgb, var(--c) 9%, transparent);}
      .ifl-verdict .big {font-size: 1.9rem; font-weight: 700; line-height: 1.2;}
      .ifl-verdict .sub {font-size: 1.1rem; margin-top: 0.3rem;}
      .ifl-reason {font-size: 1.05rem; margin: 0.35rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


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


# --------------------------------------------------------------------------
# Header and step 1: the investor's situation
# --------------------------------------------------------------------------


def header() -> None:
    st.title("🔎 Investor Fit Lens")
    st.markdown(
        '<p class="ifl-sub">Find out whether an investment suits <b>your</b> situation, '
        "explained in plain language.</p>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    steps = [
        ("1️⃣ Answer 6 quick questions", "about when you need the money and how much risk you can take."),
        ("2️⃣ Pick an investment", "from the examples, or describe one you're considering."),
        ("3️⃣ See if it fits, and why", "with each reason explained in everyday words."),
    ]
    for col, (title, text) in zip((c1, c2, c3), steps, strict=True):
        col.markdown(f'<div class="ifl-step"><b>{title}</b><br>{text}</div>', unsafe_allow_html=True)
    st.write("")
    with st.expander("ℹ️ For learning only: this is not financial advice. What this tool can and can't do"):
        st.markdown(DISCLAIMER)
        st.markdown(
            "The same investment can suit one person and not another, so this tool never calls an investment "
            "*good* or *bad* in general. It compares the investment's typical characteristics with your answers. "
            "The example investments use simplified, illustrative numbers, not live market data."
        )


def profile_questions() -> InvestorProfile:
    # Widget values live in session state so the example profiles can fill them in.
    for key, value in PROFILE_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    with st.container(border=True):
        st.subheader("1️⃣ About you")
        st.selectbox(
            "Want a shortcut? Start from an example person (optional)",
            ["", *PROFILE_PRESETS],
            format_func=lambda v: v or "No thanks, I'll answer myself",
            key="preset",
            on_change=_apply_preset,
        )
        left, right = st.columns(2, gap="large")
        with left:
            horizon = st.slider(
                "⏳ When will you need this money?",
                0.0,
                40.0,
                step=0.5,
                format="in %.1f years",
                key="horizon",
                help="How long the money can stay invested before you need to spend it.",
            )
            risk = st.radio(
                "🎢 If this investment dropped 20% in a few months, how would you feel?",
                options=list(PLAIN_RISK_LABELS),
                format_func=PLAIN_RISK_LABELS.get,
                key="risk",
            )
            liquidity = st.radio(
                "🚪 Could you suddenly need this money?",
                options=list(PLAIN_LIQUIDITY_LABELS),
                format_func=PLAIN_LIQUIDITY_LABELS.get,
                key="liquidity",
            )
        with right:
            goal = st.radio(
                "🎯 What do you want this money to do?",
                options=list(PLAIN_GOAL_LABELS),
                format_func=PLAIN_GOAL_LABELS.get,
                key="goal",
            )
            loss = st.slider(
                "🧯 In a very bad year, how much of your *total savings* could you lose without changing your plans?",
                0,
                60,
                format="%d%%",
                key="loss",
                help="Think about your ability to absorb a loss (job security, other savings), not just your feelings.",
            )
            allocation = st.slider(
                "🥧 How much of your savings would go into this investment?",
                1,
                100,
                format="%d%%",
                key="allocation",
            )
    return InvestorProfile(
        horizon_years=horizon,
        risk_tolerance=risk,
        loss_capacity_pct=float(loss),
        liquidity_need=liquidity,
        goal=goal,
        allocation_pct=float(allocation),
    )


def weights_sidebar() -> dict[str, float]:
    st.sidebar.header("⚙️ Advanced settings")
    with st.sidebar.expander("Factor weights"):
        st.caption(
            "How much each check counts in the score. These defaults are for teaching, not calibrated values. "
            "Weights are normalized to sum to 100%."
        )
        raw = {k: st.slider(FACTOR_LABELS[k], 0, 50, int(round(w * 100)), 5, key=f"w_{k}") for k, w in WEIGHTS.items()}
    if sum(raw.values()) == 0:
        st.sidebar.warning("All weights are zero; using the defaults.")
        return dict(WEIGHTS)
    return {k: float(v) for k, v in raw.items()}


# --------------------------------------------------------------------------
# Steps 2 and 3: pick an investment, see the result
# --------------------------------------------------------------------------


def custom_investment_form() -> Investment:
    st.caption("Describe the investment with your own best guesses. Nothing is looked up or checked.")
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name", "My investment", key="c_name")
    risk = c1.slider("How risky is it? (1 = very safe, 5 = very risky)", 1, 5, 3, key="c_risk")
    drawdown = c2.slider("How much could it drop in a severe crash? (%)", 0, 100, 30, key="c_dd")
    liquidity = c2.selectbox(
        "How easy is it to sell?",
        ["high", "medium", "low"],
        format_func={"high": "Easy, any day", "medium": "Takes some time or a fee", "low": "Locked for a period"}.get,
        key="c_liq",
    )
    horizon = c3.slider("How many years should you keep it, at least?", 0, 20, 5, key="c_hz")
    complexity = c3.selectbox(
        "How complicated is it?",
        ["low", "medium", "high"],
        format_func={"low": "Simple", "medium": "Somewhat", "high": "Complex"}.get,
        key="c_cx",
    )
    diversified = c3.checkbox("Spread across many holdings (diversified)", value=True, key="c_div")
    st.markdown("**How often is this kind of investment used for each goal?** (0 = never, 100 = it's what it's for)")
    cols = st.columns(len(GOAL_LABELS))
    goal_fit = {
        g: float(col.slider(PLAIN_GOAL_LABELS[g], 0, 100, 50, 5, key=f"c_goal_{g}"))
        for col, g in zip(cols, GOAL_LABELS, strict=True)
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


def show_result(profile: InvestorProfile, inv: Investment, weights: dict[str, float]) -> None:
    a = assess(profile, inv, weights=weights)
    icon, headline = RATING_HEADLINES[a.rating]
    color = RATING_COLORS[a.rating]
    st.subheader("3️⃣ Your result")
    st.markdown(
        f'<div class="ifl-verdict" style="--c:{color}" role="status" aria-label="Result: {a.rating}">'
        f'<div class="big">{icon} {a.rating}</div>'
        f'<div class="sub">{headline}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Why?")
    for reason_icon, text in plain_reasons(a):
        st.markdown(f'<div class="ifl-reason">{reason_icon} {text}</div>', unsafe_allow_html=True)

    important = [f for f in a.flags if f.severity in ("critical", "warning")]
    if important:
        st.markdown("#### ⚠️ Things to watch out for")
        for fl in important:
            (st.error if fl.severity == "critical" else st.warning)(f"**{fl.title}.** {fl.detail}")

    hints = improvement_hints(a)
    if hints:
        st.markdown("#### 💡 What would make it a better fit")
        st.markdown("\n".join(f"- {h}" for h in hints))
        st.caption("This explains how the result works. It is not advice to change your situation to suit a product.")

    notes = [f for f in a.flags if f.severity == "info"]
    if notes:
        with st.expander("📘 Good to know about this type of investment"):
            for fl in notes:
                st.info(fl.detail)

    st.download_button(
        "📄 Download this result",
        data=assessment_markdown(a),
        file_name=f"fit-report-{inv.id.strip('_')}.md",
        mime="text/markdown",
        key="download_report",
    )

    with st.expander("🔬 See the full breakdown (score, weights, assumptions)"):
        c1, c2 = st.columns([1, 2])
        c1.metric("Fit score", f"{a.score:.0f} / 100")
        c2.caption(
            "The score combines the five checks above. It is not a probability or a prediction of returns. "
            "One serious problem can lower the rating even when the score is high, which is why the rating, "
            "not the score, is shown first."
        )
        st.write(a.summary())
        for f in a.factors:
            fc1, fc2 = st.columns([1, 3])
            fc1.markdown(f"**{f.label}**  \n{f.score:.0f}/100 · counts {f.weight:.0%}")
            fc2.progress(int(round(f.score)) / 100, text=f.explanation)
        st.dataframe(pd.DataFrame(factor_rows(a)), hide_index=True, use_container_width=True)
        if inv.illustrative:
            st.caption("Example investment: simplified, illustrative assumptions, not live or current data.")
        st.json(
            {
                "category": inv.category,
                "risk level (1-5)": inv.risk_level,
                "illustrative severe decline (%)": inv.stress_drawdown_pct,
                "ease of selling": inv.liquidity,
                "suggested minimum years": inv.min_horizon_years,
                "complexity": inv.complexity,
                "diversified": inv.diversified,
                "typical use for each goal (0-100)": inv.goal_fit,
            }
        )


def check_one_tab(profile: InvestorProfile, samples: list[Investment], weights: dict[str, float]) -> None:
    with st.container(border=True):
        st.subheader("2️⃣ Pick an investment")
        options = [s.id for s in samples] + [CUSTOM_ID]
        names = {s.id: s.name for s in samples} | {CUSTOM_ID: "✏️ Describe my own investment..."}
        choice = st.selectbox(
            "Which investment do you want to check?", options, index=5, format_func=names.get, key="investment"
        )
        if choice == CUSTOM_ID:
            inv = custom_investment_form()
        else:
            inv = next(s for s in samples if s.id == choice)
            st.caption(f"**{inv.category}.** {inv.description}  \n*Example investment with illustrative numbers.*")
    show_result(profile, inv, weights)


# --------------------------------------------------------------------------
# Other tabs
# --------------------------------------------------------------------------


def compare_two_tab(profile: InvestorProfile, samples: list[Investment], weights: dict[str, float]) -> None:
    st.write("Put two investments next to each other to see which suits your answers better, and why.")
    by_id = {s.id: s for s in samples}
    c1, c2 = st.columns(2)
    first = c1.selectbox("First investment", list(by_id), index=0, format_func=lambda i: by_id[i].name, key="pair_a")
    second = c2.selectbox("Second investment", list(by_id), index=4, format_func=lambda i: by_id[i].name, key="pair_b")
    if first == second:
        st.info("Pick two different investments to compare.")
        return
    a, b = assess(profile, by_id[first], weights=weights), assess(profile, by_id[second], weights=weights)
    for col, x in ((c1, a), (c2, b)):
        icon, headline = RATING_HEADLINES[x.rating]
        col.markdown(
            f'<div class="ifl-verdict" style="--c:{RATING_COLORS[x.rating]}"><div class="big">{icon} {x.rating}</div>'
            f'<div class="sub">{headline}</div></div>',
            unsafe_allow_html=True,
        )
        for reason_icon, text in plain_reasons(x):
            col.markdown(f"{reason_icon} {text}")
    with st.expander("🔬 Score-by-score comparison"):
        st.dataframe(pd.DataFrame(side_by_side_rows(a, b)), hide_index=True, use_container_width=True)
        st.caption("Difference = second minus first. Small score differences are not meaningful.")


def portfolio_tab(profile: InvestorProfile, samples: list[Investment]) -> None:
    st.write(
        "Already own several investments, or planning to? Check them **together**: what you could lose if they all "
        "dropped at once, and whether the mix matches your answers. (The 'how much of your savings' question above "
        "isn't used here; you set each amount below.)"
    )
    by_id = {s.id: s for s in samples}
    chosen = st.multiselect(
        "Your investments",
        list(by_id),
        default=["global_equity_index", "ig_corporate_bond_fund", "savings_account"],
        format_func=lambda i: by_id[i].name,
        key="port_holdings",
    )
    if not chosen:
        st.info("Select at least one investment.")
        return
    st.markdown("**What share of your savings is in each one?**")
    cols = st.columns(min(len(chosen), 4))
    default = round(100 / len(chosen), 1) if len(chosen) > 1 else 100.0
    holdings = []
    for n, ident in enumerate(chosen):
        pct = cols[n % len(cols)].number_input(
            f"{by_id[ident].name} (%)", 0.0, 100.0, float(default), 1.0, key=f"port_{ident}"
        )
        if pct > 0:
            holdings.append(Holding(by_id[ident], pct))
    if not holdings:
        st.info("Give at least one investment a share above 0%.")
        return
    total = sum(h.allocation_pct for h in holdings)
    if total > 100:
        st.error(f"These add up to {total:g}%. Please reduce them to 100% or less.")
        return
    pa = assess_portfolio(profile, holdings)
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Combined stress loss", f"{pa.combined_stress_loss_pct:.1f}%", help="If everything fell at the same time."
    )
    m2.metric("Loss you said you can afford", f"{profile.loss_capacity_pct:g}%")
    m3.metric(
        "Weighted risk level",
        f"{pa.weighted_risk_level:.1f} / 5",
        help=f"Your comfort level: {profile.risk_tolerance}/5",
    )
    if not pa.flags:
        st.success("✅ No problems found with the mix as a whole.")
    for fl in pa.flags:
        (st.error if fl.severity == "critical" else st.warning)(f"**{fl.title}.** {fl.detail}")
    st.markdown("**Each investment on its own:**")
    for a in pa.holdings:
        icon, _ = RATING_HEADLINES[a.rating]
        st.markdown(f"{icon} **{a.investment.name}** ({a.profile.allocation_pct:g}%): {a.rating}")
    st.caption(
        "The combined loss assumes every investment suffers its illustrative severe drop at the same time: a "
        "cautious simplification, not a forecast. Any amount not assigned is treated as cash."
    )


def rank_all_tab(profile: InvestorProfile, samples: list[Investment], weights: dict[str, float]) -> None:
    st.write("Every example investment, from best to worst match for your answers.")
    ranked = rank(profile, samples, weights=weights)
    for a in ranked:
        icon, _ = RATING_HEADLINES[a.rating]
        st.markdown(f"{icon} **{a.investment.name}**: {a.rating}")
    with st.expander("🔬 Table with scores and warnings"):
        st.dataframe(pd.DataFrame(comparison_rows(ranked)), hide_index=True)
    st.caption(sample_data_notice())


def main() -> None:
    header()
    profile = profile_questions()
    weights = weights_sidebar()
    samples = _samples()
    st.write("")
    tab_one, tab_two, tab_port, tab_all, tab_how = st.tabs(
        ["🔎 Check an investment", "↔️ Compare two", "🧺 Check a portfolio", "📋 Rank all examples", "📖 How it works"]
    )
    with tab_one:
        check_one_tab(profile, samples, weights)
    with tab_two:
        compare_two_tab(profile, samples, weights)
    with tab_port:
        portfolio_tab(profile, samples)
    with tab_all:
        rank_all_tab(profile, samples, weights)
    with tab_how:
        path = Path(__file__).parent / "docs" / "METHODOLOGY.md"
        st.markdown(path.read_text("utf-8") if path.exists() else "See docs/METHODOLOGY.md in the repository.")


main()
