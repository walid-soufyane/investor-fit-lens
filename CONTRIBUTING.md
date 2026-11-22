# Contributing

Thanks for your interest in Investor Fit Lens!

## Setup

```bash
git clone https://github.com/walid-soufyane/investor-fit-lens.git
cd investor-fit-lens
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
streamlit run streamlit_app.py
pip install pre-commit && pre-commit install   # optional: lint/format automatically on commit
```

## Guidelines

- **Keep scoring transparent.** Every rule must be explainable in one sentence and documented in `docs/METHODOLOGY.md`. If you change a weight, threshold, cap or sample assumption, update the methodology doc and the tests in the same pull request.
- **Keep the engine UI-free.** Logic belongs in `src/investor_fit_lens/`, where it can be unit-tested. `streamlit_app.py` should only collect inputs and display results.
- **No live data or API keys in the core app.** Sample investments must stay generic and clearly labelled illustrative. Don't add figures that imply they are current.
- **Honest wording.** Don't describe outputs as recommendations, advice, or predictions.
- Before opening a PR, make sure `pytest`, `ruff check .` and `ruff format --check .` pass.

## Reporting issues

Open a GitHub issue with steps to reproduce, the profile and investment you used, and what you expected to see. For scoring disagreements, explain which rule you think is wrong and why. A concrete counterexample is the most helpful.

## Code of conduct

Be respectful and constructive. Harassment or discrimination of any kind isn't tolerated.
