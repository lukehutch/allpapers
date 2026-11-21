# Biomedical search: PubMed, Europe PMC, preprints, trials

What each biomedical index adds over paperclip, how to search it, and what none
of them reach. All counts below were measured on 2026-11-20 unless marked.

## What paperclip already covers

| paperclip source | Documents | Notes |
|---|---|---|
| `-s pmc` | 8,370,669 | PMC full text |
| `-s biorxiv` | 438,113 | newest posted 2026-11-19; 7,977 posted since 2026-10-01 |
| `-s medrxiv` | 96,359 | newest posted 2026-11-18 |
| `-s abstracts` | not countable (`paperclip sql` rejects the source) | PubMed abstract records mixed with PMC |
| `-s trials/us`, `eu`, `jp`, `cn` | not countable | trial registries |

bioRxiv and medRxiv are current to within a day or two, so freshness is not a
gap. The "default last-2-years window" in paperclip's help had no effect: a
`-s pmc` search gave the same 2008–2026 spread of years with and without `--all`.

**PubMed coverage of `-s abstracts` is about 84%.** PubMed holds 41,472,869
records (`esearch` term `all[sb]`). From 50 PMIDs with abstracts, 5 from each of
1975, 1990, 2000, 2008, 2014, 2018, 2021, 2023, 2024 and 2025, an exact title
search in `-s abstracts -t` found 42. The misses were mostly very old, translated
or very recent records (1975: 1104306; 1990: 2249378, 2249898; 2000: 18968124;
2018: 31892828; 2021: 35649018; 2025: 41970485, 42422408). The sample is not
uniform within a year: each PMID was drawn below position 9,999 of esearch's
default order. `paperclip lookup pmid` does not search these records at all, so
it undercounts PubMed coverage; title search is the way to test it.

A PubMed abstract record has a numeric ID that is **not** the PMID
(`/papers/88060771` is PMID 22465831); `meta.json` holds the PMID, PMCID and DOI.

## What is missing, and what fills it

| Gap | Filled by | Score 0–10 | Why |
|---|---|---|---|
| paperclip IDs for bioRxiv, medRxiv and PubMed abstracts were not parsed | fixed in `allpapers-locate` and `allpapers-search` | 10 | every bioRxiv hit printed `(no id)`, and locate listed no paperclip row for any 10.1101 DOI |
| about 16% of PubMed; MeSH and publication-type queries | `allpapers-search --pubmed` | 8 | the query language systematic reviews are written in |
| 1.29M preprints outside bioRxiv/medRxiv; section-level search | `allpapers-search --europepmc` | 9 | Research Square and Preprints.org were searched by nothing here |
| bioRxiv/medRxiv JATS XML and the published journal DOI | the bioRxiv probe in `allpapers-locate` | 9 | before it, the best row for 10.1101/760983 was a GROBID parse |
| structured trial search | ClinicalTrials.gov API v2, below | 7 | paperclip's ranked search found 12 of the 26 matching trials |
| entity-normalized search (gene, chemical, disease) | PubTator3, below | 6 | useful for gene and variant names; documented, not wired in |
| Embase, Scopus, Web of Science, CINAHL, PsycINFO, Cochrane Library | none | 0 | subscription databases with no free API; say so when a review needs them |
| keyword search of bioRxiv itself | none | 0 | api.biorxiv.org has no search endpoint; use paperclip or Europe PMC `SRC:PPR` |

## PubMed: `allpapers-search --pubmed`

```bash
scripts/allpapers-search --no-paperclip --pubmed-query \
  '"Pancreatic Neoplasms"[MeSH] AND "Metformin"[MeSH] AND Meta-Analysis[pt]'
scripts/allpapers-search --pubmed "metformin pancreatic cancer survival"   # with paperclip
```

esearch (Best Match order, or publication date with `--sort date`), then
esummary in batches of 200. The NCBI key and email from the config are sent when
set (10 requests/second with a key, 3 without). Rows show `PMID:<n>`.

PubMed maps plain words onto MeSH and explodes MeSH terms to their narrower
headings; Europe PMC does neither in the same way. For
`MeSH Pancreatic Neoplasms AND MeSH Metformin` PubMed returned 210 records and
Europe PMC's `MESH:` field 50; adding the publication type gave PubMed 3
randomized trials and 12 meta-analyses against Europe PMC's 0 and 1. **For a
MeSH or publication-type query, use PubMed.**

Useful tags: `[MeSH]`, `[majr]` (major topic), `[tiab]`, `[pt]` (Randomized
Controlled Trial, Meta-Analysis, Systematic Review, Review), `[dp]` (date),
`[au]`, `[ta]` (journal), `NOT retracted publication[pt]`.

`--year-min` and `--year-max` filter on `[pdat]`, which also matches the
electronic date: PMID 42846986, print 2026 Sep and epub 2025 Dec 16, passes a
2024–2025 filter. The row shows the print date.

## Europe PMC: `allpapers-search --europepmc`

```bash
scripts/allpapers-search --no-paperclip --europepmc-query \
  'TITLE_ABS:(metformin AND "pancreatic cancer") AND SRC:PPR'
scripts/allpapers-search --europepmc-query 'METHODS:"metformin" AND "pancreatic cancer"' \
  "metformin pancreatic cancer"                                            # paperclip too
```

The REST `search` endpoint, `resultType=lite`, cursor paging up to 1,000 a page.
Rows show `PMID:<n>` when the record has one, otherwise Europe PMC's own ID
(`PPR1183454`); the source column is the Europe PMC source and the journal or
preprint server.

Coverage by source (`SRC:` hit counts):

| Source | Records |
|---|---|
| `MED` (PubMed) | 41,400,145 |
| `PPR` (preprints) | 1,292,456 |
| `PAT` (patents) | 4,229,296 |
| `AGR` (Agricola) | 1,026,549 |
| `PMC` (PMC-only, no PubMed record) | 1,020,579 |
| `ETH` (theses) | 176,799 |
| `CBA` (Chinese Biological Abstracts) | 142,377 |
| `CTX`, `HIR` | 3,935, 2,868 |

Preprints by server (`SRC:PPR AND PUBLISHER:"…"`): Research Square 498,938,
bioRxiv 361,424, Preprints.org 135,430, medRxiv 92,098, SSRN 17,659, ChemRxiv
8,952, arXiv 7,866. 77,424 preprints have full text in Europe PMC.

**Free text matches full text, not only the abstract.** `metformin pancreatic
cancer survival` gave 12,238 hits; the same words under `TITLE_ABS:` gave 110.
The two rankings then share few papers with PubMed: in the top 40 of each, free
text overlapped PubMed on 0 papers, and `TITLE_ABS:(…) AND SRC:MED` on 20 of 40.
Use `TITLE_ABS:` for an abstract-level search and a section field when the words
must appear in a given part of the paper.

Fields worth knowing: `TITLE:`, `ABSTRACT:`, `TITLE_ABS:`, `METHODS:`,
`RESULTS:`, `DISCUSSION:`, `FIG:`, `TABLE:`, `SRC:`, `PUBLISHER:`, `HAS_FT:Y`,
`OPEN_ACCESS:Y`, `PUB_YEAR:[2020 TO 2024]`, `MESH:`, `PUB_TYPE:`, `ACCESSION_TYPE:`
(e.g. `pdb`, `gen`).

Europe PMC answered HTTP 429 after about a dozen requests in a few seconds;
`allpapers-search` waits 3 s and retries once, and reports a second 429 as a
failure under `note:`, not as zero results.

## Running both, and merging

`--europepmc-query` and `--pubmed-query` replace the shared query for their own
backend, since the two syntaxes differ. Rows are merged on DOI, PMCID, PMID, and
last on the normalized title, and tagged with every backend that found them
(`[hybrid+pubmed]`). The header gives each API's total hit count, so you can see
how much lay past `-n`.

## bioRxiv and medRxiv full text: `allpapers-locate`

For a 10.1101 DOI, locate asks `https://api.biorxiv.org/details/{biorxiv|medrxiv}/{doi}`
and lists the newest version's JATS XML (`…source.xml`, which answers 301 and
needs redirects followed; one example downloaded 168,129 bytes as
`application/xml`) and, when `published` is not `NA`, the journal DOI. One recent
post's JATS URL answered 404, so the probe checks it before listing it. Cold
Spring Harbor's journals share the prefix and get "DOI not recognizable".

paperclip holds bioRxiv and medRxiv papers under two IDs: `bio_18dbbf8171e1` in
search output and a UUID (`fb37af04-6c0e-1014-9fac-9ce395c656a4`) in `lookup`
output. Both open with `paperclip cat /papers/<id>/content.lines`.

## ClinicalTrials.gov (not wired in)

```
https://clinicaltrials.gov/api/v2/studies?query.cond=pancreatic+cancer&query.intr=metformin&countTotal=true&pageSize=100&fields=NCTId,BriefTitle,OverallStatus,HasResults
```

612,892 studies, no key, no rate-limit headers. Page with `pageToken` set to the
response's `nextPageToken`. Other parameters, each checked: `query.term` (free
text); `filter.overallStatus=COMPLETED` (26 → 10 for the query below);
`query.locn` and `query.spons` (all pancreatic cancer trials: 5,143, with
`query.locn=Houston` 456, with `query.spons=Anderson` 104).

For condition pancreatic cancer and intervention metformin it returned 26 trials.
`paperclip search -s trials/us -n 250` for the same returned 201 trials, of which
12 were among the 26; the other 14 are in paperclip and are found by NCT number,
so the gap is ranking, not coverage. **For a list of the trials of X in Y, use
this API**, then read each trial in paperclip or on the registry page.

## PubTator3 (not wired in)

```
https://www.ncbi.nlm.nih.gov/research/pubtator3-api/search/?text=@CHEMICAL_Metformin%20AND%20@DISEASE_Pancreatic_Neoplasms&page=1
```

NCBI's entity-normalized search over PubMed and PMC: gene, chemical, disease,
species, variant and cell line mentions mapped to identifiers, so a gene's
synonyms or a variant's spellings all match. JSON with `pmid`, `title`, `doi`.
Answered 200 with no key. Use it when the term has many spellings (gene symbols,
HGVS variants).

## What none of this reaches

Embase, Scopus, Web of Science, CINAHL, PsycINFO and the Cochrane Library need
an institutional subscription and have no free API. A systematic review that
names one of them as a required source cannot be completed from here; say so
rather than reporting PubMed plus Europe PMC as the full search.
