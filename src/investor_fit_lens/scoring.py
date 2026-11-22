"""Transparent, profile-relative suitability scoring.

How it works
------------
1. Five factors are each scored 0-100 by a small, documented rule:

   ========== ======= ==========================================================
   Factor     Weight  Rule
   ========== ======= ==========================================================
   horizon    20%     investor horizon / investment's minimum suggested horizon
   risk       20%     gap between investment risk level and stated tolerance
   loss       20%     portfolio-level stress loss vs. stated loss capacity
   liquidity  15%     liquidity need vs. how easily the investment can be sold
   goal       25%     how well the investment's role matches the stated goal
   ========== ======= ==========================================================

2. The fit score is the weighted average of the five factor scores.
3. The score maps to a rating band: Good (>=75), Partial (55-74),
   Weak (35-54), Poor (<35).
4. Specific mismatches **cap** the rating regardless of the score, because a
   high average should not hide a single serious problem. Critical flags
   (e.g. money needed within a year going into a locked product) cap at
   Poor or Weak; some warnings (e.g. any risk above the stated tolerance, a
   clear goal mismatch, heavy single-holding concentration) cap at Partial.

The score is an ordinal summary of rule-based judgements, not a probability
and not a forecast of returns. Differences of a few points are not meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .investments import Investment
from .profile import GOAL_LABELS, InvestorProfile

WEIGHTS: dict[str, float] = {
    "horizon": 0.20,
    "risk": 0.20,
    "loss": 0.20,
    "liquidity": 0.15,
    "goal": 0.25,
}

FACTOR_LABELS: dict[str, str] = {
    "horizon": "Time horizon",
    "risk": "Risk tolerance",
    "loss": "Loss capacity",
    "liquidity": "Liquidity needs",
    "goal": "Goal alignment",
}

RATINGS: tuple[str, ...] = ("Poor fit", "Weak fit", "Partial fit", "Good fit")  # worst -> best
RATING_THRESHOLDS: tuple[tuple[float, str], ...] = ((75, "Good fit"), (55, "Partial fit"), (35, "Weak fit"))

# How easily the money can be reached, versus how soon the investor may need it.
LIQUIDITY_MATRIX: dict[str, dict[str, float]] = {
    "high": {"high": 100, "medium": 40, "low": 0},
    "medium": {"high": 100, "medium": 75, "low": 30},
    "low": {"high": 100, "medium": 100, "low": 90},
}

RISK_GAP_SCORES: dict[int, float] = {1: 60, 2: 25}  # gap <= 0 -> 100, gap >= 3 -> 0


@dataclass(frozen=True)
class FactorResult:
    key: str
    label: str
    score: float
    weight: float
    explanation: str

    @property
    def contribution(self) -> float:
        return self.score * self.weight


@dataclass(frozen=True)
class Flag:
    severity: str  # "critical" | "warning" | "info"
    title: str
    detail: str
    cap: str | None = None  # rating ceiling imposed by this flag, if any


@dataclass
class FitAssessment:
    investment: Investment
    profile: InvestorProfile
    score: float
    score_rating: str
    rating: str
    factors: list[FactorResult]
    flags: list[Flag] = field(default_factory=list)
    portfolio_stress_loss_pct: float = 0.0
    max_allocation_within_loss_capacity_pct: float = 100.0

    @property
    def is_capped(self) -> bool:
        return self.rating != self.score_rating

    def summary(self) -> str:
        ordered = sorted(self.factors, key=lambda f: f.score)
        weakest = [f.label.lower() for f in ordered if f.score < 60][:2]
        strongest = [f.label.lower() for f in reversed(ordered) if f.score >= 80][:2]
        parts = [
            f"For the profile entered, {self.investment.name} is rated {self.rating} (fit score {self.score:.0f}/100)."
        ]
        if self.is_capped:
            caps = [f.title.lower() for f in self.flags if f.cap == self.rating]
            reason = f" ({caps[0]})" if caps else ""
            parts.append(
                f"The score alone would suggest {self.score_rating}, but a specific mismatch{reason} "
                f"caps the rating at {self.rating}."
            )
        if strongest:
            parts.append("Strongest alignment: " + " and ".join(strongest) + ".")
        if weakest:
            parts.append("Main concerns: " + " and ".join(weakest) + ".")
        return " ".join(parts)


# --------------------------------------------------------------------------
# Factor rules (pure functions; each returns (score, explanation, flags))
# --------------------------------------------------------------------------


def score_horizon(profile: InvestorProfile, inv: Investment) -> tuple[float, str, list[Flag]]:
    flags: list[Flag] = []
    h, need = profile.horizon_years, inv.min_horizon_years
    max_hold = inv.max_suggested_holding_years
    if max_hold is not None and h > max_hold:
        flags.append(
            Flag(
                "critical",
                "Designed for short holding periods",
                f"This product is generally intended to be held for about {max_hold:g} years or less, "
                f"but your horizon is {h:g} years. Long holding periods can produce results very different "
                "from what the product's description suggests.",
                cap="Weak fit",
            )
        )
        return 30.0, f"Your {h:g}-year horizon is much longer than this product is designed for.", flags
    if need <= 0 or h >= need:
        why = "no minimum holding period" if need <= 0 else f"a suggested minimum of {need:g} years"
        return 100.0, f"Your {h:g}-year horizon meets {why}.", flags
    ratio = h / need
    score = round(100 * ratio, 1)
    if ratio < 0.5:
        flags.append(
            Flag(
                "critical",
                "Horizon far too short",
                f"Your horizon ({h:g} years) is less than half the suggested minimum ({need:g} years). "
                "There may not be time to recover from a decline before the money is needed.",
                cap="Weak fit",
            )
        )
    else:
        flags.append(
            Flag(
                "warning",
                "Horizon shorter than suggested",
                f"Your horizon ({h:g} years) is below the suggested minimum of {need:g} years.",
            )
        )
    return score, f"Your {h:g}-year horizon covers {ratio:.0%} of the suggested {need:g}-year minimum.", flags


def score_risk(profile: InvestorProfile, inv: Investment) -> tuple[float, str, list[Flag]]:
    gap = inv.risk_level - profile.risk_tolerance
    level = f"risk level {inv.risk_level}/5 vs. your tolerance {profile.risk_tolerance}/5"
    if gap <= 0:
        return 100.0, f"Within your stated risk tolerance ({level}).", []
    if gap >= 3:
        flag = Flag(
            "critical",
            "Far above your risk tolerance",
            f"The investment's risk level is {gap} steps above what you said you are comfortable with.",
            cap="Poor fit",
        )
        return 0.0, f"Well above your stated tolerance ({level}).", [flag]
    flag = Flag(
        "warning",
        "Above your risk tolerance",
        f"The investment's risk level is {gap} step{'s' if gap > 1 else ''} above your stated tolerance; "
        "expect swings larger than you said you are comfortable with.",
        cap="Partial fit",
    )
    return RISK_GAP_SCORES[gap], f"Above your stated tolerance ({level}).", [flag]


def portfolio_stress_loss(profile: InvestorProfile, inv: Investment) -> float:
    """Illustrative stress decline of the *total* portfolio from this position alone, in %."""
    return inv.stress_drawdown_pct * profile.allocation_pct / 100.0


def max_allocation_within_capacity(profile: InvestorProfile, inv: Investment) -> float:
    """Largest allocation (%) whose illustrative stress loss stays within loss capacity."""
    if inv.stress_drawdown_pct <= 0:
        return 100.0
    return min(100.0, profile.loss_capacity_pct / inv.stress_drawdown_pct * 100.0)


def score_loss(profile: InvestorProfile, inv: Investment) -> tuple[float, str, list[Flag]]:
    loss = portfolio_stress_loss(profile, inv)
    cap = profile.loss_capacity_pct
    base = (
        f"An illustrative {inv.stress_drawdown_pct:g}% stress decline on a {profile.allocation_pct:g}% "
        f"allocation is about {loss:.1f}% of your portfolio, vs. your {cap:g}% loss capacity."
    )
    if loss <= cap:
        return 100.0, base, []
    ratio = loss / cap if cap > 0 else float("inf")
    score = max(0.0, round(100 * (2 - ratio), 1))
    max_alloc = max_allocation_within_capacity(profile, inv)
    if ratio > 2:
        flag = Flag(
            "critical",
            "Potential loss well beyond your capacity",
            f"In a severe decline this position alone could cost more than twice the loss you said you "
            f"could absorb. An allocation of about {max_alloc:.1f}% or less would stay within it.",
            cap="Weak fit",
        )
    else:
        flag = Flag(
            "warning",
            "Potential loss exceeds your capacity",
            f"In a severe decline this position could cost more than you said you could absorb. "
            f"An allocation of about {max_alloc:.1f}% or less would stay within it.",
        )
    return score, base, [flag]


def score_liquidity(profile: InvestorProfile, inv: Investment) -> tuple[float, str, list[Flag]]:
    score = LIQUIDITY_MATRIX[profile.liquidity_need][inv.liquidity]
    expl = f"Your liquidity need is {profile.liquidity_need}; the investment's liquidity is {inv.liquidity}."
    flags: list[Flag] = []
    if profile.liquidity_need == "high" and inv.liquidity == "low":
        flags.append(
            Flag(
                "critical",
                "Money may be locked when you need it",
                "You may need this money within 12 months, but this investment can be hard or impossible "
                "to sell before maturity or during a lock-up.",
                cap="Poor fit",
            )
        )
    elif score < 60:
        flags.append(
            Flag(
                "warning",
                "Liquidity mismatch",
                "Selling quickly could be difficult or costly relative to when you may need the money.",
            )
        )
    return score, expl, flags


def score_goal(profile: InvestorProfile, inv: Investment) -> tuple[float, str, list[Flag]]:
    score = float(inv.goal_fit[profile.goal])
    goal = GOAL_LABELS[profile.goal].lower()
    flags: list[Flag] = []
    if score >= 75:
        expl = f"Typically used for {goal}."
    elif score >= 40:
        expl = f"Can play a partial role in {goal}."
    else:
        expl = f"Not typically used for {goal}."
        flags.append(
            Flag(
                "warning",
                "Weak match with your goal",
                f"This type of investment is not typically used for {goal}, so even if it is otherwise "
                "comfortable, it may not move you toward what you said you want.",
                cap="Partial fit",
            )
        )
    return score, expl, flags


FACTOR_FUNCS = {
    "horizon": score_horizon,
    "risk": score_risk,
    "loss": score_loss,
    "liquidity": score_liquidity,
    "goal": score_goal,
}


def rating_for_score(score: float) -> str:
    for threshold, label in RATING_THRESHOLDS:
        if score >= threshold:
            return label
    return "Poor fit"


def _worse(a: str, b: str) -> str:
    return a if RATINGS.index(a) <= RATINGS.index(b) else b


def _general_flags(profile: InvestorProfile, inv: Investment) -> list[Flag]:
    flags = []
    if not inv.diversified and profile.allocation_pct > 10:
        heavy = profile.allocation_pct > 25
        flags.append(
            Flag(
                "warning",
                "Concentration",
                f"Putting {profile.allocation_pct:g}% of your portfolio into a single, undiversified holding "
                "concentrates risk in one outcome.",
                cap="Partial fit" if heavy else None,
            )
        )
    if inv.complexity == "high":
        flags.append(
            Flag(
                "warning",
                "Complex product",
                "Make sure you understand how this product works, what it costs, and how it behaves in stress.",
            )
        )
    for note in inv.notes:
        flags.append(Flag("info", "Product characteristic", note))
    return flags


def assess(profile: InvestorProfile, inv: Investment, weights: dict[str, float] | None = None) -> FitAssessment:
    """Assess how well ``inv`` fits ``profile``."""
    weights = weights or WEIGHTS
    if set(weights) != set(FACTOR_FUNCS):
        raise ValueError(f"weights must have exactly these keys: {sorted(FACTOR_FUNCS)}")
    total_w = sum(weights.values())
    if total_w <= 0 or any(w < 0 for w in weights.values()):
        raise ValueError("weights must be non-negative and sum to a positive number")

    factors: list[FactorResult] = []
    flags: list[Flag] = []
    for key, func in FACTOR_FUNCS.items():
        score, expl, fl = func(profile, inv)
        factors.append(FactorResult(key, FACTOR_LABELS[key], score, weights[key] / total_w, expl))
        flags.extend(fl)
    flags.extend(_general_flags(profile, inv))

    score = round(sum(f.contribution for f in factors), 1)
    score_rating = rating_for_score(score)
    rating = score_rating
    for flag in flags:
        if flag.cap:
            rating = _worse(rating, flag.cap)

    order = {"critical": 0, "warning": 1, "info": 2}
    flags.sort(key=lambda f: order[f.severity])
    return FitAssessment(
        investment=inv,
        profile=profile,
        score=score,
        score_rating=score_rating,
        rating=rating,
        factors=factors,
        flags=flags,
        portfolio_stress_loss_pct=portfolio_stress_loss(profile, inv),
        max_allocation_within_loss_capacity_pct=max_allocation_within_capacity(profile, inv),
    )


def rank(
    profile: InvestorProfile, investments: list[Investment], weights: dict[str, float] | None = None
) -> list[FitAssessment]:
    """Assess every investment and sort by rating, then score (best first)."""
    results = [assess(profile, inv, weights=weights) for inv in investments]
    return sorted(results, key=lambda a: (RATINGS.index(a.rating), a.score), reverse=True)


def improvement_hints(a: FitAssessment) -> list[str]:
    """Concrete profile or position changes that would remove each mismatch.

    These describe what the *rules* respond to. They are not suggestions that
    the investor should change their circumstances to fit a product.
    """
    p, inv = a.profile, a.investment
    hints: list[str] = []
    if inv.max_suggested_holding_years is not None and p.horizon_years > inv.max_suggested_holding_years:
        hints.append("This product is built for short holding periods; a long horizon will not fit it.")
    elif inv.min_horizon_years > p.horizon_years:
        hints.append(f"A horizon of at least {inv.min_horizon_years:g} years would remove the horizon concern.")
    if inv.risk_level > p.risk_tolerance:
        hints.append(f"The risk factor clears only with a risk tolerance of {inv.risk_level}/5 or higher.")
    if a.portfolio_stress_loss_pct > p.loss_capacity_pct:
        hints.append(
            f"Reducing the allocation to about {a.max_allocation_within_loss_capacity_pct:.1f}% or less would keep "
            "the illustrative stress loss within your loss capacity."
        )
    if p.liquidity_need == "high" and inv.liquidity != "high":
        hints.append("If this money may be needed within 12 months, a more liquid investment fits that need better.")
    if inv.goal_fit[p.goal] < 40:
        hints.append("This investment is rarely used for your stated goal; one closer to that goal would fit better.")
    if not inv.diversified and p.allocation_pct > 10:
        hints.append(
            "Keeping a single, undiversified holding at or below 10% of the portfolio avoids the concentration flag."
        )
    return hints
