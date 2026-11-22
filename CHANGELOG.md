# Changelog

## 0.3.0 (2026-11-22)

### Added
- Portfolio mode: `assess_portfolio()` with `Holding`, a "Portfolio" tab in the app, and an `investor-fit-lens portfolio` CLI command. It checks combined stress loss, weighted risk, locked money and concentration, alongside each holding's own fit.
- Methodology and README sections for portfolio mode.

## 0.2.0 (2026-11-22)

### Added
- Example profile presets (`preset_profile()` and a sidebar selector).
- Improvement hints: the specific changes each scoring rule responds to.
- Downloadable Markdown report for an assessment.
- Adjustable factor weights in an advanced sidebar section; `rank()` accepts weights.
- "Side by side" tab comparing two investments factor by factor.
- `load_investments()` and CLI `--file` for user-described investments, with a template in `examples/`.
- CLI `--json` output and `FitAssessment.to_dict()`.
- Invariant tests: a more favourable profile never lowers the score or rating.
- pre-commit hooks and Dependabot configuration.

### Changed
- Rating badges include a symbol and an accessible label, so they don't rely on colour alone.
- Profile widgets keep their values in session state, so presets can update them.

## 0.1.0 (2026-11-22)

Initial release: scoring engine with five weighted factors and rating caps, 13 illustrative sample investments, Streamlit app, CLI demo, tests and CI.
