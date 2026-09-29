# consent-banner-lite

A cookie consent banner for small-business sites, in **one JavaScript file and one CSS file**, with no dependencies and no build step. Made for Canada (Quebec Law 25, PIPEDA) and the EU.

Why: most small sites I audit have a banner, but Google Analytics or the Meta pixel still fire before anyone clicks it, and "Reject" is a grey link hidden under a big blue "Accept". This banner blocks the tags until the visitor chooses, and makes saying no exactly as easy as saying yes.

- **Scripts wait for consent.** Tag them `type="text/plain" data-consent="analytics"`; they only run (cloned into real `<script>` elements) once that category is granted. Iframes work too, with `data-src`.
- **Equal-weight choices.** "Accept all", "Reject all" and "Settings" are the same button, same size, same colour. Settings has per-category switches: necessary (always on), analytics, marketing, preferences.
- **Reject means no.** Refused categories never run, and known tracker cookies they may have left (`_ga*`, `_gid`, `_fbp`, `_gcl_*`...) are deleted, with matching localStorage keys.
- **Google Consent Mode v2.** If `gtag` exists, it sends `consent default` (denied until a choice) and `consent update` with `ad_storage`, `analytics_storage`, `ad_user_data` and `ad_personalization`.
- **English, French and Spanish**, picked from `<html lang>` (`fr-CA` gives French), or set with `lang`. French says "témoins", as in Quebec.
- **Remembers the choice** in a first-party cookie, with a `version`: change it when your policy changes and everyone is asked again.
- **Accessible.** `role="dialog"` with `aria-labelledby`/`aria-describedby`, focus moved into the banner and given back afterwards, visible focus ring, AA contrast in light and dark, no focus trap (it is a bottom bar, the page stays usable), `prefers-reduced-motion` respected.
- **No network requests of its own**, no fonts, no CDN. 4.7 KB minified and gzipped.

## Install

Copy two files into your site:

```html
<link rel="stylesheet" href="/consent-banner-lite.min.css">
<script src="/consent-banner-lite.min.js"></script>
```

The readable `consent-banner-lite.js` and `consent-banner-lite.css` are the sources. `python minify.py` rebuilds the `.min` files (standard library only).

## Usage

```html
<!-- Google tag with Consent Mode: define gtag before the banner -->
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
</script>

<!-- Blocked until the visitor accepts analytics -->
<script type="text/plain" data-consent="analytics" async
        src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>
<script type="text/plain" data-consent="analytics">
  gtag('js', new Date()); gtag('config', 'G-XXXXXXX');
</script>

<!-- Blocked until the visitor accepts marketing -->
<script type="text/plain" data-consent="marketing" src="/js/meta-pixel.js"></script>
<iframe data-consent="marketing" data-src="https://www.youtube-nocookie.com/embed/ID" title="Video"></iframe>

<!-- Reopen the settings later (empty element gets "Cookie settings" in the page language) -->
<a href="#" data-consent-settings></a>

<link rel="stylesheet" href="/consent-banner-lite.min.css">
<script src="/consent-banner-lite.min.js"></script>
<script>
  ConsentBannerLite.init({ version: '2026-09', policyUrl: '/privacy' });
</script>
```

`data-consent` can list several categories (`"analytics marketing"`); all must be granted. Other attributes (`async`, `defer`, `id`, `nonce`...) are copied to the real script; `data-type="module"` sets its type.

## Options

| Option | Default | Meaning |
|---|---|---|
| `version` | `'1'` | Policy version stored with the choice. A different value asks again. |
| `categories` | `['analytics','marketing','preferences']` | Categories shown in Settings. Others stay refused. |
| `lang` | from `<html lang>` | `'en'`, `'fr'`, `'es'` or any language you add in `texts`. Unknown falls back to English. |
| `texts` | | Per-language overrides or new languages, e.g. `{ fr: { title: '...' }, de: {...} }`. Missing keys come from English. |
| `policyUrl` | `''` | Adds a "Privacy policy" link to the text. |
| `cookieName` | `'cbl_consent'` | Name of the first-party cookie that stores the choice. |
| `cookieDays` | `180` | How long the choice is kept. |
| `cookieDomain` | `''` | Set to `.example.ca` to share the choice across subdomains. |
| `consentMode` | `true` | Send Google Consent Mode v2 calls when `gtag` exists. |
| `waitForUpdate` | `500` | `wait_for_update` (ms) in the first `consent default` call. `0` to omit. |
| `reloadOnRevoke` | `true` | Reload the page when a category whose scripts already ran is withdrawn, since running code cannot be unloaded. |
| `trackerCookies` | | Extra name patterns to delete per category, e.g. `{ analytics: ['_pk_*'] }`. A trailing `*` matches any suffix. Added to the built-in list. |

Consent Mode mapping: `analytics` gives `analytics_storage`; `marketing` gives `ad_storage`, `ad_user_data` and `ad_personalization`; `preferences` gives `functionality_storage` and `personalization_storage`; `security_storage` is always granted.

Theme it with CSS custom properties on `.cbl`: `--cbl-bg`, `--cbl-fg`, `--cbl-muted`, `--cbl-border`, `--cbl-btn-bg`, `--cbl-btn-fg`, `--cbl-btn-hover`, `--cbl-link`, `--cbl-focus`, `--cbl-radius`, `--cbl-font`, `--cbl-size`, `--cbl-max-width`, `--cbl-z`. Check the contrast of your colours.

## API

- `ConsentBannerLite.init(options)`: once per page; later calls are ignored.
- `ConsentBannerLite.open()`: show the banner with the settings expanded.
- `ConsentBannerLite.getConsent()`: `null` before a choice, else `{necessary: true, analytics, marketing, preferences, version, timestamp}`.
- `ConsentBannerLite.onChange(cb)`: called with the new consent after every choice; returns a function that unsubscribes. The same object is sent as a `consentbannerlite:change` event on `document`.
- `ConsentBannerLite.reset()`: forget the choice, delete tracker cookies and show the banner again.
- `ConsentBannerLite.acceptAll()`, `rejectAll()`, `set({analytics: true})`: record a choice from your own UI.

## Measured result

Checked with my scanner, [consent-tracker-scan](https://github.com/dreadmoreeee/consent-tracker-scan), which loads a page as a first-time visitor, then clicks "Reject" and reloads. `examples/serve_demo.py` serves a demo bakery shop on `127.0.0.1:8411` and a fake analytics tracker on `localhost:8412`, two different sites for the browser. Nothing leaves the machine.

With the tracker loaded through the banner (`examples/demo-shop/index.html`):

```
$ python examples/serve_demo.py            # terminal 1
$ python -m consent_tracker_scan http://127.0.0.1:8411/examples/demo-shop/ --reject \
      --extra-trackers examples/demo-trackers.json --md gated.md
scanning http://127.0.0.1:8411/examples/demo-shop/
rejecting consent on http://127.0.0.1:8411/examples/demo-shop/
1 page(s): 0 high, 0 medium, 0 low; 0 cookie(s), 0 storage key(s), 0 third-party host(s); banner: generic; after reject: ok
$ echo $?
0
```

```
## After clicking Reject

Clicked "Reject all" (text), then reloaded the page.

OK: no tracking request and no new tracking cookie after reject.
```

Counter-example: the same page and the same banner, but the tracker in a plain `<script src>` tag (`examples/demo-shop/ungated.html`):

```
$ python -m consent_tracker_scan http://127.0.0.1:8411/examples/demo-shop/ungated.html --reject \
      --extra-trackers examples/demo-trackers.json --md ungated.md
scanning http://127.0.0.1:8411/examples/demo-shop/ungated.html
rejecting consent on http://127.0.0.1:8411/examples/demo-shop/ungated.html
1 page(s): 2 high, 0 medium, 0 low; 1 cookie(s), 0 storage key(s), 1 third-party host(s); banner: generic; after reject: fail
$ echo $?
1
```

```
## Findings

- **HIGH** Demo Analytics (analytics) loaded before consent. 2 request(s) to localhost.
- **HIGH** Third-party cookie da_uid set by Demo Analytics (analytics) before consent. domain localhost, expires 2027-09-29T08:43:45Z.

## After clicking Reject

Clicked "Reject all" (text), then reloaded the page.

FAIL: tracking continues after the visitor said no.

| Host | Tracker | Category | Requests |
|---|---|---|---|
| localhost | Demo Analytics | analytics | 2 |
```

A banner alone proves nothing; the tags have to wait for it.

```
$ python minify.py
consent-banner-lite.min.js: 12979 bytes, 4774 bytes gzipped
consent-banner-lite.min.css: 2395 bytes, 1023 bytes gzipped

$ python -m pytest -q -p no:cacheprovider --import-mode=importlib consent-banner-lite
..........................................
42 passed in 25.63s
```

The tests drive headless Chromium (Playwright) against local `http.server` instances on random ports, with the fake tracker on a second origin. They cover: banner on first visit; reject never runs blocked scripts and sends nothing to the tracker host; accept runs them once; the choice survives a reload; a version bump asks again; per-category settings; withdrawing consent; Consent Mode calls through a stub `gtag`; keyboard-only use, focus return and no focus trap; AA contrast in light and dark; English, French and Spanish texts; `reset()`; tracker cookies deleted on reject; the minified build. No internet is used.

## Limitations

- It blocks what you tag. A tracker left in a plain `<script>` tag, added by a plugin, or injected by a tag manager that is itself not gated still runs. Scan your site afterwards.
- Cookies set by other domains (third-party cookies such as `da_uid` above, or Meta's on `facebook.com`) cannot be deleted from your page; they are simply never created if the tag never runs. Cookies set with a path other than `/` are not reached.
- Scripts that already ran cannot be unloaded, which is why withdrawing consent reloads the page.
- One bottom-bar layout. No geo-targeting: everyone gets the same opt-in banner, which is the safe choice for Quebec and the EU.
- The choice is stored per browser; there is no server-side consent log. If you need proof of consent records, add your own logging in `onChange`.
- The texts are a starting point. Your privacy policy and your categories have to describe what your site really does. This is not legal advice.

## Author

Marvin Palencia, founder of [DeMark Studio](https://demarkstudio.ca), Miramichi, New Brunswick, Canada. Portfolio: [marvin.demarkstudio.ca](https://marvin.demarkstudio.ca)

MIT License.
