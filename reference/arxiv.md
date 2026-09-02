# arXiv

arXiv holds 3,146,378 cumulative submissions through 2026-08, counted by summing
`https://arxiv.org/stats/get_monthly_submissions` (checked 2026-08-25). It matters
out of proportion to its size because it serves the **submitted source**, which for
almost everything is LaTeX.

## Why LaTeX beats the PDF

The PDF is a rendering. Equations become glyph runs, section structure becomes
font changes, multi-column text extracts out of order, and ligatures merge. The
LaTeX source has the equations as equations, `\section` markers, `\label`/`\ref`
pairs, and the bibliography as structured entries. When a claim turns on an
equation, the source is the only copy worth quoting from.

## Getting the source

```bash
dir=$(scripts/arxiv-source 1205.7018)     # unpacks into a mktemp directory
dir=$(scripts/arxiv-source arXiv:1706.03762v5)
dir=$(scripts/arxiv-source hep-th/9711200)
scripts/arxiv-source 2304.04556 -o /some/path
```

The script normalizes `arXiv:` prefixes, version suffixes and full URLs, then
fetches `https://arxiv.org/src/<id>`. Exit 3 means the submission was PDF-only.

`https://arxiv.org/e-print/<id>` serves the same bytes and is an equivalent
entry point (both confirmed returning `application/gzip` for 1205.7018).

### The three payload shapes

`/src/` is **not** always a tarball. All three were confirmed against live papers:

| Shape | MIME | Example | Handling |
|---|---|---|---|
| gzipped tar of the submission | `application/gzip` | 1706.03762, 1205.7018 | `tar -xzf` |
| a single gzipped `.tex`, no tar | `application/gzip` | hep-th/9711200 | `gunzip -c > name.tex` |
| PDF only, no source | `application/pdf` | rare | fall back to PDF extraction |

The first two share a MIME type, so sniffing the type is not enough — try
`tar -tzf` and fall back to `gunzip` when it fails. That is what the script does.

A bad ID returns HTTP 404 with an HTML error page, which the script reports rather
than unpacking.

### Finding the main file in a multi-file submission

Submissions routinely have ten or more `.tex` files plus figures and style files:

```bash
command grep -l '\documentclass' "$dir"/*.tex          # the main file
command grep -hoE '\\(input|include)\{[^}]+\}' "$dir"/*.tex   # what it pulls in
```

Read the main file for structure, then the `\input` targets for the sections you
need. `.bbl` files hold the resolved bibliography when there is no `.bib`.

## HTML — the second-best parseable format

```
https://arxiv.org/html/<id>            # LaTeXML rendering
https://ar5iv.labs.arxiv.org/html/<id> # independent fallback
```

The version suffix is optional and accepted either way — `1706.03762` and
`1706.03762v1` both return 200.

It is **not** restricted to recent papers, as is often assumed. `math/0010150`
(2000), `1205.7018` (2012), `1706.03762` (2017) and `2006.11239` (2020) all
return 200; arXiv has backfilled a large part of the archive.

### HTML is a subset of source availability, not an alternative to it

arXiv converts the HTML **from the submitted TeX** — from their own accessibility
page, "90% of submissions to arXiv are in TeX format", and the conversion is what
produces `/html/`. So a paper with no TeX has no HTML. The two endpoints do not
back each other up, and reaching for `/html/` because `/src/` failed is a wasted
request.

Measured over 45 papers on 2026-08-26, checking both endpoints for each:

| `/src/` | `/html/` | n | What it is |
|---|---|---|---|
| gzip (TeX) | 200 | 33 | The normal case — both formats available |
| **`application/pdf`** | **404** | 6 | PDF-only submission: no TeX exists, so no HTML either |
| gzip (TeX) | 404 | 2 | Older paper whose HTML has not been backfilled (`hep-th/9711200`, `cs/0006013`) |
| 404 | 404 | 1 | Wrong identifier form — an old-style ID with its slash stripped |

**`/html/` succeeded where `/src/` failed in none of the 45.** The 6 PDF-only
papers are the clean test of the direction, and they went 6 for 6 the other way.
The 10% PDF-only rate matches arXiv's own "90% are TeX" figure.

What follows for the skill:

- **A 200 from `/src/` does not mean you have LaTeX.** PDF-only submissions are
  served as `application/pdf` from the same URL. `scripts/arxiv-source` checks the
  payload type and exits 3 for these; `scripts/allpapers-locate` checks it too and
  labels the location `pdf` rather than `latex`, so a PDF cannot sort to the top of
  a ranking that exists to avoid PDFs.
- **When `arxiv-source` exits 3, do not try `/html/`** — it will 404. Extract text
  from the PDF.
- **Reach for `/html/` when you want structure without unpacking a tarball**, or
  when the submission is large and messy. Prefer the source when equations matter:
  LaTeXML rewrites maths into MathML, and the original macros are gone.

## Metadata: the Atom API

```bash
curl "http://export.arxiv.org/api/query?id_list=1706.03762"
curl "http://export.arxiv.org/api/query?search_query=all:transformer&start=0&max_results=50"
```

Returns Atom XML with title, authors, abstract, categories, DOI and journal
reference. `<opensearch:totalResults>` gives a result count, but note it reflects
the query, not the corpus — `search_query=all:e` returned 500,099, which is a
query artifact and not the size of arXiv.

Send the Chrome User-Agent every fetch in this skill sends (see **Every web fetch
sends a Chrome User-Agent** in `SKILL.md`), and do not hammer it: arXiv asks for
roughly one request every three seconds, and that restraint — not the agent
string — is the part that matters to them.

## Identifier forms

- New style, 2007 onward: `1706.03762`, optionally `v5`
- Old style, before 2007: `hep-th/9711200`, `math/0211159`, `cond-mat/0001001`
- arXiv mints a DataCite DOI `10.48550/arXiv.<id>`. Crossref-based tools —
  Unpaywall included — often do not know it. Look papers up by arXiv ID.
