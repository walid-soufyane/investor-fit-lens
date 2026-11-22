"""Investor Fit Lens: a transparent, profile-relative investment suitability analyzer.

Educational decision-support tool. Not personalized financial advice and not a
prediction of returns.
"""

from .investments import Investment, load_investments, load_sample_investments, sample_data_notice
from .profile import (
    GOAL_LABELS,
    LIQUIDITY_NEED_LABELS,
    PROFILE_PRESETS,
    RISK_TOLERANCE_LABELS,
    InvestorProfile,
    preset_profile,
)
from .scoring import WEIGHTS, FactorResult, FitAssessment, Flag, assess, improvement_hints, rank, rating_for_score

__version__ = "0.2.0"

DISCLAIMER = (
    "Educational decision-support tool only. It does not provide personalized financial, investment, "
    "tax or legal advice, does not predict returns, and cannot account for your full financial situation. "
    "Sample investment data is illustrative, not current market data. Consider speaking with a licensed "
    "professional before making investment decisions."
)

__all__ = [
    "DISCLAIMER",
    "GOAL_LABELS",
    "LIQUIDITY_NEED_LABELS",
    "PROFILE_PRESETS",
    "RISK_TOLERANCE_LABELS",
    "WEIGHTS",
    "FactorResult",
    "FitAssessment",
    "Flag",
    "Investment",
    "InvestorProfile",
    "__version__",
    "assess",
    "improvement_hints",
    "load_investments",
    "load_sample_investments",
    "preset_profile",
    "rank",
    "rating_for_score",
    "sample_data_notice",
]
