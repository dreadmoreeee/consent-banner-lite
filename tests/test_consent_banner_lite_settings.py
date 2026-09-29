"""Per-category choices, the settings link, and withdrawing consent."""


def test_settings_panel_per_category(visit):
    page = visit.open()
    settings = page.locator('#cbl-consent [data-cbl="settings"]')
    assert settings.get_attribute("aria-expanded") == "false"
    assert not page.locator("#cbl-prefs").is_visible()
    settings.click()
    assert settings.get_attribute("aria-expanded") == "true"
    assert page.locator("#cbl-prefs").is_visible()
    necessary = page.locator("#cbl-c-necessary")
    assert necessary.is_checked() and necessary.is_disabled()
    for cat in ("analytics", "marketing", "preferences"):
        assert not page.locator(f"#cbl-c-{cat}").is_checked()
    page.check("#cbl-c-analytics")
    page.check("#cbl-c-preferences")
    page.click('#cbl-consent [data-cbl="save"]')
    page.wait_for_function("window.demoTrackerRuns === 1")
    assert page.evaluate("ran") == {"analytics": 1, "marketing": 0, "preferences": 1, "combo": 0}
    c = page.evaluate("ConsentBannerLite.getConsent()")
    assert (c["analytics"], c["marketing"], c["preferences"]) == (True, False, True)
    page = visit.reload()
    assert page.evaluate("ran") == {"analytics": 1, "marketing": 0, "preferences": 1, "combo": 0}
    assert page.locator("iframe").get_attribute("src") is None


def test_settings_link_reopens_with_current_choice(visit):
    page = visit.open()
    link = page.locator("#settings-link")
    assert link.inner_text() == "Cookie settings"
    page.click('#cbl-consent [data-cbl="reject"]')
    assert not visit.banner_visible()
    link.click()
    assert visit.banner_visible()
    assert page.locator("#cbl-prefs").is_visible()
    assert not page.locator("#cbl-c-analytics").is_checked()
    page.check("#cbl-c-marketing")
    page.click('#cbl-consent [data-cbl="save"]')
    page.wait_for_timeout(200)
    assert page.evaluate("ran") == {"analytics": 0, "marketing": 1, "preferences": 0, "combo": 0}
    assert visit.tracker_requests() == []


def test_open_api_and_onchange(visit):
    page = visit.open()
    page.evaluate("ConsentBannerLite.acceptAll()")
    assert not visit.banner_visible()
    page.evaluate("ConsentBannerLite.open()")
    assert visit.banner_visible()
    assert page.locator("#cbl-c-analytics").is_checked()
    got = page.evaluate("changes")
    assert len(got) == 1 and got[0]["analytics"] is True and got[0]["version"] == "1"


def test_unsubscribe_and_dom_event(visit):
    page = visit.open()
    page.evaluate("""() => {
      window.seen = [];
      const off = ConsentBannerLite.onChange(c => seen.push('cb'));
      document.addEventListener('consentbannerlite:change', e => seen.push('event:' + e.detail.marketing));
      ConsentBannerLite.rejectAll();
      off();
      ConsentBannerLite.acceptAll();
    }""")
    assert page.evaluate("seen") == ["cb", "event:false", "event:true"]


def test_withdrawing_consent_reloads_and_removes_tracker_data(visit):
    page = visit.open()
    page.click('#cbl-consent [data-cbl="accept"]')
    page.wait_for_function("window.demoTrackerRuns === 1")
    page.wait_for_timeout(200)
    assert "_da_id" in visit.cookies()
    assert page.evaluate("localStorage.getItem('_da_last_visit')") is not None
    page.click("#settings-link")
    page.uncheck("#cbl-c-analytics")
    with page.expect_navigation():
        page.click('#cbl-consent [data-cbl="save"]')
    page.wait_for_load_state("load")
    page.wait_for_timeout(300)
    assert page.evaluate("window.demoTrackerRuns") is None
    assert page.evaluate("ran.analytics") == 0 and page.evaluate("ran.marketing") == 1
    assert "_da_id" not in visit.cookies()
    assert page.evaluate("localStorage.getItem('_da_last_visit')") is None
