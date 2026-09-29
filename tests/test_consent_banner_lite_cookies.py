"""Known tracker cookies are deleted when their category is refused."""

TRACKERS = {"_ga", "_ga_ABC123", "_gid", "_fbp", "_gcl_au"}


def seed(visit):
    url = visit.demo.site_url + "/"
    visit.context.add_cookies([{"name": n, "value": "x", "url": url} for n in sorted(TRACKERS) + ["keep_me"]])


def test_reject_deletes_tracker_cookies(visit):
    page = visit.open()
    seed(visit)
    assert TRACKERS <= set(visit.cookies())
    page.click('#cbl-consent [data-cbl="reject"]')
    names = set(visit.cookies())
    assert not names & TRACKERS
    assert "keep_me" in names and "cbl_consent" in names


def test_before_any_choice_tracker_cookies_are_removed(visit):
    seed(visit)
    visit.open()
    names = set(visit.cookies())
    assert not names & TRACKERS
    assert "keep_me" in names


def test_accept_keeps_them(visit):
    page = visit.open()
    page.click('#cbl-consent [data-cbl="accept"]')
    seed(visit)
    visit.reload()
    assert TRACKERS <= set(visit.cookies())


def test_partial_choice_deletes_only_refused_category(visit):
    page = visit.open()
    page.evaluate("ConsentBannerLite.set({analytics: true})")
    seed(visit)
    visit.reload()
    names = set(visit.cookies())
    assert {"_ga", "_ga_ABC123", "_gid"} <= names
    assert not names & {"_fbp", "_gcl_au"}
