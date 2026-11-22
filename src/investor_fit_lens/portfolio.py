"""Portfolio mode: assess several holdings together against one profile.

Each holding is assessed individually (with its own allocation), and a few
portfolio-level checks are added on top. The combined stress loss assumes all
holdings experience their illustrative severe decline *at the same time*. That
is a deliberately conservative simplification: real assets are not perfectly
correlated, but in severe crises correlations tend to rise. Unallocated weight
is treated as cash with no stress loss.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from .investments import Investment
from .profile import InvestorProfile
from .scoring import RATINGS, FitAssessment, Flag, assess


@dataclass(frozen=True)
class Holding:
    investment: Investment
    allocation_pct: float


@dataclass
class PortfolioAssessment:
    profile: InvestorProfile
    holdings: list[FitAssessment]
    total_allocation_pct: float
    combined_stress_loss_pct: float
    weighted_risk_level: float
    low_liquidity_share_pct: float
    flags: list[Flag] = field(default_factory=list)

    @property
    def rating_counts(self) -> dict[str, int]:
        counts = {r: 0 for r in reversed(RATINGS)}
        for a in self.holdings:
            counts[a.rating] += 1
        return counts

    def summary(self) -> str:
        p = self.profile
        parts = [
            f"{len(self.holdings)} holdings covering {self.total_allocation_pct:g}% of the portfolio"
            + (f" ({100 - self.total_allocation_pct:g}% treated as cash)." if self.total_allocation_pct < 100 else "."),
            f"If every holding suffered its illustrative severe decline at once, the portfolio would fall about "
            f"{self.combined_stress_loss_pct:.1f}%, vs. your loss capacity of {p.loss_capacity_pct:g}%.",
            f"Allocation-weighted risk level {self.weighted_risk_level:.1f}/5 "
            f"vs. your tolerance of {p.risk_tolerance}/5.",
        ]
        weak = [a.investment.name for a in self.holdings if a.rating in ("Weak fit", "Poor fit")]
        if weak:
            parts.append("Holdings with weak or poor individual fit: " + ", ".join(weak) + ".")
        return " ".join(parts)


def assess_portfolio(profile: InvestorProfile, holdings: list[Holding]) -> PortfolioAssessment:
    """Assess ``holdings`` for ``profile``. The profile's own ``allocation_pct`` is ignored."""
    if not holdings:
        raise ValueError("a portfolio needs at least one holding")
    ids = [h.investment.id for h in holdings]
    if len(set(ids)) != len(ids):
        raise ValueError("each investment may appear only once")
    if any(h.allocation_pct <= 0 for h in holdings):
        raise ValueError("allocations must be positive")
    total = sum(h.allocation_pct for h in holdings)
    if total > 100 + 1e-9:
        raise ValueError(f"allocations sum to {total:g}%, which is more than 100%")

    assessed = [assess(dataclasses.replace(profile, allocation_pct=h.allocation_pct), h.investment) for h in holdings]
    stress = sum(h.investment.stress_drawdown_pct * h.allocation_pct / 100 for h in holdings)
    # Unallocated weight is cash (risk level 1).
    weighted_risk = (sum(h.investment.risk_level * h.allocation_pct for h in holdings) + (100 - total) * 1) / 100
    low_liq = sum(h.allocation_pct for h in holdings if h.investment.liquidity == "low")

    flags: list[Flag] = []
    cap = profile.loss_capacity_pct
    if stress > cap:
        severe = cap == 0 or stress > 2 * cap
        flags.append(
            Flag(
                "critical" if severe else "warning",
                "Combined potential loss exceeds your capacity",
                f"If all holdings fell together, the portfolio could lose about {stress:.1f}%, more than the "
                f"{cap:g}% you said you could absorb.",
            )
        )
    if weighted_risk > profile.risk_tolerance:
        flags.append(
            Flag(
                "warning",
                "Portfolio riskier than your tolerance",
                f"The allocation-weighted risk level ({weighted_risk:.1f}/5) is above your tolerance "
                f"({profile.risk_tolerance}/5).",
            )
        )
    if low_liq > 0 and profile.liquidity_need == "high":
        flags.append(
            Flag(
                "critical",
                "Locked money with high liquidity needs",
                f"{low_liq:g}% of the portfolio is in investments that can be hard to sell, but you may need "
                "money within 12 months.",
            )
        )
    elif low_liq > 50 and profile.liquidity_need == "medium":
        flags.append(
            Flag(
                "warning",
                "Large share in hard-to-sell investments",
                f"{low_liq:g}% of the portfolio is in low-liquidity investments relative to a 1-3 year need.",
            )
        )
    for h in holdings:
        if not h.investment.diversified and h.allocation_pct > 25:
            flags.append(
                Flag(
                    "warning",
                    "Concentrated single holding",
                    f"{h.investment.name} is {h.allocation_pct:g}% of the portfolio.",
                )
            )
    order = {"critical": 0, "warning": 1, "info": 2}
    flags.sort(key=lambda f: order[f.severity])
    return PortfolioAssessment(profile, assessed, total, stress, weighted_risk, low_liq, flags)
