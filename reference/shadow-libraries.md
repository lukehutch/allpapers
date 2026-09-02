# Shadow libraries — the last rung

Sci-Hub, Anna's Archive, LibGen and Z-Library sit at the **bottom** of the ladder,
below Google Scholar and web search. They hold unlicensed copies. Reach for them
only when every legitimate route in `ladder.md` has returned nothing, and then
under the same three constraints that already govern Sci-Hub in this skill:

1. **Verification only.** A file fetched here exists to check a quotation, a page
   number or an equation. It is not a distribution copy.
2. **Never committed.** Keep it in the scratchpad or another ignored path. Never
   in `verification/source/`, never in a public repo. This is not merely policy:
   arXiv's own terms of use forbid serving e-prints from your servers, and the
   same reasoning applies with far more force here.
3. **Record the attempt, not the artifact.** `bib.md` gets the source URL and the
   fact that the copy was consulted. The bytes stay out of the record.

Everything below was probed live on **2026-08-26**. Treat the status of any
individual domain as perishable; treat the *shapes* — the APIs, the traps — as
durable.

---

## The first rule: HTTP 200 is not evidence of a working mirror

Two independent traps were measured, and both return a perfectly healthy status
code:

- **`sci-hub.tf` returns 200 and redirects offsite** to
  `https://arcade.now/lp1/play?subid=sci-hub.tf…` — an ad/scam landing page that
  has nothing to do with Sci-Hub. `sci-hub.hkvisa.net` likewise redirects to
  `sci-hub.usualwant.com`.
- **`yqrii5.org` and `wbsg8v.xyz`** are listed as UP by SLUM and answer on 443,
  but every path returns a 129-byte nginx 403 reading:

  > Link expired or invalid. Get a new link on Anna's Archive (find the latest
  > official domain on Wikipedia) to continue downloading.

  They are Anna's Archive **signed-URL download edges**, not browsable mirrors.
  A token minted by Anna's Archive is the only thing they will serve.

So a liveness check must verify **content**, not status. `scripts/allpapers-mirrors`
does exactly that: it fetches each candidate, follows redirects, and requires the
final URL to still be on the expected host *and* the body to contain a marker
that only the real service serves.

## SLUM — the live status source

<https://open-slum.org/> ("Shadow Library Uptime Monitor") tracks the five
families below on a **5-minute** interval, built with
[FlatMonitor](https://github.com/BrianZbr/flatmonitor). It is the best available
answer to "which mirrors are up right now", and it is what `annas-mcp` consults
when `ANNAS_AUTO_BASE_URL=true`.

Its status vocabulary matters, because it is more honest than a binary up/down:

| SLUM status | Meaning | What it means for a script |
|---|---|---|
| `UP` | responds normally | usable — *if* the content check also passes |
| `PROTECTED` | behind a JS/anti-bot challenge | **not usable by `curl`**; browser only |
| `DEGRADED` | at least one check failed in the 5-minute window | retry, may be flapping |
| `DOWN` | not responding | skip |

`PROTECTED` is the single most useful signal here. It corresponds exactly to the
DDoS-Guard and Cloudflare interstitials measured below, and it is the reason
most of these services cannot be scripted at all.

**Caveats on SLUM itself:**

- **No API.** Probed `status.json`, `data.json`, `api/status`, `summary.json`,
  `monitors.json`, `checks.json`, `index.json`, `data/status.json`, `api.json` —
  every one returns the same 28,088-byte SPA 404 page. The 99 KB index links no
  `.json`, `.js` or `.csv`. The status is inlined in the HTML.
- **It is parseable anyway**, if you must: each entry is
  `<li class="domain-item-dense">` containing
  `<a href="https://sci-hub.ru" class="domain-link">` followed by a
  `<div class="mini-timeline-inline">` whose `<span>` classes are `up`,
  `protected`, `degraded` or `down`, oldest to newest. Prefer reading the page.
- **It disagrees with direct measurement.** On 2026-08-26 SLUM reported
  `sci-hub.st` as DEGRADED where a direct fetch got a flat 403, and `sci-hub.ru`
  as DEGRADED where the front page loaded fine. Use it to *narrow* the candidate
  list, then verify.
- **UP ≠ usable**, per `yqrii5.org` above.

The two mirror lists the user asked about — <https://www.sci-hub.pub/> and
<https://scihub.help/> — are strictly worse: no machine-readable output, and
stale (scihub.help was still captioned "Working December 2025"). Both list
`sci-hub.st`, `sci-hub.se` and `sci-hub.red` as working; all three were dead when
measured. Prefer SLUM, and verify regardless.

---

## Sci-Hub

Measured 2026-08-26. See `scihub.md` for the `scihub-cli` wrapper and its defects.

| Domain | Measured | Note |
|---|---|---|
| `sci-hub.ru` | front page loads | backend A |
| `sci-hub.su` | front page loads | backend A — identical counters to `.ru` and `.box` (54,503 users/hr, 1,832,856 daily reads), so one machine |
| `sci-hub.box` | front page loads | backend A |
| `sci-hub.al` | front page loads | backend B — identical text to `.mk` |
| `sci-hub.mk` | front page loads | backend B |
| `sci-hub.ren` | front page loads | |
| `sci-hub.ee` | front page loads, **has the search form** | best entry point measured |
| `sci-hub.wf` | JS browser check | not scriptable |
| `sci-hub.tf` | **200 → offsite scam redirect** | do not use |
| `sci-hub.hkvisa.net` | **redirects to `sci-hub.usualwant.com`** | do not use |
| `sci-hub.st` | 403 | listed as working by both published lists |
| `sci-hub.se` | NXDOMAIN | listed as working by both published lists |
| `sci-hub.red` | 504 | listed as working by both published lists |

The distinct counters prove there are only **two** live backends behind seven
working names — trying more domains after one fails buys you very little.

Manual PDF fallback, already recorded in `scihub.md` and still working: the
mirror article pages embed the file at
`https://sci.bban.top/pdf/<DOI>.pdf` — fetch that URL directly with the Chrome
User-Agent (`SKILL.md`). These mirrors serve an interstitial or a stub to anything
that does not look like a browser, so the agent string is load-bearing here.

**Keys / registration:** none. **Rate limits:** none published; the sites are
unreliable rather than rate-limited. **Paid tier:** none — but see `sci-net.xyz`
(Elbakyan's newer request-based site), which SLUM tracks as PROTECTED.

---

## LibGen — the one that actually has an API

**LibGen is the only shadow library here that is fully scriptable, needs no key,
and returns clean JSON.** This makes it the first shadow library to try, ahead of
Sci-Hub.

### Live domains (2026-08-26)

Working: `libgen.li`, `libgen.bz`, `libgen.vg` (identical 28,461-byte front page,
so one backend), `libgen.la`. `libgen.mx` redirects to `libgen.ac`, which 403s
the API. Dead: `libgen.rs`, `libgen.is`, `libgen.st`, `libgen.gs`, `libgen.gl`.

Use `libgen.li`. It is the one verified to serve `json.php`.

### `json.php` — metadata, no key, no signup

```bash
curl 'https://libgen.li/json.php?object=e&fields=*&doi=10.1038/nature14539'
```

Parameters:

| Parameter | Meaning |
|---|---|
| `object=` | record type: `e` edition, `f` file, `s` series, `a` author |
| `fields=` | `*` for everything, or a comma list |
| `addkeys=` | extra joined tables |
| `doi=` | select editions by DOI |
| `ids=` | select records by primary key |

A DOI lookup returns the edition, including a `files` map of `f_id` → `md5`:

```
edition 46891081
  title      Deep learning
  author     Lecun, Yann (author);Bengio, Yoshua (author);Hinton, Geoffrey (author)
  publisher  Nature Publishing Group
  year       2015
  doi        10.1038/nature14539
  files      46848466 → 9f1fb30f486529c2277305a1650a0d64
             108771996 → ffbdbfd16706ef08a0ddbf85a3889237
```

Then resolve the file record for extension and size — these are **absent** from
the edition's `files` sub-objects, which is why a DOI lookup alone cannot tell you
whether you are about to download a 2 MB PDF or a 900 MB djvu:

```bash
curl 'https://libgen.li/json.php?object=f&fields=*&ids=46848466'
```

```
md5                  9f1fb30f486529c2277305a1650a0d64
extension            pdf
filesize             2083627
scimag_id            40503060
scimag_archive_path  10.1038\nature14539.pdf
time_added           2015-09-24 22:33:31
```

`scimag_id` being non-zero means the file came from the Sci-Hub corpus, and
`scimag_archive_path` is derivable straight from the DOI (`/` → `\`).

### `{"error":"No Request keys"}` — what it actually means

Nothing to do with API keys. "Request keys" are the **record selectors** — the
parameters naming *which rows* you want. The error fires whenever the request
resolves to no record set, and it is overloaded across two distinct causes:

| Request | Result | Cause |
|---|---|---|
| `?ids=1&fields=*` | error | `ids` given but no `object=` |
| `?object=e&fields=*` | error | object named, no selector |
| `?object=x&fields=*&doi=…` | error | invalid object (valid selector) |
| `?object=x&fields=*&ids=…` | error | invalid object (valid selector) |
| `?object=e&fields=*&doi=…` | **works** | |
| `?object=f&fields=*&ids=…` | **works** | |

So on this error, check the `object=` value *and* the selector before assuming
authentication is the problem — it never is.

### Download flow — a per-request one-time key

`get.php?md5=<md5>` alone does **not** work: it 307-redirects to
`/ads.php?md5=<md5>`. That HTML page embeds the real link with a nonce:

```
href="get.php?md5=9f1fb30f486529c2277305a1650a0d64&key=4R62UIPFZ6UYRCH5"
```

So the flow is: `GET /ads.php?md5=…` → scrape `key=` → `GET /get.php?md5=…&key=…`.
The key is single-use and short-lived, so it cannot be cached or shared.

**Keys / registration:** none for metadata or download. **Rate limits:** none
published and none observed in testing; no rate-limit headers are returned. **Paid
tier:** none.

---

## Anna's Archive

Two halves with completely different accessibility.

### The HTML site is not scriptable

`/scidb/<doi>/` (trailing slash required — without it you get a 308) 302-redirects
to `…/?&check=1` and then **403s with `server: ddos-guard`** and a body reading
"Checking your browser before accessing". Measured identically on
`annas-archive.gd`, `.pk` and `.gl`. SLUM marks all three PROTECTED, which agrees.

`annas-archive.li` returns a 1,068-byte placeholder; `annas-archive.org` and
`.se` are NXDOMAIN. Anna's Archive's own 403 body tells you to
**"find the latest official domain on Wikipedia"** — that is the authoritative
domain list for this service, not any third-party mirror page.

### The `/dyn/` JSON endpoints bypass the challenge

This is the useful discovery: DDoS-Guard fronts the HTML pages only.

```bash
curl 'https://annas-archive.gd/dyn/torrents.json'          # 200, 17.7 MB, public
curl 'https://annas-archive.gd/dyn/api/fast_download.json' # 400 + full API docs
```

`fast_download.json` **self-documents in its own error body** — this is the
authoritative contract, quoted verbatim from the service:

> This API is intended as a stable JSON API for getting fast download files as a member.
> A successful request will return status code 200 or 204, a `download_url` field and `account_fast_download_info`.
> Bad responses use different status codes, a `download_url` set to `null`, and `error` field with string description.
> Accepted query parameters:
> - `md5` (required): the md5 string of the requested file.
> - `key` (required): the secret key for your account (which must have membership).
> - `path_index` (optional): Integer, 0 or larger, indicating the collection (if the file is present in more than one).
> - `domain_index` (optional): Integer, 0 or larger, indicating the download server, e.g. 0='Fast Partner Server #1'.
>
> These parameters correspond to the fast download page like this: /fast_download/{md5}/{path_index}/{domain_index}

Measured status codes: **400** `"Invalid md5"` for a malformed md5, **401** for a
well-formed md5 with a bad key. So 401 is the "you are not a member" signal.

### Keys, membership and quotas

- **Search** needs no key.
- **`get_details` and `get_download_url` need a key**, and the key is your
  *account secret key* — the same string you log in with — obtainable by creating
  an account. Documented at `annas-archive.gl/faq#api`.
- **Fast downloads require a paid donation/membership.** This is the only paid
  tier among the shadow libraries. Free users get "slow downloads" with a
  countdown timer, through the browser only.
- Client env var names in the wild: `ANNAS_SECRET_KEY` + `ANNAS_BASE_URL`
  (+ `ANNAS_AUTO_BASE_URL` for SLUM-driven mirror discovery) in
  [annas-mcp](https://github.com/iosifache/annas-mcp);
  `ANNAS_ARCHIVE_API_KEY` in
  [annas-archive-mcp](https://github.com/remikalbe/annas-archive-mcp) (the Rust
  `annas-archive-api` crate).
- **No published per-key rate limit.** The daily *download* quota is the real
  limit and it is tied to the membership tier.

**Corpus size** (Wikipedia, 2026-08-20): 71,400,751 books and 157,010,964 papers,
with roughly 1.1 PB mirrored in public torrents.

---

## Z-Library — not scriptable

All six domains SLUM tracks were probed on 2026-08-26:

| Domain | Measured |
|---|---|
| `z-library.sk`, `1lib.sk`, `go-to-library.sk` | 307 redirect to a gate |
| `z-lib.gl`, `z-lib.gd`, `library-access.sk` | 503 + 9,592-byte Cloudflare challenge |

Nothing here is reachable with `curl`. Z-Library also assigns each user a
**personal domain** after login, so there is no stable public host to script
against, and its free tier caps downloads per day (paid tiers raise the cap).
Treat it as a browser-only, human-in-the-loop resource.

`welib.org` is the usable member of this family — it returned 200 with a full
324 KB page and no challenge — and is worth trying before Z-Library proper.

## The remaining SLUM entries

| Service | Measured | Verdict |
|---|---|---|
| `welib.org` | 200, 324 KB, no challenge | usable; Z-Library-family front end |
| `libstc.nexus` | 200, but **4,839 bytes on every path** | **not a service** — a static "Nexus Bots" placeholder page linking to `hub.libstc.cc`, AA SciDB, `libgen.is/scimag` and `sci-hub.ru`. The real STC hub is `hub.libstc.cc`. |
| `liber3.eth.limo` | 200, 24 KB | IPFS/ENS-hosted; no documented REST API |
| `library.memoryoftheworld.org` | 200, 987 bytes | JS app shell; small curated collection, no API |

---

## Order within the last rung

1. **LibGen** — real JSON API, no key, DOI lookup, extension and size before you
   commit to a download.
2. **Sci-Hub** — `sci-hub.ee` first (it has the search form), then `.ru`/`.su`/`.box`,
   then `.al`/`.mk`; `sci.bban.top/pdf/<DOI>.pdf` as the manual fallback.
3. **Anna's Archive** — `/dyn/` endpoints only; the download half needs paid
   membership, so this is a dead end unless the user already has a key.
4. **welib.org**, then Z-Library — browser-only, human-in-the-loop.

Stop at the first one that yields the passage you need to verify.
