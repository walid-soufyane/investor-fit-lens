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


def rating_badge_html(rating: str) -> str:
    color = RATING_COLORS.get(rating, "#57606a")
    return (
        f'<span style="background:{color};color:white;padding:0.35rem 0.9rem;border-radius:999px;'
        f'font-weight:600;font-size:1.05rem;">{rating}</span>'
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
