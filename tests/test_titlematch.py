from pathlib import Path

from titlematch import normalize, extract_year, Catalog, match_title
from titlematch.__main__ import run, report

EX = Path(__file__).parent.parent / "examples"
CAT = Catalog.from_csv(EX / "catalog.csv")


def test_normalize_strips_noise():
    assert normalize("The Long Orbit S01E02 (HD)") == "long orbit"
    assert normalize("Café Noir") == "cafe noir"
    assert normalize("Salt & Pepper") == "salt and pepper"


def test_extract_year():
    assert extract_year("Harbor Lights [1998] HD") == 1998
    assert extract_year("Quiet Fields") is None


def test_exact_string():
    assert match_title("Quiet Fields", CAT).status == "exact"


def test_alias_and_normalized():
    assert match_title("TLO", CAT).status == "alias"
    r = match_title("Cafe Noir (HD)", CAT)
    assert r.title_id == "c5"


def test_year_disambiguates_same_title():
    assert match_title("Harbor Lights (2015)", CAT).title_id == "c1"
    assert match_title("Harbor Lights [1998] HD", CAT).title_id == "c2"


def test_same_title_without_year_is_ambiguous_not_guessed():
    r = match_title("HARBOR LIGHTS", CAT)
    assert r.status == "ambiguous" and r.title_id == ""


def test_country_suffix_ambiguous_then_resolved():
    assert match_title("Night Shift", CAT).status == "ambiguous"
    assert match_title("Night Shift (UK)", CAT).title_id == "c3"
    assert match_title("Night Shift US S02E04", CAT).title_id == "c4"


def test_typo_is_fuzzy():
    r = match_title("Quiet Feilds", CAT)
    assert r.status == "fuzzy" and r.title_id == "c8"


def test_unknown_title_unmatched():
    assert match_title("Midnight Garden", CAT).status == "unmatched"


def test_example_run_has_no_wrong_matches():
    rows, results, _ = run(EX / "catalog.csv", EX / "log.csv")
    for r, m in zip(rows, results):
        if m.title_id:
            assert m.title_id == r["expected_id"], r
    text = report(rows, results)
    assert "wrong among resolved: 0" in text


def test_normalization_beats_exact_only():
    rows, results, _ = run(EX / "catalog.csv", EX / "log.csv")
    exact = sum(m.status == "exact" for m in results)
    resolved = sum(bool(m.title_id) for m in results)
    assert resolved > exact


def test_duplicate_exact_title_is_not_silently_resolved():
    # regression: a dict index let the last catalog row win for "Harbor Lights"
    r = match_title("Harbor Lights", CAT)
    assert r.status == "ambiguous" and r.title_id == ""


def test_trailing_repeat_word():
    assert match_title("Quiet Fields Repeat", CAT).title_id == "c8"
