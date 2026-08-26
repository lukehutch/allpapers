---
name: allpapers
description: Find and retrieve the full text of scientific papers from paperclip, arXiv LaTeX source, CORE, Unpaywall, OpenAlex, Europe PMC, Google Scholar, Gemini grounded search and Sci-Hub as a last resort. Use when asked to look up a paper, get its full text, search the literature by keyword or by meaning, check what a paper actually says, verify a citation, or build a bibliography. Always prefers parseable text formats over PDF.
---

# allpapers

Locate and read scientific papers, then leave a verifiable record of what was
found. Three rules govern everything below.

**Rule 1 — prefer parseable source.** Always take the most structured format
available, in this order:

    already-extracted text  >  LaTeX source  >  JATS/XML  >  GROBID TEI  >  HTML  >  PDF  >  scanned PDF

PDF extraction silently mangles equations, loses section boundaries, splits
ligatures and reorders multi-column text. LaTeX and JATS do not. Reaching for a
PDF when LaTeX exists means quoting from a worse copy for no reason.

**Rule 2 — follow the ladder.** Cheap, open, already-extracted sources first;
bootleg copies only when nothing else has it. `reference/ladder.md` has the full
procedure, including what to do when a rung fails.

**Rule 3 — nothing is cited until it is recorded.** Any paper used to support a
claim goes into `verification/bib.md` with its composite BibTeX entry, its
abstract, a justification, and verbatim quotes. Papers you looked at and
*rejected* get an entry too. See **Recording what you found** below.

## First run

```bash
scripts/allpapers-setup --check
```

Exit 0 means everything essential is configured. Exit 1 means an email address is
missing — Unpaywall's API rejects requests without one, and it puts OpenAlex,
Crossref and NCBI in their polite pools.

If something is missing, **ask the user for it in conversation**, then store it:

```bash
scripts/allpapers-setup --set email=them@example.org core_api_key=... \
                              openalex_api_key=... gemini_api_key=...
```

Never ask twice — the config persists in `~/.config/allpapers/config.json` and is
mirrored into `~/.scihub-cli/config.json`. Never write these values into a file
that gets committed.

| Credential | Cost | What it buys |
|---|---|---|
| **email** | — | Required. Unpaywall 422s without it; polite pools elsewhere |
| **CORE key** | free, instant | Without it CORE returns `"Not available for public API users."` instead of full text, and allows 10 requests per 10 minutes |
| **OpenAlex key** | free, instant | Raises the daily budget from $0.10 to $1, and is **required** to download OpenAlex's cached GROBID TEI XML — a structured parse existing for ~49M works |
| **Gemini key** | free tier | Enables `allpapers-search --gemini`, grounded web search over the open web. Optional |
| **NCBI key** | free | eutils at 10 requests/sec instead of 3. The anonymous limit is enforced and returns HTTP 429 mid-sequence, which reads as a lookup failure |
| **Semantic Scholar key** | free | Higher rate limits on the identifier-bridge endpoint |
| **SerpApi key** | 250/month free | Only if Google Scholar blocks and the paper matters |

Get them at <https://core.ac.uk/services/api#form>, <https://openalex.org/users>,
<https://aistudio.google.com/apikey>, <https://www.ncbi.nlm.nih.gov/account/>.

If paperclip is not installed:

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
paperclip login          # browser sign-in
```

If the user exhausts paperclip's free usage, they can get an API key at
<https://paperclip.gxl.ai/keys> and set `PAPERCLIP_API_KEY`.

## The three kinds of lookup

Decide which one you are doing before you start; they have different tools and
very different failure modes.

### 1. Exact lookup — you know which paper you want

```bash
scripts/allpapers-locate 10.1038/nature14539
scripts/allpapers-locate arXiv:1706.03762
scripts/allpapers-locate PMC3084216
scripts/allpapers-locate 26017442                      # PMID
scripts/allpapers-locate "Attention is all you need"   # resolves the title first
scripts/allpapers-locate 10.1038/nature14539 --json    # for scripting
```

Queries paperclip, arXiv, Unpaywall, OpenAlex, CORE and Europe PMC at once and
ranks every free location it finds by format. Accepts DOIs, arXiv IDs (new and
old style, with or without a version suffix), PMIDs, PMCIDs, arXiv/DOI URLs, and
titles. Exit 1 means nothing free was found — the signal to move down to Google
Scholar and below.

**Watch stderr.** On a title lookup it warns when several papers share a title or
when no exact match was found; free-text title search returns near-misses readily.
Confirm the identifier before citing anything.

**Take `identity unconfirmed` seriously.** OpenAlex and CORE attach repository
records to a work by matching, and the match is sometimes a different article that
merely *cited* it — measured, not hypothetical. Any row the tool cannot prove is
the right paper (not a publisher `publishedVersion`, and no DOI, arXiv ID or PMCID
in its URL) carries that marker. Open it and check the title before you quote it.
This is exactly the misattribution that `verification/bib.md` requirement 4 exists
to catch.

Rate-limit and withheld-full-text messages print as `note:` lines and are not
counted as locations, so exit 1 really does mean nothing was found. In `--json`
they come back under `notices` rather than `locations`.

### 2. Keyword search — you know the words that will appear

```bash
scripts/allpapers-search --mode keyword "CRISPR base editing off-target" -n 250
scripts/allpapers-search --mode keyword --bool "(prime OR base) AND editing"
scripts/allpapers-search --mode keyword -e -t "Attention Is All You Need"
```

Lexical BM25. Use it when the terminology is settled and you want documents
containing those exact strings.

### 3. Semantic search — you know the idea, not the words

```bash
scripts/allpapers-search --mode semantic \
  "correcting for systematic under-reporting when the missingness mechanism is unknown"
scripts/allpapers-search --mode analogical "..."   # same method, unrelated field
scripts/allpapers-search --mode all "..."          # all four rankers, merged
```

**Query wording matters more than any flag.** The embedding model is fine-tuned on
abstracts, so the best input is a full abstract pasted verbatim; the next best is
one or two sentences describing the *method or problem structure* rather than the
topic. Bare keywords are the weakest possible input to a semantic ranker.

`--mode analogical` finds the same structural method in a different field, which
is the one search worth running even when you think you are done — the useful
analogy is usually in the community you would not have searched.

**Always pass `-n 250`.** paperclip's real default is 20 despite its `--help`
claiming 100, and nothing warns you the rest existed. `allpapers-search` defaults
to 250 for this reason; do not lower it while sweeping.

**Think about sort order.** `--sort date` is for recency sweeps, not for finding
the single best source — it discards relevance entirely. It is also incompatible
with `--min-similarity`. See `reference/search.md`.

Add `--gemini` to run Gemini grounded web search alongside paperclip, in parallel.
It reaches the open web — preprints, theses, lab pages, standards documents —
that paperclip's four backends do not index. It returns *claims with citations*,
so treat every result as a lead to verify, never as a source. `--gemini-only`
skips paperclip.

## Getting the full text

### arXiv LaTeX source — the best format that exists

```bash
dir=$(scripts/arxiv-source 1205.7018)     # unpacks into a mktemp directory
ls "$dir"/*.tex
```

The main file is usually the `.tex` containing `\documentclass`, or the one
`\input`/`\include` lines point into. Exit 3 means the author submitted a PDF only
and there is no LaTeX to read. See `reference/arxiv.md` for the three payload
shapes, the HTML alternative for recent papers, and how to find the main file in a
multi-file submission.

### Everything else

- **paperclip** — `paperclip cat /papers/<id>/content.lines`, or better, read only
  what you need: `paperclip grep <pattern> /papers/<id>`, `paperclip scan`,
  `paperclip ls /papers/<id>/sections/`. Line numbers make quotes citable as
  `#L45-L52`. Reading one section costs roughly 200 tokens against 40k for a whole
  paper, so never `cat` a paper you can grep. See `reference/paperclip.md`.
- **Europe PMC JATS XML** — `curl` the `fullTextXML` URL. Authored structure:
  sections, equations, references. Far cleaner than the PDF of the same article.
- **OpenAlex GROBID TEI XML** — when `allpapers-locate` lists an `OpenAlex content`
  row, that is a machine parse of the paper's own PDF as XML. Costs $0.01 against
  the OpenAlex budget. It does no OCR, so it is empty for scans, and its header and
  reference parsing makes mistakes — trust the body, re-check metadata elsewhere.
- **PDF, when unavoidable** — `pdftotext -layout file.pdf -`. If that returns
  almost nothing, the PDF is a scan with no text layer: read it visually with the
  Read tool and re-check every quote character by character.

### When nothing free is found

Work down `reference/ladder.md`: Google Scholar (`reference/scholar.md`), then web
search, then `reference/scihub.md` as the last resort. Do not skip rungs to get to
the bottom faster.

**A Google Scholar miss is often not a miss.** Scholar refuses some callers with a
full-size HTTP 200 page containing no results and no CAPTCHA. Check the page is a
real results page before recording an absence — `reference/scholar.md` has the
three markers that distinguish a block from an empty result set.

## Recording what you found

Every paper that informs a claim must end up in `verification/bib.md`, and its
files in `verification/source/<citationKey>/`. `reference/verification.md` is the
authority on the format; this is the workflow.

### For an exact lookup you already know you want

```bash
scripts/allpapers-fetch 10.1038/nature14539 \
  --justification "Defines the depth-of-representation argument cited in §2." \
  --claim "Deep learning discovers structure in high-dimensional data" \
  --quote "Deep learning allows computational models ... to learn representations of data with multiple levels of abstraction@#L54-L56"
```

Downloads source and PDF into `verification/source/<key>/`, builds the composite
BibTeX entry, and writes the `verification/bib.md` record.

### For anything found by keyword or semantic search — stage first

A search returns candidates, not sources. Never write a search result straight
into the permanent record.

**Step 1 — stage.** Downloads source and PDF to a temp directory and writes
nothing permanent:

```bash
scripts/allpapers-fetch arXiv:2401.12345 --stage
```

It prints the indexes consulted, the artefacts saved, the abstract, the composite
BibTeX entry, and then the two commands to choose between, with the staged path
already filled in:

```
Files: /tmp/allpapers-Author_2024abc-k7yfvxuo/

Staged only — nothing written to verification/. Judge the paper, then:
  keep:   allpapers-fetch arXiv:2401.12345 --promote /tmp/allpapers-... --into verification --justification '...'
  drop:   allpapers-fetch arXiv:2401.12345 --reject --into verification --justification '...'
```

**Step 2 — read what was staged and decide.** The whole point of the step: the
abstract and full text are on disk, so the judgement is made on the paper rather
than on a search snippet.

**Step 3 — promote or reject**, copying the command it printed and adding your
reasoning:

```bash
scripts/allpapers-fetch arXiv:2401.12345 --promote /tmp/allpapers-Author_2024abc-k7yfvxuo \
  --justification "Gives the error bound quoted in §4." \
  --quote "the estimator converges at rate n^{-1/2}@#L211"

scripts/allpapers-fetch arXiv:2401.12345 --reject \
  --justification "Uses the same term for an unrelated optimisation problem; no bearing on the claim."
```

To script this rather than read it, use `--stage --json` and take the `staged`
key; the human report goes to stdout as prose and contains no bare path line, so
`$(...)` around a plain `--stage` captures the whole report, not a directory:

```bash
stage=$(scripts/allpapers-fetch arXiv:2401.12345 --stage --json |
        python3 -c 'import json,sys; print(json.load(sys.stdin)["staged"])')
```

Each `--stage` run downloads again into a fresh temp directory, so stage once and
keep the path rather than re-staging to recover it.

**When to record a rejection.** If you fetched the paper and read it to find out,
record it — that reasoning is worth exactly as much to the next reader as an
inclusion, and stops the same dead end being re-explored. If the title and
abstract alone made it obviously irrelevant, do not: an entry per search hit is
noise, not provenance.

### What goes in every record

`allpapers-fetch` fills these in, but you supply the judgement:

- **The composite BibTeX entry** — merged field by field across INSPIRE-HEP,
  Crossref, DataCite, arXiv, PubMed and Scholar, because no single index is right
  about everything. This is the canonical entry: the `.bib` file copies it, not the
  other way round. Disagreements between indices are printed rather than silently
  resolved. See `reference/bibtex.md`.
- **All source URLs**, not one — metadata and files often come from different
  places, and the record has to show every channel actually used.
- **The abstract**, whenever one is available anywhere.
- **A justification** saying why the paper is or is not relevant.
- **Verbatim, source-verified quotes** with locators, for every claim the citing
  text makes about the paper.

Two rules from `reference/verification.md` that bind while retrieving, not just
while writing:

- Quote only from text actually fetched in this session. Never reconstruct a quote
  from memory of a paper.
- Copies fetched from a shadow library are verification-only. Quote them in
  `verification/bib.md`, record the mirror URL there and never in the `.bib` entry,
  keep the files outside the repository, and never commit them.

Mathematical claims get the same treatment in `verification/equations.py` —
recomputed independently, not transcribed.

## Report at the end

Finish any lookup by telling the user, explicitly:

1. **Every source consulted, in order, with its outcome** — including the ones that
   returned nothing, and including rungs skipped because an earlier one succeeded.
   "paperclip: 3 hits" and "CORE: rate-limited, not consulted" are both findings.
2. **Where the search stopped and why** — found what was needed, or exhausted the
   ladder. If it exhausted the ladder, say what the last resort returned.
3. **The full composite BibTeX entry** for every paper found, as it was written to
   `verification/bib.md`.
4. **Anything unverified** — an `identity unconfirmed` location that was used, a
   field only one index carried, a quote taken from a PDF text layer rather than
   source, a Scholar result that could not be checked because Scholar was blocking.

`scripts/allpapers-locate --json` and `scripts/allpapers-bibtex --json` give you
the material for 1 and 3 without re-running anything.

## Tools

| Tool | What it does |
|---|---|
| `scripts/allpapers-setup` | First-run credential setup and status check |
| `scripts/allpapers-locate` | One paper → every free full-text location, ranked most-parseable first |
| `scripts/allpapers-search` | Keyword, semantic, hybrid and analogical search, optionally with Gemini grounded web search |
| `scripts/arxiv-source` | arXiv submitted source → unpacked LaTeX in a temp directory |
| `scripts/allpapers-bibtex` | Composite normalised BibTeX merged across every index that has the work |
| `scripts/allpapers-fetch` | Fetch source + PDF, stage or promote, and write the `verification/bib.md` record |

## Reference files

| File | Contents |
|---|---|
| `reference/ladder.md` | The full priority ladder and failure handling |
| `reference/paperclip.md` | paperclip CLI, its REST API, and measured defects |
| `reference/search.md` | Ranking modes, result limits, sort order, query wording |
| `reference/arxiv.md` | LaTeX source retrieval, payload shapes, HTML, the Atom API |
| `reference/core.md` | CORE API v3, auth, rate limits, data-quality traps |
| `reference/unpaywall.md` | Unpaywall API, response shape, the broken search endpoint |
| `reference/other-indices.md` | OpenAlex, Crossref, Europe PMC, Semantic Scholar, NCBI, DOAJ, OpenAIRE |
| `reference/scholar.md` | Google Scholar scraping, the silent block, SerpApi |
| `reference/gemini.md` | Gemini grounded search: endpoints, request shapes, citation extraction |
| `reference/bibtex.md` | How the composite entry is merged, the per-field trust order, normalisation |
| `reference/scihub.md` | scihub-cli, its defects, and the manual fallback |
| `reference/verification.md` | `verification/bib.md` and `verification/equations.py` |
