"""Investor profile: the inputs the suitability assessment is relative to."""

from __future__ import annotations

from dataclasses import dataclass

RISK_TOLERANCE_LABELS: dict[int, str] = {
    1: "Very low: I want to avoid declines, even small ones",
    2: "Low: small, temporary declines are acceptable",
    3: "Moderate: I accept noticeable swings for some growth",
    4: "High: I accept large swings for higher long-term growth",
    5: "Very high: I accept very large or total losses on part of my money",
}

LIQUIDITY_NEED_LABELS: dict[str, str] = {
    "high": "High: I may need this money within 12 months",
    "medium": "Medium: I may need it within 1-3 years",
    "low": "Low: I do not expect to need it for 3+ years",
}

GOAL_LABELS: dict[str, str] = {
    "preservation": "Capital preservation",
    "income": "Regular income",
    "balanced": "Balanced growth and stability",
    "growth": "Long-term growth",
    "speculation": "Speculation / high-risk opportunity",
}


@dataclass(frozen=True)
class InvestorProfile:
    """What the investor told us. Every assessment is relative to these values.

    Attributes
    ----------
    horizon_years:
        How long the money can stay invested before it is needed.
    risk_tolerance:
        Willingness to accept swings in value, 1 (very low) to 5 (very high).
    loss_capacity_pct:
        The largest decline of the *total portfolio* the investor could absorb
        in a bad year without changing their plans (0-100). This is about
        ability, not willingness.
    liquidity_need:
        ``"high"``, ``"medium"`` or ``"low"``; see :data:`LIQUIDITY_NEED_LABELS`.
    goal:
        One of :data:`GOAL_LABELS`.
    allocation_pct:
        The share of the total portfolio this investment would represent (1-100).
    """

    horizon_years: float
    risk_tolerance: int
    loss_capacity_pct: float
    liquidity_need: str
    goal: str
    allocation_pct: float = 10.0

    def __post_init__(self) -> None:
        errors = self.validation_errors()
        if errors:
            raise ValueError("Invalid investor profile: " + "; ".join(errors))

    def validation_errors(self) -> list[str]:
        errors = []
        if not 0 <= self.horizon_years <= 60:
            errors.append("horizon_years must be between 0 and 60")
        if self.risk_tolerance not in RISK_TOLERANCE_LABELS:
            errors.append("risk_tolerance must be an integer from 1 to 5")
        if not 0 <= self.loss_capacity_pct <= 100:
            errors.append("loss_capacity_pct must be between 0 and 100")
        if self.liquidity_need not in LIQUIDITY_NEED_LABELS:
            errors.append(f"liquidity_need must be one of {sorted(LIQUIDITY_NEED_LABELS)}")
        if self.goal not in GOAL_LABELS:
            errors.append(f"goal must be one of {sorted(GOAL_LABELS)}")
        if not 0 < self.allocation_pct <= 100:
            errors.append("allocation_pct must be greater than 0 and at most 100")
        return errors
