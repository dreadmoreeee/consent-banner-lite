"""English, French and Spanish texts, picked from <html lang> or the lang option."""

import pytest

EN = ("We use cookies", ["Accept all", "Reject all", "Settings"], "Cookie settings")
FR = ("Nous utilisons des témoins (cookies)", ["Tout accepter", "Tout refuser", "Paramètres"],
      "Paramètres des témoins")
ES = ("Usamos cookies", ["Aceptar todo", "Rechazar todo", "Configuración"], "Configuración de cookies")

CASES = [
    ("htmllang=en", "en", EN),
    ("htmllang=fr-CA", "fr", FR),
    ("htmllang=es", "es", ES),
    ("htmllang=fr&lang=es", "es", ES),
    ("htmllang=de", "en", EN),
]


@pytest.mark.parametrize("query,lang,expected", CASES)
def test_texts(visit, query, lang, expected):
    title, buttons, link = expected
    page = visit.open(query)
    assert page.locator("#cbl-consent").get_attribute("lang") == lang
    assert page.locator("#cbl-title").inner_text() == title
    got = [page.locator(f'#cbl-consent [data-cbl="{n}"]').inner_text() for n in ("accept", "reject", "settings")]
    assert got == buttons
    assert page.locator("#settings-link").inner_text() == link


def test_french_reject_works(visit):
    page = visit.open("htmllang=fr")
    page.get_by_role("button", name="Tout refuser").click()
    page.wait_for_timeout(200)
    assert page.evaluate("ConsentBannerLite.getConsent().analytics") is False
    assert visit.tracker_requests() == []


def test_second_init_is_ignored(visit):
    page = visit.open()
    assert page.evaluate("ConsentBannerLite.init({lang: 'fr'}) === ConsentBannerLite")
    assert page.locator("#cbl-title").inner_text() == "We use cookies"


def test_custom_language_categories_and_cookie(visit):
    page = visit.open(path="/tests/pages/custom.html")
    assert page.locator("#cbl-consent").get_attribute("lang") == "de"
    assert page.locator("#cbl-title").inner_text() == "Wir verwenden Cookies"
    assert page.locator('#cbl-consent [data-cbl="accept"]').inner_text() == "Alle akzeptieren"
    # Keys that are not translated fall back to English.
    assert page.locator('#cbl-consent [data-cbl="reject"]').inner_text() == "Reject all"
    # A link that already has text keeps it.
    assert page.locator("#settings-link").inner_text() == "Cookies"
    page.click('#cbl-consent [data-cbl="settings"]')
    assert page.locator("[data-cat]").count() == 1
    page.click('#cbl-consent [data-cbl="accept"]')
    c = page.evaluate("ConsentBannerLite.getConsent()")
    assert c["analytics"] is True and c["marketing"] is False and c["preferences"] is False
    cookie = next(c for c in visit.context.cookies() if c["name"] == "site_consent")
    days = (cookie["expires"] - page.evaluate("Date.now() / 1000")) / 86400
    assert 29 < days <= 30.01
