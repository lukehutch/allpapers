# allpapers

A Claude Code skill for finding and retrieving the full text of scientific papers.

It merges the older `paperclip` and `scihub-cli` skills, adds CORE and Unpaywall,
adds arXiv LaTeX source retrieval, and arranges every source into one priority
ladder. The organising rule is that **a parseable text format is worth more than a
convenient one**: LaTeX and JATS XML carry equations, section structure and
reference lists that PDF text extraction destroys.

## Install

```bash
git clone <this repo> ~/Work/allpapers
ln -s ~/Work/allpapers ~/.claude/skills/allpapers
~/Work/allpapers/scripts/allpapers-setup          # asks once for what it needs
```

`allpapers-setup` writes `~/.config/allpapers/config.json` (mode 0600) and mirrors
the email address and CORE key into `~/.scihub-cli/config.json` so `scihub-cli`
picks up the same values. Run `allpapers-setup --check` at any time to see what is
configured; nothing is ever asked for twice.

It asks for one required value and a few optional ones. The required value is an
**email address**: Unpaywall's API rejects requests without one, and it also puts
Crossref and OpenAlex requests into their faster "polite" pools. The optional ones
are free API keys — **CORE** and **OpenAlex** are the two that materially change
what you get back, and both are instant to obtain. Everything works without them,
just less well.

## How it works

Six tools plus a set of reference documents:

| Tool | What it does |
|---|---|
| `scripts/allpapers-setup` | First-run credential setup and status check. Asks once, stores in `~/.config/allpapers/config.json`. |
| `scripts/allpapers-locate` | Queries paperclip, arXiv, Unpaywall, OpenAlex, CORE and Europe PMC **concurrently** for one paper and prints every free full-text location, ranked most-parseable first. |
| `scripts/allpapers-search` | Keyword (BM25), semantic (vector), hybrid and analogical search over paperclip's 11.6M full texts, optionally alongside Gemini grounded web search. |
| `scripts/arxiv-source` | Downloads an arXiv paper's submitted source into a `mktemp` directory and unpacks it, handling all three payload shapes arXiv serves. |
| `scripts/allpapers-bibtex` | Builds one composite BibTeX entry by merging INSPIRE-HEP, Crossref, DataCite, arXiv, PubMed and Scholar field by field, then normalising it. |
| `scripts/allpapers-fetch` | Fetches source *and* PDF into `verification/source/<citationKey>/`, and writes the `verification/bib.md` record — staged first, promoted or rejected after you have read the paper. |

`reference/ladder.md` is the decision procedure the skill follows; the other
reference files hold the API details for each service, including the defects
measured in each one.

### The ladder, in short

1. **paperclip** — already-extracted, line-numbered full text. Fastest, and the
   line numbers make quotes citable as `#L45-L52`.
2. **arXiv LaTeX source** — the best format that exists for anything on arXiv.
3. **CORE and Unpaywall** — the two large open indices, plus OpenAlex and Europe
   PMC, which answer the same question from different angles.
4. **Google Scholar** — has no official API; the scraping recipe, the silent
   block that looks like an empty result set, and the paid SerpApi alternative are
   all documented in `reference/scholar.md`.
5. **Web search, and Gemini grounded search** — publisher pages, institutional
   repositories, theses, author copies. Gemini runs real Google Search queries and
   returns answers with citations, which reaches material paperclip's four backends
   do not index. Results are leads to verify, never sources to quote.
6. **Sci-Hub** — last resort only, when nothing above has a copy. Bootleg, not
   open. Fetched copies are verification-only and must never be committed.

Full detail, including what to do when paperclip's rate limit is exhausted, is in
`reference/ladder.md`.

### Verification

Retrieval is only useful if the record of it survives. `reference/verification.md`
carries the project's citation-verification requirements: every cited paper is
downloaded and read, its metadata cross-checked against an authoritative index,
and every claim the citing text makes about it backed by a verbatim quote with a
locator — all recorded in a `verification/bib.md` beside the `.tex` file. Numerical
claims get the same treatment in `verification/equations.py`, recomputed
independently rather than transcribed. The file also holds the fourteen-channel
sourcing flow the ladder is derived from, and the hard rules about quoting,
shadow-library copies, and recording `NO-SOURCE` rather than quietly dropping to
abstract-level verification.

`allpapers-fetch` implements this as a two-step workflow, because a search result
is a candidate and not yet a source:

```bash
scripts/allpapers-fetch arXiv:1706.03762 --stage      # to a temp dir; nothing permanent
# read it, then one of:
scripts/allpapers-fetch arXiv:1706.03762 --promote /tmp/allpapers-… --justification '…' --quote '…@#L7'
scripts/allpapers-fetch arXiv:1706.03762 --reject     --justification '…'
```

A promotion puts the LaTeX source, the original tarball, the extracted
`content.lines`, the PDF, a `.bib` file and a `PROVENANCE.json` into
`verification/source/<citationKey>/`, and writes a `bib.md` record carrying the
composite BibTeX entry, every source URL used, the abstract, the justification, and
each claim with its verbatim quote and locator. A rejection writes the same record
minus the files, so the next reader knows the paper was examined and why it was
declined — which is worth as much as an inclusion and stops the dead end being
re-explored.

**A caveat on directory names.** Citation keys from INSPIRE-HEP contain a colon
(`Vaswani:2017lxt`), and the directory is named for the key exactly as specified.
Colons are legal on Linux and macOS but illegal in Windows filenames, so a
repository containing `verification/source/Vaswani:2017lxt/` will not check out on
Windows. If that matters for your repository, sanitise the directory name — the
key inside the `.bib` entry must not change.

### Reference files

| File | Contents |
|---|---|
| `reference/ladder.md` | The priority ladder and what to do when a rung fails |
| `reference/paperclip.md` | The CLI, its REST transport, and why to use the CLI |
| `reference/arxiv.md` | LaTeX source retrieval, payload shapes, HTML, the Atom API |
| `reference/core.md` | CORE API v3, auth, rate limits, data-quality traps |
| `reference/unpaywall.md` | Unpaywall API, response shape, the broken search endpoint |
| `reference/search.md` | Ranking modes, result limits, sort order, how to word a query |
| `reference/other-indices.md` | OpenAlex, Crossref, Europe PMC, Semantic Scholar, NCBI, DOAJ, OpenAIRE |
| `reference/scholar.md` | Google Scholar URL patterns, the silent block, CAPTCHA handling, SerpApi |
| `reference/gemini.md` | Gemini grounded search: endpoints, request shapes, citation extraction |
| `reference/bibtex.md` | The composite merge, the per-field trust order, every normalisation applied |
| `reference/scihub.md` | scihub-cli, its defects, mirror state, the manual fallback |
| `reference/verification.md` | `verification/bib.md` and `verification/equations.py` |

## How many papers are there?

Every number below was read from the service's own API or site on **2026-08-25**,
not from a marketing page. The query used is given so each can be re-checked.

| Service | Records | What that counts | How it was measured |
|---:|---:|---|---|
| OpenAlex | 322,042,936 | all scholarly works | `api.openalex.org/works` → `meta.count` |
| CORE | 259,057,483 | works aggregated from repositories and journals | `api.core.ac.uk/v3/search/works/?q=*` → `totalHits` |
| Crossref | 185,829,151 | registered DOI records | `api.crossref.org/works?rows=0` → `message.total-results` |
| Unpaywall | ~120,000,000 | DOI records tracked for OA status | "Search all 120M of our articles" — unpaywall.org's own site bundle |
| PubMed | 41,056,331 | biomedical citations (abstracts, not full text) | eutils `esearch db=pubmed` |
| DOAJ | 13,487,985 | articles in indexed open-access journals | `doaj.org/api/search/articles` → `total` |
| PMC | 12,547,390 | full-text biomedical articles | eutils `esearch db=pmc term=all[sb]` |
| **paperclip** | **11,624,272** | **full text already extracted and line-numbered** | `paperclip sql` (see note below) |
| PMC open-access subset | 8,171,125 | the redistributable part of PMC | eutils `esearch term="open access"[filter]` |
| arXiv | 3,146,378 | cumulative submissions through 2026-08 | `arxiv.org/stats/get_monthly_submissions`, summed |
| Sci-Hub | *unverified* | — | every mirror was unreachable from this machine |

**Open-access subtotals**, also live from OpenAlex: 121,719,172 works are
`is_oa:true`, and 47,547,905 have `has_fulltext:true`. So of ~322M known works,
roughly 38% are open access in some form and about 15% have machine-readable full
text anywhere. That gap is the reason the ladder exists.

**OpenAlex now stores full text itself**, which is new and changes the ladder.
Counted the same way on the same day: **48,978,284** works have a cached GROBID TEI
XML parse (`has_content.grobid_xml:true`) and **52,396,004** have a cached PDF
(`has_content.pdf:true`). The XML is structured text — sections, paragraphs,
references — so it ranks above any PDF. Downloading either needs a free API key and
costs $0.01 per file against the account's daily budget.

paperclip's 11,624,272 is the sum of its three backends — PMC 8,014,647,
arXiv 3,106,926, and bioRxiv+medRxiv 502,699 (413,666 + 89,033). It has to be
summed by hand: see the defect note below.

### The overlap is large, and it is not incidental

These are not 900M distinct papers. The indices are layered on each other:

- **Crossref is the spine.** Unpaywall is built directly on it — it takes Crossref
  DOIs and asks, for each one, where a free copy lives. So Unpaywall's ~120M is a
  subset of Crossref's 186M, not an addition to it.
- **OpenAlex is a superset of Crossref**, adding records from PubMed, arXiv,
  institutional repositories and elsewhere that never got a Crossref DOI. It is
  run by the same organisation as Unpaywall and carries the same OA data.
- **CORE aggregates repositories**, so the same paper appears once per repository
  that holds it. Its 259M counts deposits, not distinct papers, which is why CORE
  returns several records for one DOI.
- **paperclip re-indexes PMC, arXiv, bioRxiv and medRxiv**, all of which are
  already inside OpenAlex and CORE. Its value is not corpus size but that the full
  text is already extracted, sectioned and line-numbered.
- **arXiv sits inside all of them**, and paperclip holds 3,106,926 of arXiv's
  3,146,378 submissions — about 98.7%.

A useful way to read the table: OpenAlex's 322M is close to the real number of
distinct known works, 121.7M of those are open in some form, and everything else
in the table is a differently-shaped view of that same population. Querying
several indices is still worth it, because they disagree about *where* the free
copy is, and one will often know a repository copy the others have missed.

### Measured defects worth knowing

Each of these was reproduced against the live service; they are documented in full
in the relevant `reference/` file.

- **CORE mis-attributes DOIs.** A `doi:"10.1038/nature14539"` query returned a
  record carrying that DOI whose title was a Spanish thesis about advertising
  campaigns — the DOI had been scraped from its reference list. `allpapers-locate`
  therefore checks the title before trusting any CORE record.
- **OpenAlex does it too**, through the same mechanism. Of the five locations it
  lists for Braun and Clarke's "Using thematic analysis in psychology", only the
  journal's `publishedVersion` was that paper; two of the repository entries were
  confirmed to be entirely different articles. Neither index gives you a field that
  separates the good matches from the bad, so `allpapers-locate` marks every
  location it cannot prove — anything that is not a publisher `publishedVersion` and
  does not carry the work's own DOI, arXiv ID or PMCID in its URL — as
  `identity unconfirmed`, and says to check the title before quoting it.
- **CORE withholds full text from anonymous users**, returning the literal string
  `"Not available for public API users."` in the `fullText` field. A free key
  fixes this and raises the limit from 10 requests per 10 minutes.
- **paperclip's `SELECT COUNT(*)` returns one row per backend**, not a total.
- **paperclip's `lookup --json` ignores the flag** and prints human text anyway,
  and it exits 0 even when it found nothing.
- **Unpaywall's `/v2/search` endpoint returns HTTP 500** on every variation tried;
  DOI lookup works normally.
- **arXiv `/src/` is not always a tarball** — it can be a bare gzipped `.tex`, or
  a PDF when the author submitted no source at all.
- **OpenAlex is metered in dollars now**, which is easy to miss because nothing
  breaks until it does. Every response carries `x-ratelimit-limit-usd` and
  `x-ratelimit-remaining-usd`; anonymous callers get $0.10 a day — 1000 metadata
  lookups at 1 credit each — resetting at midnight UTC, and a free account key
  raises that to $1.
- **Unpaywall covers Crossref DOIs only.** DataCite DOIs are excluded by design, so
  an arXiv paper looked up by its `10.48550/arXiv.…` DOI returns nothing. That is
  not a miss; go to arXiv directly.
- **Google Scholar is a discovery tool, not an identity resolver.** Live probes on
  four exact-title queries put the queried paper outside the returned results
  entirely. Use it to find copies, not to confirm which paper you are holding.
- **Google Scholar's block is invisible.** When it refuses a caller it returns
  HTTP 200 and a full-size ~142 kB page with no CAPTCHA marker and no results —
  indistinguishable from "this paper is not indexed" unless you read the prose. Two
  further traps: the result-block class names appear 24 times in the page's own
  inlined CSS, so testing for their presence reports success on an empty page; and
  the message's apostrophe is entity-encoded (`can&#39;t`), so a literal string
  match never fires. Not User-Agent dependent — the address is what is refused.
- **Scholar's citation-export endpoint does not answer**: `output=cite` returned
  HTTP 404 and `view_op=export_citations` HTTP 302 to sign-in. A lot of third-party
  code still documents these as the way to get BibTeX out of Scholar.
- **NCBI's `idconv` only knows papers that are in PMC**, and reports everything else
  as a per-record `status: error` under an HTTP 200 and a top-level `status: ok`.
  Measured on a 20-PMID spread across 1953–2024, it resolved 10 DOIs where
  `esummary` resolved 18 — including Watson and Crick 1953, which it calls not
  found. Reading its silence as "no such paper" is the easy mistake.
- **NCBI enforces 3 requests/sec for anonymous callers**, returning HTTP 429
  mid-sequence rather than throttling. A free key raises it to 10/s.
- **scihub-cli exits 1 if any identifier failed and 0 only when all succeeded**, and
  it writes `download-report.json` only when something failed — so the file's
  absence is not evidence of a problem, and its presence is.
