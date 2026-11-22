"""Investment profiles and the bundled illustrative sample set.

The sample figures are **illustrative assumptions** chosen to describe broad
types of investments. They are not live market data, not current, not sourced
from any provider, and not forecasts. ``stress_drawdown_pct`` is a round
number describing the rough order of magnitude of the decline such an asset
type *could* experience in a severe market stress; real outcomes can be
better or much worse.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources

from .profile import GOAL_LABELS

LIQUIDITY_LEVELS = ("high", "medium", "low")
COMPLEXITY_LEVELS = ("low", "medium", "high")


@dataclass(frozen=True)
class Investment:
    """Characteristics of an investment that the scoring engine uses."""

    id: str
    name: str
    category: str
    description: str
    risk_level: int
    stress_drawdown_pct: float
    liquidity: str
    min_horizon_years: float
    goal_fit: dict[str, float]
    complexity: str = "low"
    diversified: bool = True
    max_suggested_holding_years: float | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)
    illustrative: bool = True

    def __post_init__(self) -> None:
        errors = []
        if not 1 <= self.risk_level <= 5:
            errors.append("risk_level must be 1-5")
        if not 0 <= self.stress_drawdown_pct <= 100:
            errors.append("stress_drawdown_pct must be 0-100")
        if self.liquidity not in LIQUIDITY_LEVELS:
            errors.append(f"liquidity must be one of {LIQUIDITY_LEVELS}")
        if self.complexity not in COMPLEXITY_LEVELS:
            errors.append(f"complexity must be one of {COMPLEXITY_LEVELS}")
        if self.min_horizon_years < 0:
            errors.append("min_horizon_years must be >= 0")
        missing = set(GOAL_LABELS) - set(self.goal_fit)
        if missing:
            errors.append(f"goal_fit missing goals: {sorted(missing)}")
        if any(not 0 <= v <= 100 for v in self.goal_fit.values()):
            errors.append("goal_fit values must be 0-100")
        if errors:
            raise ValueError(f"Invalid investment '{self.id}': " + "; ".join(errors))

    @classmethod
    def from_dict(cls, data: dict) -> Investment:
        data = dict(data)
        data["notes"] = tuple(data.get("notes", ()))
        return cls(**data)


def load_sample_investments() -> list[Investment]:
    """Load the bundled illustrative sample investments."""
    text = resources.files("investor_fit_lens").joinpath("data/sample_investments.json").read_text("utf-8")
    payload = json.loads(text)
    return [Investment.from_dict(item) for item in payload["investments"]]


def sample_data_notice() -> str:
    text = resources.files("investor_fit_lens").joinpath("data/sample_investments.json").read_text("utf-8")
    return json.loads(text)["notice"]
