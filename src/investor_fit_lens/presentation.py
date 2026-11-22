"""UI-independent helpers for presenting assessments (kept out of the Streamlit file so they are testable)."""

from __future__ import annotations

from .scoring import FitAssessment

RATING_COLORS: dict[str, str] = {
    "Good fit": "#1a7f37",
    "Partial fit": "#9a6700",
    "Weak fit": "#bc4c00",
    "Poor fit": "#cf222e",
}

RATING_MEANINGS: dict[str, str] = {
    "Good fit": "The investment's characteristics line up with every part of the profile you entered.",
    "Partial fit": "It lines up in important ways, but at least one factor deserves a closer look.",
    "Weak fit": "Several factors, or one serious factor, point away from this profile.",
    "Poor fit": "One or more major mismatches with the profile you entered.",
}


def factor_rows(a: FitAssessment) -> list[dict]:
    return [
        {
            "Factor": f.label,
            "Score (0-100)": round(f.score),
            "Weight": f"{f.weight:.0%}",
            "Points": round(f.contribution, 1),
            "Why": f.explanation,
        }
        for f in a.factors
    ]


def comparison_rows(results: list[FitAssessment]) -> list[dict]:
    rows = []
    for a in results:
        critical = [f.title for f in a.flags if f.severity == "critical"]
        warnings = [f.title for f in a.flags if f.severity == "warning"]
        rows.append(
            {
                "Investment": a.investment.name,
                "Rating": a.rating,
                "Fit score": round(a.score),
                "Critical flags": "; ".join(critical) or "-",
                "Warnings": len(warnings),
                "Max allocation within loss capacity": f"{a.max_allocation_within_loss_capacity_pct:.0f}%",
            }
        )
    return rows


# A symbol per rating so the result is never conveyed by colour alone.
RATING_SYMBOLS: dict[str, str] = {"Good fit": "✓", "Partial fit": "◐", "Weak fit": "!", "Poor fit": "✕"}


def rating_badge_html(rating: str) -> str:
    color = RATING_COLORS.get(rating, "#57606a")
    symbol = RATING_SYMBOLS.get(rating, "")
    return (
        f'<span role="status" aria-label="Rating: {rating}" style="background:{color};color:white;'
        f'padding:0.35rem 0.9rem;border-radius:999px;font-weight:600;font-size:1.05rem;">'
        f'<span aria-hidden="true">{symbol}</span> {rating}</span>'
    )


def assessment_markdown(a: FitAssessment) -> str:
    """A self-contained Markdown report of one assessment, suitable for download or sharing."""
    from . import DISCLAIMER
    from .profile import GOAL_LABELS, LIQUIDITY_NEED_LABELS, RISK_TOLERANCE_LABELS
    from .scoring import improvement_hints

    p, inv = a.profile, a.investment
    lines = [
        f"# Investor Fit Lens report: {inv.name}",
        "",
        f"**Rating:** {a.rating}  ",
        f"**Fit score:** {a.score:.0f} / 100 (ordinal summary; not a probability or a return forecast)",
        "",
        a.summary(),
        "",
        "## Profile entered",
        "",
        f"- Horizon: {p.horizon_years:g} years",
        f"- Risk tolerance: {RISK_TOLERANCE_LABELS[p.risk_tolerance]}",
        f"- Loss capacity: {p.loss_capacity_pct:g}% of total portfolio",
        f"- Liquidity needs: {LIQUIDITY_NEED_LABELS[p.liquidity_need]}",
        f"- Goal: {GOAL_LABELS[p.goal]}",
        f"- Allocation to this investment: {p.allocation_pct:g}%",
        "",
        "## Factors",
        "",
        "| Factor | Score | Weight | Why |",
        "|---|---|---|---|",
    ]
    lines += [f"| {f.label} | {f.score:.0f} | {f.weight:.0%} | {f.explanation} |" for f in a.factors]
    lines += ["", "## Flags", ""]
    if a.flags:
        for fl in a.flags:
            cap = f" (caps the rating at {fl.cap})" if fl.cap else ""
            lines.append(f"- **{fl.severity.upper()}: {fl.title}.** {fl.detail}{cap}")
    else:
        lines.append("- None")
    hints = improvement_hints(a)
    if hints:
        lines += ["", "## What the rules respond to", ""] + [f"- {h}" for h in hints]
    source = "illustrative sample (not live or current data)" if inv.illustrative else "user-entered assumptions"
    lines += ["", "---", f"Investment data: {source}.", "", f"*{DISCLAIMER}*", ""]
    return "\n".join(lines)


def _flag_counts(a: FitAssessment) -> str:
    critical = sum(f.severity == "critical" for f in a.flags)
    warnings = sum(f.severity == "warning" for f in a.flags)
    return f"{critical} / {warnings}"


def side_by_side_rows(a: FitAssessment, b: FitAssessment) -> list[dict]:
    """Factor-by-factor comparison of two assessments for the same profile."""
    if a.profile != b.profile:
        raise ValueError("side-by-side comparison requires assessments of the same profile")
    rows = [{"": "Rating", a.investment.name: a.rating, b.investment.name: b.rating, "Difference": ""}]
    rows.append(
        {
            "": "Fit score",
            a.investment.name: f"{a.score:.0f}",
            b.investment.name: f"{b.score:.0f}",
            "Difference": f"{b.score - a.score:+.0f}",
        }
    )
    for fa, fb in zip(a.factors, b.factors, strict=True):
        rows.append(
            {
                "": fa.label,
                a.investment.name: f"{fa.score:.0f}",
                b.investment.name: f"{fb.score:.0f}",
                "Difference": f"{fb.score - fa.score:+.0f}",
            }
        )
    rows.append(
        {
            "": "Critical / warning flags",
            a.investment.name: _flag_counts(a),
            b.investment.name: _flag_counts(b),
            "Difference": "",
        }
    )
    return rows


# --------------------------------------------------------------------------
# Plain-language layer for non-specialist users
# --------------------------------------------------------------------------

RATING_HEADLINES: dict[str, tuple[str, str]] = {
    "Good fit": ("✅", "This investment matches your answers well."),
    "Partial fit": ("⚠️", "It matches you in some ways, but something important doesn't."),
    "Weak fit": ("🟠", "Several things about it don't match your situation."),
    "Poor fit": ("❌", "This investment doesn't match your situation."),
}

PLAIN_RISK_LABELS: dict[int, str] = {
    1: "I'd be very upset: I can't stand seeing my money go down",
    2: "I'd be uncomfortable, but small dips are okay",
    3: "I'd be uneasy, but I'd wait it out",
    4: "I'd stay calm: ups and downs are part of investing",
    5: "I'd see it as an opportunity: I accept big swings",
}

PLAIN_LIQUIDITY_LABELS: dict[str, str] = {
    "high": "Yes, I might need it within a year",
    "medium": "Maybe, in 1 to 3 years",
    "low": "No, not for at least 3 years",
}

PLAIN_GOAL_LABELS: dict[str, str] = {
    "preservation": "🛡️ Keep it safe",
    "income": "💵 Pay me regular income",
    "balanced": "⚖️ Grow steadily, with some safety",
    "growth": "📈 Grow as much as possible over the long term",
    "speculation": "🎲 Take a big chance for a big gain",
}

_GOAL_PHRASES: dict[str, str] = {
    "preservation": "keeping money safe",
    "income": "earning regular income",
    "balanced": "steady, balanced growth",
    "growth": "long-term growth",
    "speculation": "high-risk, high-reward bets",
}


def factor_icon(score: float) -> str:
    """✅ for scores of 80 and up, ⚠️ for 40-79, ❌ below 40."""
    if score >= 80:
        return "✅"
    if score >= 40:
        return "⚠️"
    return "❌"


def plain_reasons(a: FitAssessment) -> list[tuple[str, str]]:
    """One everyday-language sentence per factor, each paired with a status icon."""
    p, inv = a.profile, a.investment
    by_key = {f.key: f for f in a.factors}
    reasons: list[tuple[str, str]] = []

    s = by_key["horizon"].score
    if inv.max_suggested_holding_years is not None and p.horizon_years > inv.max_suggested_holding_years:
        text = "It's designed to be held for days or weeks, not the years you plan to stay invested."
    elif s >= 80:
        text = "You can leave the money invested long enough for this kind of investment."
    else:
        text = (
            f"This usually needs about {inv.min_horizon_years:g} years to recover from bad periods, "
            f"but you may need the money in {p.horizon_years:g}."
        )
    reasons.append((factor_icon(s), text))

    s = by_key["risk"].score
    text = (
        "Its ups and downs are within what you said you're comfortable with."
        if s >= 80
        else "Its value can swing more than you said you're comfortable with."
    )
    reasons.append((factor_icon(s), text))

    s = by_key["loss"].score
    loss = a.portfolio_stress_loss_pct
    if s >= 80:
        text = (
            f"Even in a severe crash, the loss (about {loss:.1f}% of your savings) would stay within "
            f"what you can afford ({p.loss_capacity_pct:g}%)."
        )
    else:
        text = (
            f"In a severe crash you could lose about {loss:.1f}% of your savings, more than the "
            f"{p.loss_capacity_pct:g}% you said you can afford."
        )
    reasons.append((factor_icon(s), text))

    s = by_key["liquidity"].score
    text = (
        "You should be able to get your money out when you need it."
        if s >= 80
        else "Your money could be hard or costly to get out when you need it."
    )
    reasons.append((factor_icon(s), text))

    s = by_key["goal"].score
    phrase = _GOAL_PHRASES[p.goal]
    if s >= 75:
        text = f"It's commonly used for {phrase}, which is your goal."
    elif s >= 40:
        text = f"It can help with {phrase}, but it isn't the most typical choice."
    else:
        text = f"It isn't usually used for {phrase}, which is your goal."
    reasons.append((factor_icon(s), text))
    return reasons
