## Methodology

Investor Fit Lens answers one question: **how well do an investment's characteristics line up with the profile you entered?** It does not judge whether an investment is "good", and it does not forecast returns.

### Inputs

**Your profile**

| Input | Meaning |
|---|---|
| Horizon (years) | How long the money can stay invested before you need it |
| Risk tolerance (1-5) | How comfortable you are with swings in value (*willingness*) |
| Loss capacity (%) | The largest one-year decline of your **total portfolio** you could absorb without changing your plans (*ability*) |
| Liquidity needs | High (within 12 months), medium (1-3 years), low (3+ years) |
| Goal | Preservation, income, balanced, growth, or speculation |
| Allocation (%) | The share of your portfolio this investment would represent |

**The investment** (sample assumptions or your own)

The investment is described by a risk level (1-5), a plausible severe decline (%), liquidity (high/medium/low), a suggested minimum horizon, complexity, whether it is diversified, and a 0-100 "goal fit" for each goal.

### Five factors

Each factor is scored from 0 to 100 by one simple rule.

| Factor | Weight | Rule |
|---|---|---|
| Time horizon | 20% | 100 if your horizon ≥ the suggested minimum; otherwise proportional (e.g. 3 of 6 years → 50). Products designed only for short holding periods score 30 when held longer. |
| Risk tolerance | 20% | Investment risk level minus your tolerance: ≤0 → 100, +1 → 60, +2 → 25, ≥+3 → 0 |
| Loss capacity | 20% | Portfolio stress loss = severe decline × allocation. Within your capacity → 100; falls linearly to 0 at twice your capacity |
| Liquidity needs | 15% | Matrix of your need vs. the investment's liquidity (e.g. high need + locked product → 0) |
| Goal alignment | 25% | The investment's goal-fit value for your goal |

**Fit score** = weighted average of the five factor scores.

### Rating bands and caps

| Fit score | Rating |
|---|---|
| 75-100 | Good fit |
| 55-74 | Partial fit |
| 35-54 | Weak fit |
| 0-34 | Poor fit |

An average can hide one serious problem, so specific mismatches **cap** the rating whatever the score:

| Condition | Severity | Rating cap |
|---|---|---|
| Money may be needed within 12 months, investment is locked | Critical | Poor fit |
| Risk level ≥3 steps above your tolerance | Critical | Poor fit |
| Horizon below half the suggested minimum | Critical | Weak fit |
| Illustrative portfolio loss more than 2× your loss capacity | Critical | Weak fit |
| Short-term product held far beyond its design | Critical | Weak fit |
| Any risk above your stated tolerance | Warning | Partial fit |
| Goal fit below 40 | Warning | Partial fit |
| Single undiversified holding above 25% of the portfolio | Warning | Partial fit |

Other warnings, such as a horizon somewhat below the minimum, a loss up to 2× capacity, high complexity, or concentration above 10%, and informational product notes are shown but do not cap the rating.

The app also reports the **largest allocation** that would keep the illustrative stress loss within your loss capacity.

### How to read the score

- It is an **ordinal summary of rule-based judgements**, not a probability, a quality grade, or a forecast. Differences of a few points are not meaningful.
- Every number traces back to a rule above and an assumption you can see in the app.
- Changing the weights or thresholds changes the results. They are reasonable defaults chosen for teaching, not calibrated against outcomes.

### Limitations

- **Illustrative data.** The sample investments are generic types with round-number assumptions. They are not live, not current, and not specific products.
- **Single-investment view.** It looks at one position plus its share of your portfolio. It does not model correlations, your other holdings, taxes, fees, inflation, debt, or income stability.
- **Self-reported profile.** The result is only as good as the answers. The tool doesn't verify them or run a full risk-profiling questionnaire.
- **Rules, not regulation.** It is not a regulatory suitability or "Know Your Client" assessment and does not satisfy any legal obligation.
- **No advice.** It is an educational decision-support tool, not personalized financial advice. Consider speaking with a licensed professional.
