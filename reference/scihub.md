# Sci-Hub — the last rung

Sci-Hub hosts copies that were not lawfully redistributed. It is here because the
alternative, when every legitimate channel has failed, is verifying a claim
against an abstract instead of against what the paper actually says — and a
misquoted source is a worse outcome than an awkward one. That reasoning holds
only under the conditions below.

**Rules, not preferences:**

- Reach it only after paperclip, arXiv, Unpaywall/OpenAlex, CORE, Europe PMC,
  publisher free text, Google Scholar and web search have all come up empty.
  `scripts/allpapers-locate` returning nothing is the signal.
- What you fetch is **verification-only**: read it, quote it, record the quote.
  Keep the file in a scratch directory. **Never commit it**, never redistribute
  it, never attach it to anything.
- The reference in the `.bib` file and in the paper carries the canonical
  locator — DOI, journal, arXiv ID. The mirror URL appears **only** in
  `verification/bib.md` as the access record.
- **Cross-check against Crossref before trusting it.** Mirrors do occasionally
  pair the wrong PDF with a DOI. Compare the title page, volume and pages
  against `api.crossref.org/works/{doi}`.
- If it fails, record `NO-SOURCE` with the channels tried. Do not quietly drop
  to abstract-level verification without saying so.

## scihub-cli

`~/.local/bin/scihub-cli`, v0.5.1. Despite the name it is a **multi-source
downloader that tries the open sources first** and only falls through to Sci-Hub.
Its own banner lists: OpenAlex, Europe PMC, Unpaywall, arXiv, CORE, Sci-Hub.

```bash
printf '%s\n' '10.1038/nature14539' > dois.txt
scihub-cli dois.txt --output papers
```

Input is a text file of DOIs, identifiers or URLs, one per line.

The email for Unpaywall is already stored in `~/.scihub-cli/config.json`, so
**never pass `--email`** — and never write the address into a committed file.

Useful options: `-p/--parallel` (default 16), `-t/--timeout` (15s),
`-r/--retries` (3), `--enable-core` (CORE is off by default to dodge its rate
limit), `--to-md` with `--md-backend` (default `pymupdf4llm`) to convert to
Markdown, `--trace-html` to keep the HTML of failed attempts, and
`--no-fast-fail` to allow the slower 403-bypass path.

### Gating a "downloaded" claim

Measured on 2026-08-25 — all three cases run and the exit code read directly,
not through a pipe:

| Case | Exit | `download-report.json` |
|---|---|---|
| 1 identifier, succeeded | **0** | not written |
| 1 identifier, failed | **1** | written |
| 2 identifiers, 1 ok 1 failed | **1** | written |

So: exit 0 means *every* identifier succeeded, and the report file appears only
when at least one failed. Check the exit code, then check the output file
exists — and read the report when the exit code is nonzero. Never announce a
download without both.

The report holds `summary {total, download_success, download_failures,
md_attempted, md_success, md_failures}` and a `download_failures[]` array in
which each entry carries `source_attempts[]` — per source, its `phase`
(`fast_parallel` / slow), `priority`, `status` and `duration_ms`. That array is
what tells you whether the OA channels were genuinely exhausted or merely timed
out.

### How it routes

From an observed run:

```
[Router] Year 2007 < 2021, using fast OA -> OpenAIRE -> Sci-Hub
[Router] Parallel query to 5 sources: ['OpenAlex','Unpaywall','Europe PMC OA','Europe PMC','arXiv']
[Router] SUCCESS: Using OpenAlex (parallel, priority)
```

It branches on publication year, fires the fast OA sources concurrently, then
tries the slow ones, then Sci-Hub. Because those fast sources are the same ones
`allpapers-locate` already queried, running scihub-cli after a failed locate is
mostly a Sci-Hub attempt with a second OA pass for free.

### Measured defects

- **The block-page detector false-positives on live mirrors.** Observed:
  `Detected blocked mirror page for https://sci-hub.ee` → `Added
  https://sci-hub.ee to blacklist for 300s` → the same for `sci-hub.mk` → `All
  mirrors returned block pages; cooling down for 120s`. The blacklist persists
  across runs, so an immediate retry dies with all mirrors unavailable. Wait it
  out rather than hammering.
- **`-m/--mirror` does not pin the mirror.** With and without the flag the log
  showed the same `Finding working mirror... [Tier 1] Testing easy mirrors in
  parallel...` discovery, and nothing acknowledged the requested host. Once
  chosen, a mirror is cached for 3600s.
- **`--fast-fail` is the default** and skips the 403 bypass
  (`Fast-fail enabled: skipping 403 bypass for page access`). Pass
  `--no-fast-fail` if a 403 is the only thing in the way.

### Mirror reachability, measured 2026-08-25

| Host | Result |
|---|---|
| `sci-hub.se` | DNS does not resolve |
| `sci-hub.st` | TLS certificate fails validation (no usable common name) |
| `sci-hub.ru` | TLS certificate fails validation |
| `sci-hub.box` | HTTP 200 |
| `sci.bban.top` | HTTP 200 |
| `sci-hub.ee`, `sci-hub.mk` | reachable by the CLI, served block pages |

The `.st` and `.ru` failures are certificate problems, not outages — a browser
would warn rather than fail. Do not work around it by disabling verification.

### Manual fallback

When the CLI cannot get there, the mirror article page embeds the PDF at

```
https://sci.bban.top/pdf/<DOI>.pdf
```

Fetch that directly with a browser `User-Agent`.

### Old scans have no text layer

Pre-1990 journal PDFs are frequently image scans: `pdftotext` returns roughly
nothing. Read those visually with the Read tool and re-check every quote
character by character before it goes into `verification/bib.md`. An OCR
restoration goes in brackets and is marked as such.
