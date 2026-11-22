import pytest

from investor_fit_lens import PROFILE_PRESETS, assess, load_sample_investments, preset_profile


@pytest.mark.parametrize("name", list(PROFILE_PRESETS))
def test_every_preset_is_a_valid_profile(name):
    assert preset_profile(name).goal in {"preservation", "income", "balanced", "growth", "speculation"}


def test_preset_overrides_and_unknown_name():
    assert preset_profile("Retiree seeking income", allocation_pct=5).allocation_pct == 5
    with pytest.raises(KeyError):
        preset_profile("Nobody")


def test_presets_produce_different_best_fits():
    samples = {s.id: s for s in load_sample_investments()}
    cautious = preset_profile("Cautious saver, short horizon")
    grower = preset_profile("Young long-term grower")
    assert assess(cautious, samples["savings_account"]).rating == "Good fit"
    assert assess(grower, samples["savings_account"]).rating != "Good fit"
    assert assess(grower, samples["global_equity_index"]).rating == "Good fit"
    assert assess(cautious, samples["global_equity_index"]).rating == "Poor fit"
