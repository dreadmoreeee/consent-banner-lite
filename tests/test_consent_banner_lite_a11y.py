"""Keyboard use, focus handling, ARIA wiring, contrast and reduced motion."""


def focused(page):
    return page.evaluate("document.activeElement.getAttribute('data-cbl') || document.activeElement.id || document.activeElement.className")


def test_dialog_labels_and_initial_focus(visit):
    page = visit.open()
    d = page.locator("#cbl-consent")
    assert d.get_attribute("aria-labelledby") == "cbl-title"
    assert d.get_attribute("aria-describedby") == "cbl-desc"
    assert d.get_attribute("aria-modal") == "false"
    assert "We use necessary cookies" in page.locator("#cbl-desc").inner_text()
    assert focused(page) == "cbl-consent"


def test_keyboard_only_reject(visit):
    page = visit.open()
    page.keyboard.press("Tab")
    assert focused(page) == "cbl__link"
    page.keyboard.press("Tab")
    assert focused(page) == "accept"
    page.keyboard.press("Tab")
    assert focused(page) == "reject"
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    assert not visit.banner_visible()
    assert page.evaluate("ConsentBannerLite.getConsent().analytics") is False


def test_keyboard_settings_and_escape(visit):
    page = visit.open()
    page.locator('#cbl-consent [data-cbl="settings"]').focus()
    page.keyboard.press("Enter")
    assert page.locator("#cbl-prefs").is_visible()
    page.keyboard.press("Escape")
    assert not page.locator("#cbl-prefs").is_visible()
    assert focused(page) == "settings"
    assert visit.banner_visible()
    page.keyboard.press("Space")
    assert page.locator("#cbl-prefs").is_visible()
    page.locator("#cbl-c-marketing").focus()
    page.keyboard.press("Space")
    assert page.locator("#cbl-c-marketing").is_checked()
    page.keyboard.press("Tab")
    assert focused(page) == "cbl-c-preferences"
    page.locator('#cbl-consent [data-cbl="save"]').focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    c = page.evaluate("ConsentBannerLite.getConsent()")
    assert (c["analytics"], c["marketing"], c["preferences"]) == (False, True, False)


def test_not_a_focus_trap(visit):
    page = visit.open()
    page.locator('#cbl-consent [data-cbl="settings"]').focus()
    page.keyboard.press("Tab")
    assert focused(page) == "before"
    assert visit.banner_visible()


def test_focus_restored_to_settings_link(visit):
    page = visit.open()
    page.click('#cbl-consent [data-cbl="reject"]')
    page.focus("#settings-link")
    page.keyboard.press("Enter")
    assert visit.banner_visible()
    assert focused(page) == "cbl-consent"
    page.click('#cbl-consent [data-cbl="save"]')
    assert focused(page) == "settings-link"


def test_visible_focus_ring(visit):
    page = visit.open()
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    assert focused(page) == "accept"
    style = page.evaluate("[getComputedStyle(document.activeElement).outlineStyle, getComputedStyle(document.activeElement).outlineWidth]")
    assert style == ["solid", "3px"]


def _lum(rgb):
    out = []
    for v in rgb:
        v = v / 255
        out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def _ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _rgb(s):
    return [int(float(x)) for x in s[s.index("(") + 1 : s.index(")")].split(",")[:3]]


def test_contrast_aa_light_and_dark(browser, demo):
    for scheme in ("light", "dark"):
        ctx = browser.new_context(color_scheme=scheme)
        page = ctx.new_page()
        page.goto(demo.site_url + "/tests/pages/test.html", wait_until="load")
        page.click('#cbl-consent [data-cbl="settings"]')
        pairs = page.evaluate("""() => {
          const s = q => getComputedStyle(document.querySelector(q));
          const bg = s('#cbl-consent').backgroundColor;
          return [[s('#cbl-desc').color, bg], [s('.cbl__link').color, bg], [s('.cbl__cat span').color, bg],
                  [s('[data-cbl=accept]').color, s('[data-cbl=accept]').backgroundColor],
                  [s('[data-cbl=reject]').color, s('[data-cbl=reject]').backgroundColor]];
        }""")
        for fg, bg in pairs:
            assert _ratio(_rgb(fg), _rgb(bg)) >= 4.5, (scheme, fg, bg)
        ctx.close()


def test_reduced_motion_disables_animation(browser, demo):
    ctx = browser.new_context(reduced_motion="reduce")
    page = ctx.new_page()
    page.goto(demo.site_url + "/tests/pages/test.html", wait_until="load")
    assert page.evaluate("getComputedStyle(document.getElementById('cbl-consent')).animationName") == "none"
    ctx.close()
