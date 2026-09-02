---
name: allpapers
description: Find and retrieve the full text of scientific papers from paperclip, arXiv LaTeX source, CORE, Unpaywall, OpenAlex, Europe PMC, Google Scholar, Gemini grounded search and shadow libraries (LibGen, Sci-Hub, Anna's Archive, Z-Library) as a last resort. Use when asked to look up a paper, get its full text, search the literature by keyword or by meaning, check what a paper actually says, verify a citation, or build a bibliography. Always prefers parseable text formats over PDF.
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

`scripts/allpapers-setup --check`, and `scripts/allpapers-setup` with no
arguments, print the registration URL for every one of these plus the services
that need no key at all. Read the URL out of the tool rather than from memory —
it is the one place that is kept current. Any setting can also come from its env
var: the key name in upper case, except `email`, whose variable is
`ALLPAPERS_EMAIL`.

The Gemini key is only needed for the API backend. If `agy` (Google Antigravity)
is installed, `allpapers-search --gemini` falls back to it automatically and uses
the user's existing Antigravity login instead — see below.

If paperclip is not installed:

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
paperclip login          # browser sign-in
```

If the user exhausts paperclip's free usage, they can get an API key at
<https://paperclip.gxl.ai/keys> and set `PAPERCLIP_API_KEY`.

## Every web fetch sends a Chrome User-Agent

**Every HTTP request this skill makes — API call, PDF download, HTML scrape,
mirror probe — must carry a current Chrome User-Agent string:**

```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36
```

Use it in `curl -A "..."`, in a `User-Agent` header, and in anything you write ad
hoc. The scripts already send it, from one constant in `scripts/allpapers-locate`
(`CHROME_UA`, imported by `allpapers-bibtex`, `allpapers-fetch` and
`allpapers-search`, mirrored in `allpapers-mirrors` and `arxiv-source`);
`ALLPAPERS_USER_AGENT` overrides it. Bump the Chrome version there when it goes
stale — one edit covers every script but `arxiv-source`, which is shell and keeps
its own copy.

This is not evasion, it is correctness. A descriptive or default agent gets
throttled, refused, or served a stub page by enough of these hosts that the cost
is measured in false negatives, and **the failure is silent**: `curl` with no `-A`
gets an empty page, not an error, and that reads exactly like "the paper is not
here." Google Scholar blocks the default `curl` agent outright, and several
shadow-library mirrors serve an interstitial to anything that does not look like
a browser.

It costs nothing in politeness. Every service that offers a polite pool —
OpenAlex, Crossref, Unpaywall, Europe PMC, NCBI — accepts the contact address as a
`mailto=` or `email=` query parameter, which is the documented alternative to
putting it in the User-Agent, and the scripts send it that way. The one service
that asks for identification rather than an address is arXiv, and what it actually
asks for is restraint: roughly one request every three seconds, which is what to
give it.

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

Queries paperclip, arXiv, Unpaywall, OpenAlex, CORE, Europe PMC and dblp at once
and ranks every free location it finds by format. Accepts DOIs, arXiv IDs (new and
old style, with or without a version suffix), PMIDs, PMCIDs, arXiv/DOI URLs, and
titles. Exit 1 means nothing free was found — the signal to move down to Google
Scholar and below.

**For a computer science paper, dblp is the identity resolver.** Query it with the
title *and the first author's surname*: its index contains no DOIs, so a DOI lookup
returns zero hits whether or not it has the paper, and the title alone is not enough
either — the search is ranked and truncated, so a famous title can match more records
than dblp will rank and leave the paper itself off the list. It holds no full text.
What it contributes
is a precise title match where Google Scholar gives none, the open-access `ee`
link on records it marks open, and the conference booktitle, editors and series
that Crossref frequently has no record of at all. `reference/dblp.md`.

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

If the output says **"no cited sources: this answer is ungrounded"**, the model
answered from its own weights and never ran a search — that is not the same as
"the web had nothing", and nothing in it may be relied on. Re-ask with wording
that forces a search, or use the corpus.

**Two Gemini backends.** `--gemini-backend` picks between them:

| Value | What it uses | When it applies |
|---|---|---|
| `auto` (default) | the API if `gemini_api_key` is set, otherwise `agy` | leave it here |
| `api` | `generativelanguage.googleapis.com` with the key | billed to a Google Cloud account |
| `agy` | the `agy` CLI with the user's Antigravity login | no key, no cloud billing |

The `agy` route matters because a Gemini API key bills a Google Cloud account —
Antigravity or Gemini subscription credits do **not** cover it. A user who has
signed into `agy` already has grounded Google search with nothing more to pay.
The model is `gemini-3.7-flash-high` (override with `ALLPAPERS_AGY_MODEL`).

**`agy` hangs if you run it plainly from a script.** It asks gnome-keyring for
its stored credentials, the unlock dialog takes the terminal, and the run blocks
forever with no output. Present the shell as a remote SSH session with no display
and it falls back to its own token store:

```bash
export DISPLAY=""
export SSH_CLIENT="127.0.0.1 12345 22"
export SSH_TTY="/dev/pts/0"
agy -p "your prompt" --model gemini-3.7-flash-high
```

`allpapers-search` sets those three itself, so `--gemini-backend agy` needs no
setup. Apply the same three exports to **any** other `agy` invocation you make.

## Getting the full text

### arXiv LaTeX source — the best format that exists

```bash
dir=$(scripts/arxiv-source 1205.7018)     # unpacks into a mktemp directory
ls "$dir"/*.tex
```

The main file is usually the `.tex` containing `\documentclass`, or the one
`\input`/`\include` lines point into.

**Exit 3 means the author submitted a PDF only**, so there is no LaTeX to read —
and no `arxiv.org/html/` either, because arXiv converts its HTML from the TeX.
Extract from the PDF rather than spending a request on `/html/`.

Old-style identifiers need their slash: `hep-th/9711200`, not `hep-th9711200`.
paperclip strips it (`arx_math0010150`), and arXiv 404s on that form; both scripts
put it back for you.

### arXiv HTML — the second-best format

`https://arxiv.org/html/<id>` is LaTeXML-converted HTML, available well back into
the archive (`math/0010150` from 2000 returns 200) but not universal. It is a
subset of source availability, never a substitute: measured over 45 papers, it
never once succeeded where `/src/` failed. Use it when you want structure without
unpacking a tarball; prefer the source when equations matter. See
`reference/arxiv.md` for the measured availability table and the payload shapes.

### Everything else

- **paperclip** — read only what you need: `paperclip grep`, `paperclip scan`,
  `paperclip ls /papers/<id>/sections/`, all against `/papers/<id>`. Line
  numbers make quotes citable as `#L45-L52`. Reading one section costs roughly
  200 tokens against 40k for a whole paper, so never read a whole paper you can
  grep — and when you do need all of it, **a bare `cat` truncates at ~1000
  characters**; pass `--full`. Two things to know before quoting: its LaTeX is
  **reconstructed from the PDF**, faithful in meaning but not verbatim, so
  markup quotes come from arXiv source instead; and for pre-2000 papers it
  returns **metadata and abstract only, with nothing marking it as such** —
  `paperclip ls /papers/<id>/sections/` listing no narrative sections is the
  tell. See `reference/paperclip.md`.
- **Europe PMC JATS XML** — `curl` the `fullTextXML` URL. Authored structure:
  sections, equations, references. Far cleaner than the PDF of the same article.
- **OpenAlex GROBID TEI XML** — when `allpapers-locate` lists an `OpenAlex content`
  row, that is a machine parse of the paper's own PDF as XML. Costs $0.01 against
  the OpenAlex budget. It does no OCR, so it is empty for scans, and its header and
  reference parsing makes mistakes — trust the body, re-check metadata elsewhere.
- **PDF, when unavoidable** — use plain `pdftotext file.pdf -` for the body, and
  `pdftotext -layout` only for tables and single-column papers. `-layout`
  preserves the physical line, so on a two-column page it welds the two columns
  together and sentences from opposite sides of the page share a line; plain
  reads the columns in order, but scatters table rows away from their values.
  Both splice the journal running head into the text, and paperclip beats both
  on multi-column layout — `reference/paperclip.md` has the measurement. If
  either returns almost nothing, the PDF is a scan with no text layer: read it
  visually with the Read tool and re-check every quote character by character.

### When nothing free is found

Work down `reference/ladder.md`: Google Scholar (`reference/scholar.md`), then web
search, then `reference/shadow-libraries.md` as the last resort (LibGen first,
then Sci-Hub, then Anna's Archive, then welib/Z-Library; `reference/scihub.md`
covers the scihub-cli wrapper). Do not skip rungs to get to
the bottom faster.

**A Google Scholar miss is often not a miss.** Scholar refuses some callers with a
full-size HTTP 200 page containing no results and no CAPTCHA. Check the page is a
real results page before recording an absence — `reference/scholar.md` has the
three markers that distinguish a block from an empty result set. Scholar's refusals
are usually transient: retry it over the next few minutes as described under
**Transient failures** below rather than writing the rung off on one page.

## Transient failures — retry before believing them

Every service here fails intermittently, and Google Scholar most of all. A failure
is transient until proven otherwise, and service usually comes back within a few
minutes. **Do not record an absence, and do not fall through to the next rung, on
a single failed call.**

Treat as transient and retry:

- any HTTP 5xx, a connection reset, a DNS failure or a timeout;
- HTTP 429, and any rate-limit message — but honor `Retry-After` or
  `x-ratelimit-retry-after` when the response carries one;
- **a success status whose body is an error.** This is the one that gets missed.
  Google Scholar's `The system can't perform the operation now. Try again later.`
  arrives as a well-formed HTTP 200 page with no results and no CAPTCHA; a Sci-Hub
  mirror answers 200 and redirects to an ad landing page. Read the body, not the
  status line.

The procedure: **retry for up to 5 minutes, spaced out — roughly at 15s, 45s, 90s,
3min and 5min — and do other work in between.** Never block on the wait: fire off
the other rungs, the other identifiers, or the next paper while the failing service
recovers, then come back to it. A serial sleep loop wastes the whole five minutes.

After 5 minutes of failures, treat the rung as unavailable, move down the ladder,
and say in the final report which service was down and what it would have been
asked — that is a "could not check", not a "not found".

**A transient failure can reach you as a confident wrong answer.** When one index
in a chain goes down, the code after it may quietly substitute a weaker source
rather than report the outage. Measured 2026-09-02: with OpenAlex briefly
unreachable, resolving the title "Attention is all you need" fell through to a
one-row Crossref title search and returned an unrelated 2025 Springer book chapter
— no error anywhere, just a different paper. `allpapers-locate` now refuses to
resolve a title when OpenAlex did not answer, and says so. Apply the same
suspicion by hand: if a lookup returns something surprising just after a service
failed, re-run it once the service is back before believing it.

Three things are **not** transient, and retrying them only burns time: an
authentication error (HTTP 401/403 from a missing or wrong key — fix the key); a
malformed query the service rejects the same way every time (CORE's HTTP 500 on a
bare quoted phrase is this, not an outage — field-qualify the phrase, see
`reference/core.md`); and a well-formed empty result set from a healthy service,
which is a real miss. `paperclip lookup` exiting 0 with no document ID is also a
real miss, not a failure — it never signals absence any other way.

## Recording what you found

Every paper that informs a claim must end up in `verification/bib.md`, and its
files in `verification/source/<citationKey>/`. `reference/verification.md` is the
authority on the format; this is the workflow.

`verification/` is created **in the current working directory** the first time a
paper is kept, rejected or retired — so run `allpapers-fetch` from the directory
that owns the bibliography, not from wherever you happen to be. Two switches
move or silence it:

| Switch | Effect |
|---|---|
| `--into DIR` | put the directory somewhere else; relative paths resolve against the current directory. `ALLPAPERS_VERIFICATION_DIR` sets the same thing once |
| `--no-record` | create nothing: fetch to a temp directory, print the report, leave no trace. For "what does this paper actually say?" when no claim depends on it |

`--no-record` cannot be combined with `--promote`, `--reject` or `--retire` —
those modes exist only to write the record, so the tool refuses rather than
silently doing nothing.

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
abstract and full text are on disk, so the judgment is made on the paper rather
than on a search snippet.

**Step 3 — promote or reject**, copying the command it printed and adding your
reasoning:

```bash
scripts/allpapers-fetch arXiv:2401.12345 --promote /tmp/allpapers-Author_2024abc-k7yfvxuo \
  --justification "Gives the error bound quoted in §4." \
  --quote "the estimator converges at rate n^{-1/2}@#L211"

scripts/allpapers-fetch arXiv:2401.12345 --reject \
  --justification "Uses the same term for an unrelated optimization problem; no bearing on the claim."
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

`allpapers-fetch` fills these in, but you supply the judgment:

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
   Name any service that was still failing after the 5-minute retry window, and say
   what it would have been asked — that is a gap in coverage, not a negative result.
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
| `scripts/allpapers-install` | Link this skill into Claude Code, Codex and Antigravity; `--check` re-verifies an existing install |
| `scripts/allpapers-setup` | First-run credential setup and status check |
| `scripts/allpapers-locate` | One paper → every free full-text location, ranked most-parseable first |
| `scripts/allpapers-search` | Keyword, semantic, hybrid and analogical search, optionally with Gemini grounded web search via the API or `agy` |
| `scripts/arxiv-source` | arXiv submitted source → unpacked LaTeX in a temp directory |
| `scripts/allpapers-mirrors` | Which shadow-library mirrors are usable right now — verifies content, not status |
| `scripts/allpapers-bibtex` | Composite normalized BibTeX merged across every index that has the work |
| `scripts/allpapers-fetch` | Fetch source + PDF, stage or promote, and write the `verification/bib.md` record (`--into`, `--no-record`) |

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
| `reference/dblp.md` | dblp: CS identity resolution, proceedings metadata, BibTeX, its rate limiting |
| `reference/gemini.md` | Gemini grounded search: the API and `agy` backends, request shapes, citation extraction |
| `reference/bibtex.md` | How the composite entry is merged, the per-field trust order, normalization |
| `reference/scihub.md` | scihub-cli, its defects, and the manual fallback |
| `reference/shadow-libraries.md` | LibGen, Anna's Archive and Z-Library, live mirror status, the traps |
| `reference/verification.md` | `verification/bib.md` and `verification/equations.py` |
