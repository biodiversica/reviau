"""Every interface language carries every string, with the same placeholders."""

import json
import re
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "src" / "reviau" / "locales"


def flat(tree, prefix=""):
    out = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            out.update(flat(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


def load(name):
    return flat(json.loads((LOCALES / name).read_text(encoding="utf-8")))


def test_both_languages_have_the_same_strings():
    en, pt = load("en.json"), load("pt-BR.json")
    assert sorted(set(en) - set(pt)) == []
    assert sorted(set(pt) - set(en)) == []


def test_placeholders_match_between_languages():
    en, pt = load("en.json"), load("pt-BR.json")
    holes = re.compile(r"\{(\w+)\}")
    for key in en:
        if key.startswith("meta."):
            continue
        assert set(holes.findall(en[key])) == set(holes.findall(pt[key])), key
