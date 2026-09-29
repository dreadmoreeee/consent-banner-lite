"""First visit, accept, reject, persistence, version bump and reset()."""

import json
from urllib.parse import unquote

NOTHING = {"analytics": 0, "marketing": 0, "preferences": 0, "combo": 0}
EVERYTHING = {"analytics": 1, "marketing": 1, "preferences": 1, "combo": 1}


def click(page, name):
    page.click(f'#cbl-consent [data-cbl="{name}"]')
    page.wait_for_timeout(300)


def test_banner_shows_on_first_visit_and_nothing_runs(visit):
    page = visit.open()
    assert visit.banner_visible()
    assert page.locator("#cbl-consent").get_attribute("role") == "dialog"
    assert page.locator("#cbl-title").inner_text() == "We use cookies"
    assert page.evaluate("ran") == NOTHING
    assert page.evaluate("ConsentBannerLite.getConsent()") is None
    assert visit.tracker_requests() == []
    assert page.locator("iframe").get_attribute("src") is None
    assert "cbl_consent" not in visit.cookies()


def test_three_choices_have_equal_weight(visit):
    page = visit.open()
    boxes = [page.locator(f'#cbl-consent [data-cbl="{n}"]') for n in ("accept", "reject", "settings")]
    js = "e => { const s = getComputedStyle(e); return [s.backgroundColor, s.color, s.fontSize, s.fontWeight, s.borderTopWidth]; }"
    styles = [b.evaluate(js) for b in boxes]
    assert styles[0] == styles[1] == styles[2]
    assert len({round(b.bounding_box()["height"]) for b in boxes}) == 1


def test_reject_never_runs_blocked_scripts_or_contacts_tracker(visit):
    page = visit.open()
    click(page, "reject")
    assert not visit.banner_visible()
    assert page.evaluate("ran") == NOTHING
    page = visit.reload()
    page.wait_for_timeout(500)
    assert not visit.banner_visible()
    assert page.evaluate("ran") == NOTHING
    assert page.evaluate("window.demoTrackerRuns") is None
    assert visit.tracker_requests() == []
    assert visit.demo.tracker_hits == []
    assert page.locator('script[type="text/plain"]').count() == 5
    c = page.evaluate("ConsentBannerLite.getConsent()")
    assert c["necessary"] is True and not c["analytics"] and not c["marketing"] and not c["preferences"]


def test_accept_runs_scripts_once_and_persists(visit):
    page = visit.open()
    click(page, "accept")
    page.wait_for_function("window.demoTrackerRuns === 1")
    page.wait_for_timeout(200)
    assert page.evaluate("ran") == EVERYTHING
    assert page.locator("iframe").get_attribute("src") == "/tests/pages/embed.html"
    for _ in range(30):
        if any("/collect?" in h for h in visit.demo.tracker_hits):
            break
        page.wait_for_timeout(100)
    assert any("/collect?" in h for h in visit.demo.tracker_hits)
    assert "_da_id" in visit.cookies()
    assert page.evaluate("changes.length") == 1
    stored = json.loads(unquote(visit.cookies()["cbl_consent"]))
    assert stored["v"] == "1" and stored["c"] == {"analytics": 1, "marketing": 1, "preferences": 1}
    page = visit.reload()
    page.wait_for_function("window.demoTrackerRuns === 1")
    assert not visit.banner_visible()
    assert page.evaluate("ran") == EVERYTHING


def test_consent_cookie_attributes(visit):
    page = visit.open()
    click(page, "reject")
    cookie = next(c for c in visit.context.cookies() if c["name"] == "cbl_consent")
    assert cookie["path"] == "/" and cookie["sameSite"] == "Lax" and cookie["domain"] == "127.0.0.1"
    days = (cookie["expires"] - page.evaluate("Date.now() / 1000")) / 86400
    assert 179 < days <= 180.01


def test_version_bump_asks_again(visit):
    page = visit.open("v=1")
    click(page, "accept")
    visit.open("v=1")
    assert not visit.banner_visible()
    page = visit.open("v=2")
    assert visit.banner_visible()
    assert page.evaluate("ConsentBannerLite.getConsent()") is None
    assert page.evaluate("ran.analytics") == 0


def test_reset_clears_choice_and_shows_banner(visit):
    page = visit.open()
    click(page, "reject")
    assert "cbl_consent" in visit.cookies()
    page.evaluate("ConsentBannerLite.reset()")
    assert visit.banner_visible()
    assert page.evaluate("ConsentBannerLite.getConsent()") is None
    assert "cbl_consent" not in visit.cookies()
    visit.reload()
    assert visit.banner_visible()


def test_minified_build_behaves_the_same(visit):
    page = visit.open("min=1")
    assert page.evaluate("typeof ConsentBannerLite.init") == "function"
    assert visit.banner_visible()
    click(page, "reject")
    visit.reload()
    assert visit.tracker_requests() == []
    page.evaluate("ConsentBannerLite.reset()")
    click(page, "accept")
    page.wait_for_function("window.demoTrackerRuns === 1")
    assert page.evaluate("ran.analytics") == 1
