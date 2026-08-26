# Google Scholar

**There is no official Google Scholar API.** Google has never published one, sells
no access, and the Terms of Service disallow automated querying. What exists is
the public HTML interface, third-party scrapers that parse it, and paid
proxy-scraping services. Everything below is the HTML interface, with the URL
patterns taken from the `scholarly` package (v1.7.11, read from the PyPI sdist)
and confirmed against live pages on 2026-08-25.

Scholar earns its rung on the ladder for one reason: it indexes *versions*.
Where Unpaywall and CORE know about deposits they were told about, Scholar
crawls repositories, course pages, author homepages and lab sites, and puts a
`[PDF]` link in the right-hand column when it found a free copy anywhere. That
column is often the only free copy of an old or paywalled paper.

## What it is not good for

**It is not an identity resolver.** Measured on 2026-08-25:

| Query | Result |
|---|---|
| `q="Quantifying Organismal Complexity using a Population Genetic Approach"` | 15 results, **the queried paper in none of them** |
| `q="Attention is all you need"` | "About 122,000 results", the Vaswani paper **not in the top 3** |
| `as_epq=Attention is all you need&as_occt=title` | About 68 results — much tighter, still not rank 1 |
| `as_epq=Deep learning&as_occt=title` | title-restricted and exact-phrased, and the LeCun/Bengio/Hinton *Nature* paper still did not come back first |

Quoting a phrase does not force a title match; relevance ranking dominates and
the exact paper can be absent from the page entirely. So: **resolve identity
with Crossref or OpenAlex first**, come to Scholar holding a known title and
authors, and check the title of whatever result you take a PDF from. Never trust
rank position.

**Its citation export does not answer.** `scholarly` builds a BibTeX URL from the
result's `data-cid`, and a lot of third-party code copies that pattern, so it is
worth recording that it did not work from here:

| URL | Result |
|---|---|
| `/scholar?q=info:{cid}:scholar.google.com/&output=cite&scirp=0&hl=en` | **HTTP 404**, 1,646 bytes |
| `/citations?view_op=export_citations&user={id}&hl=en` | **HTTP 302**, 294 bytes — a redirect to sign-in |

Both reproduced on 2026-08-25 with a browser `User-Agent`. Read the caveat in
**Blocking** below before concluding the endpoint is gone: this machine was being
refused at the time, so the 404 may be the block rather than a removal. Either way
it does not currently return BibTeX, which is why `allpapers-bibtex` builds the
entry from Crossref, DataCite, INSPIRE, arXiv and PubMed and uses Scholar only for
fields nothing else carries.

## URL patterns

Base is `https://scholar.google.com`. Send a browser `User-Agent`; the default
`curl` agent gets blocked.

```
/scholar?hl=en&q={query}                     publication search
/scholar?hl=en&as_epq={phrase}&as_occt=title exact phrase, title only  ← for title lookups
/scholar?hl=en&cites={cluster_id}            papers citing this one
/scholar?cluster={cluster_id}&hl=en          all versions of one paper
/scholar?q=related:{scholar_id}:scholar.google.com/   related articles
/scholar?q=info:{scholar_id}:scholar.google.com/&output=cite&hl=en   citation export — 404s, see above
/citations?hl=en&user={author_id}            author profile
/citations?hl=en&view_op=search_authors&mauthors={name}   author search
```

Query parameters that work on `/scholar`:

| Parameter | Effect |
|---|---|
| `as_ylo=`, `as_yhi=` | Year lower / upper bound |
| `as_sdt=0,33` | Exclude patents (`1,33` includes them) |
| `as_vis=1` | Exclude citation-only records |
| `as_occt=title` | Restrict matching to titles |
| `as_epq=` | Exact phrase |
| `scisbd=1` \| `2` | Sort by date — `1` abstracts only, `2` everything |
| `start=` | Offset; the page holds 10 results |
| `hl=en` | Language |

## Pulling the free PDF out of a results page

The free-copy link lives in `<div class="gs_ggs gs_fl">` — take the first `<a
href>` inside it. Each result block is `<div class="gs_r gs_or gs_scl" ...>`,
its title is `<h3 class="gs_rt">`, and the version-cluster id appears as
`cluster={id}` in the "All versions" link.

```bash
curl -sS -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36" \
  "https://scholar.google.com/scholar?hl=en&as_epq=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$TITLE")&as_occt=title" \
  -o scholar.html
```

Then parse `gs_ggs gs_fl` for the PDF href and `gs_rt` for the title to check it.

## Blocking

There are two kinds, and the second is the dangerous one.

**The CAPTCHA.** Scholar serves a challenge page rather than an error. `scholarly`
detects it by looking for these ids in the HTML: `gs_captcha_ccl` (the inline
captcha div), `recaptcha` and `captcha-form` (full-page forms), and
`rc-doscaptcha-body`. It also treats HTTP 403 as access-denied and rotates
sessions. Check for those strings before believing a page — the response is still
HTTP 200. If one appears, do not fight it: drop to the next rung of the ladder.

**The silent refusal, which has no CAPTCHA marker at all.** Measured repeatedly on
2026-08-25, including on a bare `?q=photosynthesis`:

```
HTTP 200, ~142 kB, Content-Type: text/html
0 occurrences of "gs_r gs_or gs_scl"   (result blocks)
0 occurrences of "<h3"                 (result titles)
none of the four CAPTCHA markers
visible text: "Google Scholar   Loading...
               The system can't perform the operation now. Try again later.
               Please enter a query in the search box above."
```

A full-size, well-formed, CAPTCHA-free page containing no results. Three traps in
it, all of which cost time here:

1. **It looks exactly like "this paper is not in Scholar."** It is not — it is
   "Scholar will not talk to this address right now." Reporting the first is a
   false negative that silently propagates into a citation record. `allpapers-bibtex`
   now distinguishes them and says which it saw.
2. **The class names are in the stylesheet.** Counting `gs_rt` in the raw HTML of
   that empty page gives 24 hits and `gs_a` gives 34 — every one inside the inlined
   CSS, none in the body. Any detector that tests for the presence of a class name
   rather than parsing result markup will call this page a success. Match on the
   full `<h3 class="gs_rt"…>` element, or strip `<style>` and `<script>` first.
3. **The apostrophe is entity-encoded.** The page ships `can&#39;t`, so a literal
   search for `can't perform the operation` never matches. Unescape entities before
   testing for the message — confirmed both ways on the same page body.

**It is not User-Agent dependent.** The same query with a Chrome 126 UA and with
`allpapers/1.0 (mailto:…)` returned the same 139,800-byte empty page. Rotating the
UA does not clear it; it is the address that is refused.

So a Scholar miss is only evidence of absence once you have checked the page is a
real results page. When it is refusing, treat the whole rung as unavailable and
move down the ladder — the rest of the ladder does not depend on it.

## Paid alternative: SerpApi

If Scholar blocks and the paper matters, SerpApi runs the scrape and returns JSON.
Confirmed against its docs and pricing page on 2026-08-25.

```
https://serpapi.com/search.json?engine=google_scholar&q={query}&api_key={key}
```

Engines: `google_scholar`, `google_scholar_author`, `google_scholar_cite`,
`google_scholar_profiles`, `google_scholar_case_law`. Parameters mirror the HTML
ones — `cites`, `cluster`, `as_ylo`, `as_yhi`, `as_sdt`, `as_vis`, `as_rr`,
`scisbd`, `hl`, `lr`, `start`, `num` (1–20, default 10), `safe`, `filter`.

Free plan is **250 searches per month** with a guaranteed throughput of 50
successful searches per hour. Store the key with
`scripts/allpapers-setup --set serpapi_key=...`; it is optional and the skill
works without it.
