# 🔎 Investor Fit Lens

[![tests](https://github.com/walid-soufyane/investor-fit-lens/actions/workflows/tests.yml/badge.svg)](https://github.com/walid-soufyane/investor-fit-lens/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)

**Is this investment a good fit for *this* investor?**

Investor Fit Lens is a transparent, profile-relative suitability analyzer. You describe an investor (horizon, risk tolerance, loss capacity, liquidity needs, goal, position size) and pick an investment. The app returns a **fit rating**, a **0–100 fit score**, a plain-language **explanation** of each factor, and **risk flags**, along with the rule behind every number.

It never labels an investment as universally good or bad. The same covered-call fund that is a *Good fit* (98/100) for a 20-year, income-focused investor with high risk tolerance is only a *Partial fit* (74/100) for a cautious investor with a 3-year horizon.

> ⚠️ **Educational decision-support tool, not financial advice.** It does not predict returns, cannot see your full financial situation, and is not a regulatory suitability or KYC assessment. Sample investment data is **illustrative**: generic types with round-number assumptions, not live or current market data.

---

## Features

- **Profile inputs:** horizon, risk tolerance (1–5), loss capacity (% of total portfolio), liquidity needs, goal, and allocation size. Four **example profiles** can fill these in for you.
- **13 illustrative sample investments:** from a savings account and bond funds to equity index funds, REITs, a single stock, crypto, a private real estate fund with a lock-up, and a 3x leveraged ETF.
- **"Describe my own investment":** score any product using your own assumptions.
- **Explained results:** per-factor score bars with a sentence each, colour-coded critical, warning and info flags, and a note when a flag caps the rating.
- **"What would change the picture":** the largest allocation that keeps an illustrative stress loss within your loss capacity, plus the specific horizon, tolerance or goal changes that each rule responds to.
- **Downloadable report:** a Markdown file with the profile, factors, flags and disclaimer.
- **Adjustable factor weights:** an advanced sidebar option for seeing how much a result depends on the default weights.
- **Side-by-side tab:** compare two investments factor by factor.
- **Compare tab:** every sample ranked against the current profile.
- **Methodology tab:** the full scoring rules, inside the app.
- **Accessible ratings:** each rating has its own symbol and an accessible label, so it never relies on colour alone.
- **No API keys, no paid services, no network calls.**

## Quickstart

Requires Python 3.10+.

```bash
git clone https://github.com/walid-soufyane/investor-fit-lens.git
cd investor-fit-lens
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

streamlit run streamlit_app.py      # opens http://localhost:8501
```

A command-line demo is included too:

```bash
investor-fit-lens demo                                    # rank all samples for a default profile
investor-fit-lens demo --horizon 1 --liquidity high \
    --investment private_real_estate_fund                  # detailed assessment of one sample
investor-fit-lens demo --json                             # machine-readable output
investor-fit-lens demo --file examples/my_investments.json # assess your own investments
```

To assess products you are considering, copy `examples/my_investments.json` and replace the template values with your own assumptions. The file uses the same schema as the bundled samples. Investments loaded from it are labelled as your assumptions, not as samples.

## Demo walkthrough

1. **Set the profile in the sidebar.** For example: 3-year horizon, risk tolerance 2 (low), loss capacity 10%, medium liquidity needs, goal *regular income*, and 25% of the portfolio for this investment.
2. **Pick an investment.** Choose *Covered-call equity fund*. The result appears immediately. The CLI prints the same assessment:

   ```
   Covered-call equity fund: Partial fit (fit score 74/100)
     Factors:
       Time horizon       60  x0.20  Your 3-year horizon covers 60% of the suggested 5-year minimum.
       Risk tolerance     25  x0.20  Above your stated tolerance (risk level 4/5 vs. your tolerance 2/5).
       Loss capacity     100  x0.20  An illustrative 40% stress decline on a 25% allocation is about
                                     10.0% of your portfolio, vs. your 10% loss capacity.
       Liquidity needs   100  x0.15  Your liquidity need is medium; the investment's liquidity is high.
       Goal alignment     90  x0.25  Typically used for regular income.
     Flags:
       [WARNING] Horizon shorter than suggested
       [WARNING] Above your risk tolerance            (caps the rating at Partial fit)
       [INFO]    Upside in strong markets is capped by the options sold, while most of the downside remains.
       [INFO]    High distributions can include a return of capital.
   ```

   The goal matches, but the product is riskier than this investor said they are comfortable with, and the horizon is short.
3. **Change one answer.** Set liquidity needs to *High* and pick *1-year term deposit (non-redeemable)*. The deposit has no price risk, yet the rating drops to **Poor fit**. A critical flag explains why: *Money may be locked when you need it.* A high average score can't hide that.
4. **Open "Compare all samples"** to see every sample ranked for the current profile, with its critical flags and the largest allocation that stays within the loss capacity.
5. **Open "Methodology"** to see the exact rules behind every number.

> **Screenshots.** The UI isn't pictured here yet; run `streamlit run streamlit_app.py` to see it. The walkthrough above uses real output from the scoring engine.

## How the scoring works

Five factors are each scored 0–100 by a single documented rule and then combined with fixed weights:

| Factor | Weight | Rule (summary) |
|---|---|---|
| Time horizon | 20% | Proportional to your horizon ÷ the suggested minimum horizon |
| Risk tolerance | 20% | 100 if within tolerance; 60 / 25 / 0 at 1 / 2 / 3+ levels above it |
| Loss capacity | 20% | Illustrative stress loss × allocation vs. your loss capacity; 0 at 2× capacity |
| Liquidity needs | 15% | Matrix of your need vs. the investment's liquidity |
| Goal alignment | 25% | The investment's typical fit for your stated goal |

The score maps to **Good (≥75) / Partial (55–74) / Weak (35–54) / Poor (<35)**. Specific mismatches **cap** the rating whatever the score. For example, a locked product for money needed within a year caps it at *Poor*, and any risk above your tolerance caps it at *Partial*.

Full rules, caps and rationale: **[docs/METHODOLOGY.md](docs/METHODOLOGY.md)**.

**How to read the score:** it is an ordinal summary of rule-based judgements, not a probability, a quality grade or a forecast. Differences of a few points are not meaningful.

## Limitations

- The sample data is illustrative. The figures are round-number assumptions about generic investment types, not live, current or product-specific data.
- It looks at one position at a time. It doesn't model correlations, your other holdings, taxes, fees, inflation or income stability.
- The profile is self-reported and unverified, and there is no full risk questionnaire.
- The weights and thresholds are sensible teaching defaults, not values calibrated against investor outcomes.
- It is not regulatory suitability, KYC, or personalized advice.

## Project structure

```
streamlit_app.py                 Streamlit UI (thin layer over the engine)
src/investor_fit_lens/
  profile.py                     InvestorProfile + validation
  investments.py                 Investment model + sample loader
  scoring.py                     Factor rules, weights, rating caps, assess() / rank()
  presentation.py                UI-independent tables, badge and Markdown report
  cli.py                         `investor-fit-lens demo` (text or --json, samples or --file)
  data/sample_investments.json   Illustrative sample investments
examples/my_investments.json     Template for describing your own investments
docs/METHODOLOGY.md              Scoring rules and limitations (also shown in the app)
tests/                           Unit, invariant and Streamlit AppTest UI tests
```

The scoring engine is pure Python with no third-party dependencies. You can use it without the UI:

```python
from investor_fit_lens import InvestorProfile, assess, load_sample_investments

profile = InvestorProfile(
    horizon_years=5, risk_tolerance=3, loss_capacity_pct=15, liquidity_need="medium", goal="balanced", allocation_pct=20
)
fund = next(i for i in load_sample_investments() if i.id == "balanced_fund")
result = assess(profile, fund)
print(result.rating, result.score)
print(result.summary())
```

Other building blocks: `preset_profile()`, `improvement_hints()`, `rank()`, `load_investments()`, `FitAssessment.to_dict()`, and `presentation.assessment_markdown()`.

## Running the tests

```bash
pytest            # engine tests, plus Streamlit UI tests when streamlit is installed
ruff check . && ruff format --check .
```

Beyond unit tests for each rule, `tests/test_invariants.py` checks that a more favourable profile never gets a lower score or a worse rating, across about 2,300 profile and investment combinations.

GitHub Actions runs linting, the full test suite (including Streamlit's `AppTest` UI tests) and the CLI demo on Python 3.10–3.13.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Changes to scoring rules or sample assumptions should update `docs/METHODOLOGY.md` and the tests in the same pull request.

## License

[MIT](LICENSE) © 2026 Walid Soufyane

## Disclaimer

This project is for education and decision support only. It is not personalized financial, investment, tax or legal advice, does not predict returns, and should not be the sole basis for any investment decision. Consider consulting a licensed professional.
