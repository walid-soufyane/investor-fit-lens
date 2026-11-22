"""Text demo: ``investor-fit-lens demo`` or ``python -m investor_fit_lens demo``."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from . import (
    DISCLAIMER,
    Holding,
    InvestorProfile,
    assess,
    assess_portfolio,
    load_investments,
    load_sample_investments,
    rank,
)


def format_assessment(a) -> str:
    lines = [f"{a.investment.name}: {a.rating} (fit score {a.score:.0f}/100)", f"  {a.summary()}", "  Factors:"]
    for f in a.factors:
        lines.append(f"    {f.label:<15} {f.score:5.0f}  x{f.weight:.2f}  {f.explanation}")
    if a.flags:
        lines.append("  Flags:")
        for fl in a.flags:
            lines.append(f"    [{fl.severity.upper()}] {fl.title}: {fl.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="investor-fit-lens", description="Profile-relative suitability demo")
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--horizon", type=float, default=2)
    common.add_argument("--risk", type=int, default=2)
    common.add_argument("--loss-capacity", type=float, default=10)
    common.add_argument("--liquidity", default="medium", choices=["high", "medium", "low"])
    common.add_argument("--goal", default="income")
    common.add_argument("--file", help="JSON file of your own investments (same schema as the bundled samples)")
    demo = sub.add_parser("demo", parents=[common], help="assess sample investments for a profile")
    demo.add_argument("--allocation", type=float, default=20)
    demo.add_argument("--investment", help="investment id to assess in detail (default: rank all)")
    demo.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    port = sub.add_parser("portfolio", parents=[common], help="assess several holdings together")
    port.add_argument(
        "--holding",
        action="append",
        required=True,
        metavar="ID=PCT",
        help="investment id and its %% of the portfolio, e.g. --holding global_equity_index=40 (repeatable)",
    )
    args = parser.parse_args(argv)

    try:
        profile = InvestorProfile(
            horizon_years=args.horizon,
            risk_tolerance=args.risk,
            loss_capacity_pct=args.loss_capacity,
            liquidity_need=args.liquidity,
            goal=args.goal,
            allocation_pct=getattr(args, "allocation", 10.0),
        )
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.file:
        try:
            samples = load_investments(args.file)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"Could not load {args.file}: {exc}", file=sys.stderr)
            return 2
        source = f"investments from {args.file} (your own assumptions)"
    else:
        samples = load_sample_investments()
        source = "illustrative sample data"
    by_id = {s.id: s for s in samples}
    if args.command == "portfolio":
        return _portfolio(profile, by_id, args.holding, source)
    if args.investment and args.investment not in by_id:
        print(f"Unknown investment id. Choose from: {', '.join(by_id)}", file=sys.stderr)
        return 2
    if args.json:
        chosen = [assess(profile, by_id[args.investment])] if args.investment else rank(profile, samples)
        payload = {
            "profile": asdict(profile),
            "data_source": source,
            "disclaimer": DISCLAIMER,
            "assessments": [a.to_dict() for a in chosen],
        }
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Profile: {profile}\n({source}; educational use only.)\n")
    if args.investment:
        print(format_assessment(assess(profile, by_id[args.investment])))
    else:
        for a in rank(profile, samples):
            print(f"  {a.rating:<12} {a.score:5.0f}  {a.investment.name}")
    print(f"\n{DISCLAIMER}")
    return 0


def _portfolio(profile, by_id, specs: list[str], source: str) -> int:
    holdings = []
    for spec in specs:
        ident, _, pct = spec.partition("=")
        if ident not in by_id:
            print(f"Unknown investment id {ident!r}. Choose from: {', '.join(by_id)}", file=sys.stderr)
            return 2
        try:
            holdings.append(Holding(by_id[ident], float(pct)))
        except ValueError:
            print(f"Invalid holding {spec!r}; expected ID=PCT", file=sys.stderr)
            return 2
    try:
        pa = assess_portfolio(profile, holdings)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(f"({source}; educational use only.)\n")
    print(pa.summary(), "\n")
    for a in pa.holdings:
        print(f"  {a.profile.allocation_pct:5.1f}%  {a.rating:<12} {a.score:5.0f}  {a.investment.name}")
    if pa.flags:
        print("\nPortfolio flags:")
        for fl in pa.flags:
            print(f"  [{fl.severity.upper()}] {fl.title}: {fl.detail}")
    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
