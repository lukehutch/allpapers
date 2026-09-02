# dblp

The computer science bibliography, run by Schloss Dagstuhl. It is a **metadata
and identity** index, not a full-text source: it holds no papers, no abstracts
and no citation graph. What it does hold, and nothing else on the ladder holds as
well, is a clean, human-curated record of **conference proceedings** — the venue,
the editors, the series, the page range — for a literature where the conference
paper, not the journal article, is the unit of record.

Everything below was measured against the live API on 2026-09-02 with a Chrome
User-Agent. There is **no API key and no registration**; the service is open.

## Why it earns a place

Two things it does better than anything else here:

**It resolves identity, where Google Scholar does not.** The same query that
Scholar could not answer — `Attention is all you need Vaswani` — returns from dblp
exactly two hits, and both are the right paper:

| Rank | Title | Venue | Year | Key |
|---|---|---|---|---|
| 1 | Attention is All you Need. | NIPS | 2017 | `conf/nips/VaswaniSPUJGKP17` |
| 2 | Attention Is All You Need. | CoRR | 2017 | `journals/corr/VaswaniSPUJGKP17` |

Total hits: 2. Compare `scholar.md`, where the same paper is not in the top 3 of
122,000 results. When the paper is in computer science, **dblp is the identity
resolver to reach for, ahead of Scholar.**

**It carries proceedings metadata that Crossref does not have.** That NIPS 2017
paper has no Crossref record — the proceedings were never deposited — so a
DOI-based route yields no venue at all. dblp gives the full booktitle, the seven
editors and the page range. `allpapers-bibtex` now merges dblp in for exactly
this, and trusts it first for `booktitle`, `editor` and `series`.

## The trap: dblp does not index DOIs

A DOI query returns **zero hits**, even for a paper whose dblp record carries that
exact DOI. The API tokenizes the string into prefix terms and searches for those
words:

| Query | `result.query` echoed back | Hits |
|---|---|---|
| `10.1038/nature14539` | `10 1038* nature14539*` | 0 |
| `10.1109/DAC18074.2021.9586227` | `10 1109* DAC18074* 2021* 9586227*` | 0 |

The second DOI is on a record dblp holds and returns for a title query. So a
zero-hit DOI lookup is **not** evidence the paper is absent — it is evidence you
used the wrong key. **Enter dblp by title plus the first author's surname**, for the
reason in the next section. Then compare the returned title with the one you asked
for before believing anything, because a title query is a relevance search, not a
lookup.

## A title alone is not a key either

The search is ranked and truncated, and `h` caps at 100. A well-known title matches
far more records than that — reviews, citing papers, workshop versions, reprints —
and the paper you want is not guaranteed to be among the ranked hundred.

Measured 2026-09-02 on "Attention Is All You Need": the title query reports 112
matches, dblp ranks only the first 100, and the paper is in **none of them**. Its
own exact title, with `$`-forced exact-word terms and `h=100`, does not retrieve it.
Adding the first author's surname — `Attention Is All You Need Vaswani` — collapses
the same search to 2 hits with the paper at rank 1.

So the surname is not a refinement. It is the difference between finding the paper
and silently concluding dblp does not have it. Both `allpapers-locate` and
`allpapers-bibtex` therefore skip dblp entirely when they have no author to send.

## Query syntax

Every term is **prefix-matched by default**, and the API tells you so: it echoes
the expanded query in `result.query`. Append `$` to a term to force exact-word
matching.

| Query | Echoed as | Hits |
|---|---|---|
| `need` | `need*` | 19,082 |
| `need$` | `need` | 8,221 |
| `transformer` | `transformer*` | 52,057 |
| `transformer$` | `transformer` | 38,920 |

**Facets** are written `field:value:` — note the trailing colon — and the API
rewrites them visibly in the echoed query, which is how you confirm one was
understood rather than searched for as a word:

| Query | Echoed as | Hits |
|---|---|---|
| `attention venue:NIPS:` | `attention* :facetid:venue:"NIPS"` | 53 |
| `attention year:2017:` | `attention* :facetid:year:"2017"` | 1,036 |

## The three endpoints

```
https://dblp.org/search/publ/api?q={query}&format=json&h=10&f=0
https://dblp.org/search/author/api?q={name}&format=json&h=10
https://dblp.org/search/venue/api?q={name}&format=json&h=10
```

| Parameter | Effect |
|---|---|
| `q` | The query. Prefix-matched per term; `$` forces an exact word |
| `format` | `json`, `xml` or `jsonp`. **An unknown value returns HTTP 500**, not a 400 |
| `h` | Hits to return. **Capped at 100** — asking `h=1000` returned `@sent: 100` |
| `f` | First hit, i.e. the offset, for paging past 100 |
| `c` | Number of completion terms to suggest |

The response envelope is `result.status.{@code,text}`, `result.completions` and
`result.hits.{@total,@computed,@sent,@first,hit[]}`. `@total` is the true hit
count; `@computed` is how many the server actually ranked, and it stops at 100.

Each publication hit's `info` carries: `title`, `authors.author[]` (each with a
`@pid`), `venue`, `volume`, `pages`, `year`, `type`, `access`, `key`, `doi`, `ee`,
`url`. Author hits carry the author's `url` — their **PID page**, e.g.
`https://dblp.org/pid/56/953` for Yoshua Bengio — plus `notes` holding affiliation
and awards. Venue hits carry `venue`, `acronym`, `type` and the venue's `url`.

**`access` is the open-access flag** — `"open"` or `"closed"` — and on an `open`
record the `ee` link is a free copy. That is the one thing dblp contributes to
locating full text, and it is what `allpapers-locate`'s dblp probe emits.

**Titles come back with a trailing period.** `"Attention is All you Need."` in
JSON and XML; the BibTeX record drops it. Normalize before comparing titles.

## Getting a record: BibTeX and XML

Once a search has given you a `key` like `conf/nips/VaswaniSPUJGKP17`:

```
https://dblp.org/rec/{key}.bib?param=0     condensed
https://dblp.org/rec/{key}.bib?param=1     standard   ← use this one
https://dblp.org/rec/{key}.bib?param=2     standard + a @proceedings crossref entry
https://dblp.org/rec/{key}.xml             the raw record
https://dblp.org/pid/{pid}.xml             an author's complete publication list
```

The PID page is the full record and it is large: `https://dblp.org/pid/56/953.xml`
(Yoshua Bengio) is **1,053,237 bytes** and its root element declares `n="1247"`
publications. Fetch it only when you actually want the whole list.

The `param` values are not cosmetic. `param=0` condenses the venue to its
acronym — `booktitle = {NIPS}` — which is not a citable venue name. `param=1`
gives the real one:

```bibtex
@inproceedings{DBLP:conf/nips/VaswaniSPUJGKP17,
  author       = {Ashish Vaswani and Noam Shazeer and ...},
  editor       = {Isabelle Guyon and Ulrike von Luxburg and ...},
  title        = {Attention is All you Need},
  booktitle    = {Advances in Neural Information Processing Systems 30: Annual
                  Conference on Neural Information Processing Systems 2017,
                  December 4-9, 2017, Long Beach, CA, {USA}},
  pages        = {5998--6008},
  year         = {2017},
  url          = {https://proceedings.neurips.cc/paper/2017/hash/3f5ee...html},
  biburl       = {https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```

Cite keys are prefixed `DBLP:`. `param=2` additionally emits the `@proceedings`
entry the paper cross-references, which is what you want if the bibliography
should cite the volume as well as the paper.

The XML record is worth fetching when the search hit's single `ee` is not enough:
it lists **every** electronic edition, each tagged with its own access type.

```xml
<ee type="oa">https://proceedings.neurips.cc/paper/2017/hash/3f5ee...html</ee>
<ee type="oa">http://papers.nips.cc/paper/7181-attention-is-all-you-need</ee>
<crossref>conf/nips/2017</crossref>
```

## Failure modes, all measured

dblp has no API key, and it rate-limits by refusing rather than by telling you.
There are no `x-ratelimit-*` headers on any response.

- **HTTP 503, `No server is available to handle this request`.** Hit on the first
  probe of the session; cleared on its own in under a minute. Transient.
- **HTTP 500 with a full `dblp: error 500` HTML page.** This is what throttling
  looks like — the same query that returned clean JSON a minute earlier returns
  a 500 HTML page after roughly a dozen requests in quick succession. It is also
  what a genuinely malformed request returns: `format=jsonx` gives the identical
  500 page (confirmed separately, while other queries were answering 200), so a
  500 alone does not tell you which of the two you have.
- **A 500 never means "no results".** A query that genuinely matches nothing
  answers HTTP 200 with a well-formed envelope and `hits.@total: 0` — measured on
  `q=zzzqqqxxnotapaper`. So if you get a 500, you have a throttle or a bad
  request, and recording an absence from it is always wrong. This one cost time
  here: an empty-query probe returned a 500 mid-throttle and looked like a
  meaningful result until it was re-run cleanly and came back 200 with zero hits.
- **Connection timeouts with no response at all**, once throttling is established.
- **`HEAD` returns HTTP 500 on every endpoint**, including ones that answer `GET`
  with a clean 200. Never probe dblp with a HEAD request.

So: **go slowly** — a couple of requests per paper, not a dozen — and treat a 500
or a timeout as transient, retrying on the schedule in `ladder.md` rather than
recording an absence. Responses are cached (`cache-control: max-age=28800`), so
repeating an identical query is cheap.

## What dblp will not give you

No abstracts, no full text, no citation counts, no references. It covers computer
science and immediately adjacent fields only — for anything else it is a silent
miss, which is why both scripts treat an empty dblp result as "not applicable"
rather than as a finding.
