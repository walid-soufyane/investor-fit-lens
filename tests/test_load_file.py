import json
from pathlib import Path

import pytest

from investor_fit_lens import load_investments
from investor_fit_lens.cli import main

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "my_investments.json"


def test_example_file_loads_as_user_assumptions():
    invs = load_investments(EXAMPLE)
    assert len(invs) == 1 and invs[0].illustrative is False


def test_bare_list_and_validation(tmp_path):
    item = json.loads(EXAMPLE.read_text())["investments"][0]
    f = tmp_path / "list.json"
    f.write_text(json.dumps([item]))
    assert load_investments(f)[0].id == item["id"]
    f.write_text(json.dumps([item, item]))
    with pytest.raises(ValueError, match="unique"):
        load_investments(f)
    f.write_text(json.dumps([{**item, "risk_level": 9}]))
    with pytest.raises(ValueError):
        load_investments(f)
    f.write_text("[]")
    with pytest.raises(ValueError):
        load_investments(f)


def test_cli_with_file(capsys, tmp_path):
    assert main(["demo", "--file", str(EXAMPLE), "--investment", "example_target_date_fund"]) == 0
    out = capsys.readouterr().out
    assert "your own assumptions" in out and "Example: target-date retirement fund" in out
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert main(["demo", "--file", str(bad)]) == 2


def test_cli_json_output(capsys):
    assert main(["demo", "--json", "--investment", "term_deposit_1y", "--liquidity", "high"]) == 0
    data = json.loads(capsys.readouterr().out)
    (a,) = data["assessments"]
    assert a["rating"] == "Poor fit" and a["capped"] is True
    assert {f["key"] for f in a["factors"]} == {"horizon", "risk", "loss", "liquidity", "goal"}
    assert any(f["cap"] == "Poor fit" for f in a["flags"])
    assert "not provide personalized financial" in data["disclaimer"]
    assert main(["demo", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)["assessments"]) == 13
