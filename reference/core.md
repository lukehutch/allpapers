# CORE

CORE aggregates open-access deposits from repositories and journals worldwide:
**259,057,483 works** (`api.core.ac.uk/v3/search/works/?q=*` → `totalHits`, read
2026-08-25). That counts deposits, not distinct papers — the same article appears
once per repository holding it, which is why a single DOI returns several records.

Its distinctive value is that it sometimes carries **extracted full text** in the
response, so you skip PDF parsing entirely. That field is gated behind a key.

## Get a key first

Without one, CORE is close to unusable:

- `fullText` comes back as the literal string `"Not available for public API
  users."` — 35 characters where the paper should be.
### Rate limits are metered in tokens, not requests

CORE's own documentation: "a simple query will cost you 1 token while more complex
queries will cost you between 3 to 5 tokens" — recommender, scroll search and bulk
queries cost the most. So the per-day figures are token budgets, not call counts.

| User type | Rate limit |
|---|---|
| Unauthenticated | 100 tokens/day, max 10/minute |
| Registered personal | 1,000 tokens/day, max 25/minute |
| Registered academic, not at a Supporting/Sustaining institution | 5,000 tokens/day, max 10/minute |
| Registered academic at a Supporting/Sustaining institution, and non-academic organisations | negotiated; CORE estimates ~200k tokens/day |

The ~200k tier requires an academic affiliation whose library supports CORE — it
is not obtainable by registration alone. Register at
<https://core.ac.uk/services/api#form>.

Every response carries `x-ratelimit-limit`, `x-ratelimit-remaining` and
`x-ratelimit-retry-after` (an ISO 8601 timestamp). Measured with a registered
personal key on 2026-08-26: `x-ratelimit-limit: 10`, `x-ratelimit-remaining: 9`,
with `x-ratelimit-retry-after` inside the current minute — i.e. the header
reported the 10/minute bucket, not the 25/minute the tier table promises. Trust
the headers over the table.

### Defects measured 2026-08-26 with a registered key

- **A bare quoted phrase returns HTTP 500.** `q="thematic analysis"` → 500 on both
  attempts; `q=thematic analysis` → 200 with 15,820,682 hits; and
  `q=title:"thematic analysis"` → 200 with 4,265,338. Quoted phrases must be
  field-qualified. A 500 here is a query-shape problem, not an outage.
- **DOI mis-attribution reproduces with a key.** `q=doi:"10.1038/nature14539"`
  returned three results — two of them Spanish theses carrying the DOI only
  because it appears in their reference lists — and a second DOI query returned 25
  hits for a single DOI. Always check the title.
- **`fullText` is `""` for most records even with a key.** A key does unlock real
  text (38,460 and 68,513 characters in one measured query), but the empty string
  now stands for "nothing stored", where anonymous callers get the explicit
  `"Not available for public API users."`. With a key you lose the ability to tell
  those two cases apart from that field alone.
- **`sourceFulltextUrls` is not reliably a list of URLs.** One record's was a
  single-element list containing a reference-list citation string with a URL
  embedded in the prose. Validate before fetching.

### The anonymous limit, measured earlier

- The anonymous limit is **10 requests per 10 minutes**. Measured directly: after the
  eleventh call the API returned HTTP 429 with `x-ratelimit-limit: 10`,
  `x-ratelimit-remaining: 0` and `x-ratelimit-retry-after` set exactly ten minutes
  past the response `date`.

Registration is free and instant at <https://core.ac.uk/services/api#form>. Store
it with `scripts/allpapers-setup --set core_api_key=...`.

## The API

Base URL `https://api.core.ac.uk/v3`. The authoritative spec is the live OpenAPI
document at <https://api.core.ac.uk/swagger/v3.json> — **not** the HTML page at
`core.ac.uk/documentation/api`, which still describes the retired v2 API
(`/articles/get`, `/search/{query}`) and its old rate limits.

Authentication, either form:

```
Authorization: Bearer <API_KEY>        # header
?api_key=<API_KEY>                     # query parameter
```

Search:

```
GET /v3/search/works/?q=doi:"10.1038/nature14539"&limit=5
GET /v3/search/works/?q=<query>&limit=100&offset=0
```

**Keep the trailing slash on `/works/`.** Without it the API answers HTTP 301.

Response envelope: `totalHits`, `limit`, `offset`, `results[]`, `tooks`, `searchId`.

Useful fields on each result:

```
id, doi, title, authors, yearPublished, abstract,
fullText, downloadUrl, sourceFulltextUrls[], links[]
```

## Three data-quality traps, all measured

**1. A DOI query returns records that are not that paper.** Querying
`doi:"10.1038/nature14539"` (Deep learning, LeCun/Bengio/Hinton) returned three
records; the first carried exactly that DOI but its title was
*"Uso de la inteligencia artificial en la implementación de la campaña Missing
Sto…"* — a Spanish thesis that merely cited the paper, with the DOI harvested out
of its reference list. **Always check the returned title before trusting a CORE
record.** `allpapers-locate` compares titles across the first five results and
reports a mis-attribution rather than offering it.

**2. `sourceFulltextUrls` is not always a URL.** In the same response it held a
1,900-character dump of a reference list. Validate each entry against
`https?://\S+` and a sane length before fetching it.

**3. The spec says snake_case; the API returns camelCase.** `fullText`,
`downloadUrl`, `sourceFulltextUrls` are the real field names. Code written from
the spec alone silently reads `None` everywhere.

Results are also not stable across identical calls — the same query returned
different records in the first position on successive runs, so pull several
results and filter rather than taking `limit=1`.

## Choosing a PDF link

CORE's own `downloadUrl` proxies through `core.ac.uk/download/<id>.pdf`, which
works but is slower and occasionally stale. The heuristic the `scihub-cli` CORE
integration uses, and a good one: prefer a URL on the original repository host
over a `core.ac.uk` one, prefer URLs that look like a direct PDF (`.pdf` suffix,
`.pdf?`, `/pdf/`, or `viewcontent.cgi` with an `article=` parameter), and
penalise obvious landing pages. Treat HTTP 403 on a probe as "probably still
valid" — many repositories block HEAD requests but serve GETs.
