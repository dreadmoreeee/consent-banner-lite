"""Shared fixtures: the local demo servers and a Chromium browser.

No internet: the first party is http://127.0.0.1:<random port> and the fake
tracker is http://localhost:<another random port>, two different sites.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("cbl_serve_demo", REPO / "examples" / "serve_demo.py")
serve_demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(serve_demo)


@pytest.fixture(scope="session")
def demo():
    d = serve_demo.Demo()
    yield d
    d.close()


@pytest.fixture(scope="session")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as err:  # pragma: no cover - depends on the machine
            pytest.skip(f"Chromium cannot start: {err}")
        yield b
        b.close()


class Visit:
    """One fresh browser profile, with every request recorded."""

    def __init__(self, browser, demo):
        self.demo = demo
        self.context = browser.new_context()
        self.requests: list[str] = []
        self.context.on("request", lambda r: self.requests.append(r.url))
        self.page = self.context.new_page()
        demo.tracker_hits.clear()

    def open(self, query: str = "", path: str = "/tests/pages/test.html"):
        self.page.goto(self.demo.site_url + path + (("?" + query) if query else ""), wait_until="load")
        self.page.wait_for_timeout(150)
        return self.page

    def reload(self):
        self.page.reload(wait_until="load")
        self.page.wait_for_timeout(150)
        return self.page

    def tracker_requests(self) -> list[str]:
        return [u for u in self.requests if u.startswith(self.demo.tracker_url)]

    def cookies(self) -> dict[str, str]:
        return {c["name"]: c["value"] for c in self.context.cookies()}

    def banner_visible(self) -> bool:
        return self.page.locator("#cbl-consent").is_visible()


@pytest.fixture
def visit(browser, demo):
    v = Visit(browser, demo)
    yield v
    v.context.close()
