"""Light and dark: one palette, pinned or following the system."""

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "src" / "segment_reviewer" / "web"
CSS = (WEB / "styles.css").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")
APP = (WEB / "app.js").read_text(encoding="utf-8")

ROOT = re.search(r"^:root \{(.*?)^\}", CSS, re.S | re.M).group(1)
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")


def test_every_colour_token_names_both_themes():
    """One palette, not two that can drift apart."""
    tokens = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", ROOT))
    colours = {k: v for k, v in tokens.items() if COLOUR.search(v)}
    assert colours, "no colour tokens found"
    for name, value in colours.items():
        assert value.startswith("light-dark("), name


def test_colours_live_only_in_the_tokens():
    """A colour written outside :root would not follow the theme."""
    outside = CSS.replace(ROOT, "")
    assert not COLOUR.search(re.sub(r"/\*.*?\*/", "", outside, flags=re.S))


def test_no_second_palette_for_dark_mode():
    assert "prefers-color-scheme" not in CSS


def test_a_pinned_theme_sets_the_colour_scheme():
    assert "color-scheme: light dark;" in ROOT
    assert ':root[data-theme="light"] { color-scheme: light; }' in CSS
    assert ':root[data-theme="dark"] { color-scheme: dark; }' in CSS


def test_a_pinned_theme_is_applied_before_the_first_paint():
    """In <head>, with the key app.js stores the choice under."""
    head = HTML.split("</head>")[0]
    assert "localStorage.getItem('segrev.theme')" in head
    assert "dataset.theme" in head
    assert "const THEME_KEY = 'segrev.theme';" in APP
