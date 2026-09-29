"""Google Consent Mode v2 calls, recorded through a stub gtag()."""

KEYS = ("ad_storage", "ad_user_data", "ad_personalization", "analytics_storage")


def test_default_denied_then_update_on_accept(visit):
    page = visit.open("gtag=1")
    calls = page.evaluate("gtagCalls")
    assert len(calls) == 1
    name, kind, params = calls[0]
    assert (name, kind) == ("consent", "default")
    assert all(params[k] == "denied" for k in KEYS)
    assert params["security_storage"] == "granted"
    assert params["wait_for_update"] == 500
    page.click('#cbl-consent [data-cbl="accept"]')
    name, kind, params = page.evaluate("gtagCalls")[-1]
    assert (name, kind) == ("consent", "update")
    assert all(params[k] == "granted" for k in KEYS)


def test_update_per_category_and_stored_default(visit):
    page = visit.open("gtag=1")
    page.evaluate("ConsentBannerLite.set({analytics: true})")
    _, kind, params = page.evaluate("gtagCalls")[-1]
    assert kind == "update"
    assert params["analytics_storage"] == "granted"
    assert params["ad_storage"] == params["ad_user_data"] == params["ad_personalization"] == "denied"
    page = visit.reload()
    calls = page.evaluate("gtagCalls")
    assert len(calls) == 1
    _, kind, params = calls[0]
    assert kind == "default" and params["analytics_storage"] == "granted" and params["ad_storage"] == "denied"
    assert "wait_for_update" not in params


def test_reject_sends_denied_update(visit):
    page = visit.open("gtag=1")
    page.click('#cbl-consent [data-cbl="reject"]')
    _, kind, params = page.evaluate("gtagCalls")[-1]
    assert kind == "update" and all(params[k] == "denied" for k in KEYS)


def test_no_gtag_no_error(visit):
    errors = []
    visit.page.on("pageerror", lambda e: errors.append(str(e)))
    page = visit.open()
    page.click('#cbl-consent [data-cbl="accept"]')
    page.wait_for_timeout(200)
    assert errors == []
