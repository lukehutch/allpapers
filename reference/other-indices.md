# The other indices

Everything here was checked live on 2026-08-25. Endpoints, field names and
counts are from the responses shown, not from memory.

## OpenAlex — the metadata spine, and now a full-text host

`https://api.openalex.org/works/doi:{doi}` (also `works/{openalex_id}`,
`works?filter=…`, `works?search=…`).

Two things make OpenAlex worth a call on nearly every lookup:

**1. It lists every known location for a work**, open or not, under `locations[]`
— each with `is_oa`, `pdf_url`, `landing_page_url`, `license`, `version` and a
`source.display_name`. `best_oa_location` picks one. For the PLoS DOI above it
returned 8 locations. It also carries `abstract_inverted_index`, which rebuilds
into an abstract for old paywalled papers whose abstract is deposited but
displayed nowhere free — sort the word positions and join.

**A repository location is sometimes a different paper.** This is the same defect
CORE has, and it is worth knowing that OpenAlex has it too, because it produces
exactly the misattribution that citation verification exists to catch. Measured on
`W1979290264`, Braun and Clarke's "Using thematic analysis in psychology":

| Location | `version` | What is actually there |
|---|---|---|
| `tandfonline.com/doi/abs/10.1191/1478088706qp063oa` | publishedVersion | the paper |
| `scielo.sa.cr/…uniciencia…587.pdf` | submittedVersion | "An Analysis of Students' Mathematical Reasoning in Solving Probability Problems…" |
| `hdl.handle.net/10125/42031` | submittedVersion | "Mentor-Apprentice Programs: Effects on Mentors & Apprentices' wellbeing" |
| `hal.science/hal-04848132` | submittedVersion | PDF filename reads "Zanni et al. — Representations and lived experiences of sexual he…"; the landing page served a bot check, so unconfirmed |
| `hdl.handle.net/2292/14647` | submittedVersion | page returned no title; unverified |

Each wrong entry is a repository record that cites Braun and Clarke, matched to
their work. The rule that follows: **`version: publishedVersion` can be taken on
trust; anything else needs its title checked before you quote it.**

`version` alone is too blunt a test, because OpenAlex also labels PMC's own copy of
a PLoS article `submittedVersion`. The reliable signal is the URL: one that spells
out the work's own DOI, arXiv ID or PMCID cannot be a different paper.
`allpapers-locate` combines the two — publisher `publishedVersion` or an identifier
in the URL means certain, everything else is printed `— identity unconfirmed` with
a footer saying to open it and check the title. The same test is applied to CORE's
`downloadUrl` and `sourceFulltextUrls`, which have the same problem.

**2. It now serves its own cached full text.** Confirmed live:

```
has_content:  {"pdf": true, "grobid_xml": true}
content_urls: {"pdf":        "https://content.openalex.org/works/W3038568908.pdf",
               "grobid_xml": "https://content.openalex.org/works/W3038568908.grobid-xml"}
```

Measured corpus coverage:

| Filter | Works |
|---|---|
| `has_content.pdf:true` | 52,396,004 |
| `has_content.grobid_xml:true` | 48,978,284 |

The GROBID TEI XML is a structured parse — headers, sections, paragraphs,
references as markup — so it sits just below arXiv LaTeX in the format order and
above every PDF. That is a genuinely large parseable-text corpus, second only to
paperclip's extracted text among the channels here.

Downloads require a key: without one `content.openalex.org` answers

```
HTTP 401  {"error":"API key required",
           "message":"Content downloads require an API key. Get one free at https://openalex.org/users"}
```

**Caveats.** GROBID does no OCR, so scanned or image-only PDFs parse to almost
nothing, and its output is known to carry wrong or partial header metadata and
missing or duplicated references. Treat the TEI as a good parse, not a
publisher-authored one, and check anything a quote hangs on. The cached PDFs keep
their original copyright — OpenAlex grants no extra rights.

**It is metered.** This is the change most likely to surprise: OpenAlex now bills
API use in dollars. Every response carries the running total:

```
x-ratelimit-limit: 1000            x-ratelimit-limit-usd: 0.1
x-ratelimit-remaining: 955         x-ratelimit-remaining-usd: 0.0955
x-ratelimit-credits-used: 1        x-ratelimit-cost-usd: 0.0001
x-ratelimit-reset: 73693
```

Measured: anonymous access gets **$0.10 per day** — 1000 credits, one metadata
lookup costing 1 credit — and `x-ratelimit-reset` counts down to **midnight
UTC** (73693 s at 03:31 UTC resolved to 00:00:10 the following day). A free
account key raises that to **$1/day**, which the docs price at roughly 100
full-text file downloads ($0.01 each) or ~10,000 metadata calls. Paid tiers go
$20/$100/$200+ per day. Get the free key at <https://openalex.org/users> and
store it with `scripts/allpapers-setup --set openalex_api_key=...`.

Pass `mailto=` on every request regardless; it identifies the caller.

## Crossref — the metadata authority

`https://api.crossref.org/works/{doi}`, and
`works?query.bibliographic=…` for search.

This is what a `.bib` entry must be checked against: authors, exact title,
container title, volume, issue, page range, year, publisher. It is the DOI
registration record, so it is right about bibliographic detail in a way that a
scraped index is not.

It is *not* a full-text channel. The `link[]` array on the PLoS record held one
entry, `content-type: unspecified`, `intended-application:
similarity-checking` — a Similarity Check deposit, which is for plagiarism
services and not generally fetchable. Do not report those as reader-accessible
copies.

185,829,151 records indexed. Free, no key. Put your address in a `mailto=`
parameter or the `User-Agent` to land in the polite pool.

## Europe PMC — the best JATS XML source

Search: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=…&format=json&resultType=core`

The `core` result type returns `fullTextUrlList.fullTextUrl[]`, each entry
tagged with `availability` ("Open access" / "Subscription required"),
`availabilityCode` (`OA` / `S`), `documentStyle` (`pdf`, `html`, `doi`) and
`site` (`Europe_PMC`, `Unpaywall`, `DOI`). Also `isOpenAccess`, `inEPMC`,
`hasTextMinedTerms`, `pmid`, `pmcid`.

Full text, when `inEPMC` is `Y`:

```
https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML
```

**The path is one segment, and the PMCID keeps its `PMC` prefix.** Measured:

| Path | Result |
|---|---|
| `/rest/PMC1790863/fullTextXML` | **200, 94,888 bytes** |
| `/rest/PMC/PMC1790863/fullTextXML` | 404 |
| `/rest/PMC/1790863/fullTextXML` | 404 |
| `/rest/MED/17299597/fullTextXML` | 404 |

The two-segment `{source}/{id}` form appears in a lot of third-party code and
does not work. This is JATS XML — authored structure, not a parse — so it is the
best non-arXiv machine-readable format available and outranks TEI.

Free, no key.

## Semantic Scholar

`https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,externalIds,openAccessPdf,isOpenAccess`

Returns `openAccessPdf: {url, status, license}` plus `externalIds` mapping
between DOI, PubMed, PubMedCentral, MAG, ArXiv and its own CorpusId — which
makes it a useful identifier bridge when NCBI has no record. Abstracts are
available too, though some AIP and IOP abstracts are elided by the publisher.

Works without a key at a low rate; a free key raises the limit
(<https://www.semanticscholar.org/product/api#api-key>).

## NCBI — resolving PMIDs, PMCIDs and DOIs into each other

There are four endpoints here and they answer different questions. Using the
wrong one produces a confident, wrong "this paper does not exist".

### The ladder

| Want | Use | Covers |
|---|---|---|
| PMID/PMCID → DOI, fast, batched | `idconv` | **PMC only** |
| PMID → DOI, anything in PubMed | `esummary` | all 41M PubMed records |
| DOI or publisher ID → PMID | `esearch` with `[AID]` | all of PubMed |
| Abstract when there is no free full text | `efetch` | all of PubMed |

Work down it. `allpapers-locate` calls `idconv` first because it batches and is
fast, and falls through to `esummary` on the error described below.

### 1. idconv — batched, but PMC only

```
https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids={ids}&format=json&tool=allpapers&email={email}
```

**The old `https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/` URL now returns
301** to the address above. Follow redirects or use the new host directly. It takes
a comma-separated list, returns `records[]` with `doi`, `pmcid`, `pmid`, and warns
if `tool` and `email` are missing but still answers.

**It only knows articles that are in PMC**, and it reports that as a *success*.
Hand it a PMID for anything else and you get:

```
{"status":"ok",
 "records":[{"pmid":26017442,"requested-id":"26017442",
             "status":"error","errmsg":"Identifier not found in PMC"}]}
```

HTTP 200, `status: ok` at the top level, per-record `status: error`, no DOI. PMID
26017442 is Nature's "Deep learning" — indexed everywhere. A caller that checks the
HTTP code and the top-level status, then reads `doi`, sees a blank and concludes
the paper is unknown.

How often that fires, measured 2026-08-25 on a 20-PMID spread across 1953–2024
and a range of journals:

| Endpoint | PMIDs resolved to a DOI |
|---|---|
| `idconv` | **10 of 20** — the other 10 came back `Identifier not found in PMC` |
| `esummary` | **18 of 20** |

Half the sample was invisible to `idconv`. The two `esummary` also missed are
genuinely pre-DOI (PMID 4587288, a 1973 dentistry paper) — that is a real absence,
not a coverage gap.

### 2. esummary — the whole of PubMed

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmids}&retmode=json
```

The DOI is in `result[<pmid>].articleids[]` under `idtype: "doi"`; the same array
carries `pubmed`, `pmc`, `pii`, `mid` and `rid`, so one call resolves every
identifier a record has. Also batched, comma-separated.

Measured: it returns `10.1038/171737a0` for Watson and Crick's 1953 structure of
DNA (PMID 13054692), which `idconv` reports as not found. Age is no obstacle —
being outside PMC is.

### 3. esearch `[AID]` — the reverse direction, DOI → PMID

Nothing above goes backwards from a DOI unless the paper is in PMC. This does:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={doi}%5BAID%5D
```

`[AID]` is the Article Identifier field, and it holds more than DOIs. All measured
2026-08-25, each returning `count: 1`:

| `term=` | → PMID |
|---|---|
| `10.1038/nature14539[AID]` | 26017442 |
| `10.1038/171737a0[AID]` | 13054692 |
| `10.1371/journal.pone.0000217[AID]` | 17299597 |
| `S0092-8674(11)00127-9[AID]` — a publisher PII, not a DOI | 21376230 |
| `10.1038/nature14539[DOI]` — `[DOI]` also resolves | 26017442 |
| `10.48550/arXiv.1706.03762[AID]` — a DataCite DOI | `count: 0`, correctly |

URL-encode the term; the brackets and any parentheses in a PII must be escaped.
A `count: 0` with no `warninglist.phrasesnotfound` is a genuine absence from
PubMed rather than a query that failed to parse — worth checking, because those two
are otherwise indistinguishable.

### 4. efetch — the abstract, when there is no free full text

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract
```

Add `&retmode=xml` for structured output. This is an abstract, not full text: it
supports an `ABSTRACT-ONLY` verdict in `verification/bib.md` and never a
quote-backed one.

### Rate limit

**3 requests per second per IP without an API key**, and it is enforced — four
rapid sequential `esearch` calls from here produced `HTTP 429 Too Many Requests` on
the fourth, mid-loop. A free key from
<https://www.ncbi.nlm.nih.gov/account/settings/> raises it to 10/s; pass it as
`&api_key=…`. Batch the identifier lists rather than looping, space unbatchable
calls, and retry a 429 rather than reading it as a failure.

## DOAJ

`https://doaj.org/api/search/articles/doi:{doi}` — returns
`{total, page, pageSize, timestamp, query, results, last}`. 13,487,985 articles,
all from vetted fully-open-access journals, so a DOAJ hit is a strong signal that
a legitimate free copy exists. Free, no key.

## OpenAIRE

`https://api.openaire.eu/search/publications?doi={doi}&format=json` — responds
200 `application/json`. Aggregates European repository deposits, and sometimes
holds an institutional copy the other indices missed. Worth a call only when the
rest of the ladder has come up empty.
