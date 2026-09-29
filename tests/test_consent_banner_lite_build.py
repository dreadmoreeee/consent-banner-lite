"""Source rules, the minified build and its size."""

import gzip
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("cbl_minify", REPO / "minify.py")
minify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(minify)

SHIPPED = ("consent-banner-lite.js", "consent-banner-lite.css", "consent-banner-lite.min.js", "consent-banner-lite.min.css")


def test_sources_are_ascii():
    for name in SHIPPED + ("minify.py",):
        (REPO / name).read_bytes().decode("ascii")


def test_minified_files_are_up_to_date():
    for name, text in minify.build().items():
        assert (REPO / name).read_text(encoding="ascii") == text, f"run python minify.py ({name})"


def test_size_budget():
    js = (REPO / "consent-banner-lite.min.js").read_bytes()
    assert len(gzip.compress(js, 9)) < 6 * 1024


def test_no_network_requests_of_its_own():
    for name in SHIPPED:
        src = (REPO / name).read_text(encoding="ascii")
        for needle in ("fetch(", "XMLHttpRequest", "sendBeacon", "Image(", "http://", "https://", "@import", "url(", "@font-face"):
            assert needle not in src, (name, needle)


def test_minifier_keeps_meaningful_spaces():
    assert minify.minify_js("var a = b + +c; // x\nreturn  x;") == "var a=b+ +c;return x;\n"
    assert minify.minify_js("s = 'a  // b';/* c */") == "s='a  // b';\n"
    assert minify.minify_css("a  b { color: red ; }\n@media (x: y) and (z) { p { m: 0 } }") == \
        "a b{color:red}\n".rstrip("\n") + "@media (x:y) and (z){p{m:0}}\n"
