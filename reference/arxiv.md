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

The script normalises `arXiv:` prefixes, version suffixes and full URLs, then
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

## HTML alternative

```
https://arxiv.org/html/<id>            # LaTeXML rendering, no version needed
https://ar5iv.labs.arxiv.org/html/<id> # independent fallback
```

Confirmed available for 1205.7018 (2012), 1706.03762 (2017) and 2006.11239 (2020),
so it is **not** restricted to recent papers as is often assumed — arXiv has
backfilled a large part of the archive. It is still not universal:
`hep-th/9711200` (1997) returns 404. Use it when you want structure without
unpacking a tarball; prefer the source when equations matter.

## Metadata: the Atom API

```bash
curl "http://export.arxiv.org/api/query?id_list=1706.03762"
curl "http://export.arxiv.org/api/query?search_query=all:transformer&start=0&max_results=50"
```

Returns Atom XML with title, authors, abstract, categories, DOI and journal
reference. `<opensearch:totalResults>` gives a result count, but note it reflects
the query, not the corpus — `search_query=all:e` returned 500,099, which is a
query artifact and not the size of arXiv.

Send a descriptive User-Agent and do not hammer it; arXiv asks for roughly one
request every three seconds.

## Identifier forms

- New style, 2007 onward: `1706.03762`, optionally `v5`
- Old style, before 2007: `hep-th/9711200`, `math/0211159`, `cond-mat/0001001`
- arXiv mints a DataCite DOI `10.48550/arXiv.<id>`. Crossref-based tools —
  Unpaywall included — often do not know it. Look papers up by arXiv ID.
