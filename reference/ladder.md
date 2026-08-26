# The source priority ladder

Two orderings operate at once. Do not confuse them.

**Format order** decides which copy to take once you have found several:

    extracted text  >  LaTeX  >  JATS/XML  >  HTML  >  PDF (text layer)  >  PDF (scan)

**Source order** decides where to look, and in what sequence. That is the ladder
below. `scripts/allpapers-locate` collapses rungs 1–3 into a single concurrent
query, so in practice you run it first and only walk the rest by hand.

---

## Rung 1 — paperclip

First because the full text is already extracted, sectioned and line-numbered, so
a quote comes back citable as `#L45-L52` with no parsing at all, and because the
index is fast.

```bash
paperclip lookup doi 10.1038/nature14539
paperclip lookup arxiv 1706.03762
paperclip search -s papers -n 250 "<one or two sentences describing the method>"
```

**Look up arXiv papers by their arXiv ID, not by DOI.** paperclip indexes them
under `arx_1706.03762`; the DataCite DOI arXiv mints (`10.48550/arXiv.1706.03762`)
returns nothing.

**Fall through to rung 2 when:** the paper is not indexed; the rate limit or free
usage allowance is exhausted; `paperclip` is not installed and the user does not
want to install it; or the command errors or times out. A rate-limit or quota
message is a fall-through, not a failure to report — keep going down the ladder
and mention it at the end. If the user is hitting the limit often, point them at
<https://paperclip.gxl.ai/keys> for an API key.

`lookup` exits 0 even when it found nothing, so gate on the output text
containing a document ID, never on the exit code.

## Rung 2 — arXiv LaTeX source

If the paper is on arXiv, stop here: this is the best format that exists.

```bash
dir=$(scripts/arxiv-source 1706.03762)
```

Preprints differ from the published version, sometimes materially. When the claim
depends on the final text, say which version you read. See `arxiv.md`.

## Rung 3 — the open indices

Query all of them; they disagree about *where* the free copy is, and one will
often know a repository copy the others missed. `allpapers-locate` does this
concurrently.

| Index | Best at | File |
|---|---|---|
| Unpaywall | is there a legal free copy of this DOI, and where | `unpaywall.md` |
| OpenAlex | same data plus identifiers, citations, and non-DOI works | `other-indices.md` |
| CORE | repository deposits, sometimes with extracted full text | `core.md` |
| Europe PMC | JATS XML for anything with a PMCID — very parseable | `other-indices.md` |

Two traps, both measured: CORE will hand you a record that carries the requested
DOI but is a different paper, so check the title; and without an API key CORE puts
`"Not available for public API users."` in the `fullText` field rather than
leaving it empty.

**OpenAlex now hosts full text of its own**, which makes this rung better than it
used to be. A work object carries `has_content` and `content_urls`, and where
`has_content.grobid_xml` is true you can download a GROBID TEI XML parse of the
paper — structured text, so it outranks any PDF beside it. Counts measured against
the live API on 2026-08-25: **48,978,284** works with GROBID XML and **52,396,004**
with a cached PDF. Downloads need a free API key and cost $0.01 per file against
the account's daily budget; without a key `content.openalex.org` returns HTTP 401.
GROBID does no OCR, so a scanned paper yields nothing, and its header and reference
parsing has known errors — trust the body text, re-check the metadata against
Crossref.

The same change metered the rest of OpenAlex. Every response now carries
`x-ratelimit-limit-usd` and friends: anonymous callers get **$0.10 per day**, which
is 1000 metadata lookups at 1 credit each, resetting at midnight UTC. A free
account key raises that to $1/day. That is enough for ordinary work and not enough
for a bulk sweep, so get a key at <https://openalex.org/users> — `allpapers-setup`
stores it and `allpapers-locate` uses it.

## Rung 4 — Google Scholar

Only once rungs 1–3 have come up empty. Scholar indexes material the open indices
miss — theses, technical reports, old scanned journal runs, author copies on
personal pages — and its `[PDF]` link points at a free copy when one exists.

There is no official API. `scholar.md` has the scraping recipe, verified against a
live page, and the paid SerpApi alternative. Scholar rate-limits aggressively and
will serve a CAPTCHA; when that happens, stop rather than working around it.

## Rung 5 — web search

For the cases Scholar also misses: a publisher's own free-access page, a lab or
personal site, a conference proceedings archive, a government or standards body.
Search the exact title in quotes, plus `filetype:pdf` or the author's surname.

Anything found here needs its identity confirmed against the metadata from rung 3
before it is quoted — a file with the right title may be a different version, a
preprint, or a slide deck.

## Rung 6 — Sci-Hub, last resort only

Only when rungs 1–5 have all failed and the paper genuinely has no open copy.
This is not an open service and holds unauthorised copies. See `scihub.md`.

Hard rules, from the project standards:

- Verification-only. Quote it in `verification/bib.md` and nowhere else.
- The mirror URL goes in `verification/bib.md`, never in the `.bib` entry.
- Keep the file outside the repository. Never commit it.
- APS `journals.aps.org` blocks automated fetching. Do not fight it.

---

## When every rung fails

Record `NO-SOURCE` in `verification/bib.md` with the list of channels tried, and
say so plainly in your answer. Do not quote from memory, do not reconstruct an
abstract, and do not describe a paper you were unable to open. An honest
"I could not get the full text of this one" is worth more than a confident
paraphrase of something you never read.

One thing is still worth trying at that point: OpenAlex deposits abstracts for
papers whose full text is free nowhere, stored as `abstract_inverted_index`.
Rebuild it by sorting word positions, and verify the claim against the abstract —
labelled as abstract-level verification, not full text. `verification.md` has the
rule; `other-indices.md` has the field.
