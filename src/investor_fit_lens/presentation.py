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
