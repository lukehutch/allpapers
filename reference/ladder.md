# The source priority ladder

Two orderings operate at once. Do not confuse them.

**Format order** decides which copy to take once you have found several:

    extracted text  >  LaTeX  >  JATS/XML  >  HTML  >  PDF (text layer)  >  PDF (scan)

**Source order** decides where to look, and in what sequence. That is the ladder
below. `scripts/allpapers-locate` collapses rungs 1–3 into a single concurrent
query, so in practice you run it first and only walk the rest by hand.

---

## Before falling through: is the rung down, or is the paper absent?

A failing service and a missing paper look alike from one call, and confusing them
writes a false "not found" into a citation record. **Every rung on this ladder can
fail transiently, and it usually recovers within a few minutes.** Google Scholar is
the worst offender, but CORE, OpenAlex, Europe PMC, the Sci-Hub and LibGen mirrors,
and paperclip itself all do it.

Retry, for up to 5 minutes, when you see: an HTTP 5xx, a timeout, a connection
reset or DNS failure; an HTTP 429 or a rate-limit message (honoring `Retry-After` /
`x-ratelimit-retry-after` if present); or **an HTTP 200 whose body is an error** —
Scholar's `The system can't perform the operation now. Try again later.` page, or a
mirror that answers 200 with an ad landing page.

Space the attempts out — roughly 15s, 45s, 90s, 3min, 5min — and **do other work in
between**: query the other rungs, the other identifiers, or the next paper while
the failing one recovers. Never sit in a sleep loop.

If it is still failing after 5 minutes, drop to the next rung and record the
service as *unavailable*, not as *no result*. Say so in the final report.

Do not retry an authentication failure (401/403 from a missing or wrong key — fix
the key instead), a query the service rejects deterministically (CORE's HTTP 500 on
a bare unqualified quoted phrase is a query-shape problem, not an outage — see
`core.md`), or a well-formed empty result set, which is a real miss. `paperclip
lookup` exiting 0 with no document ID is a miss too: that is simply how it reports
absence.

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

**Fall through to rung 2 when:** the paper is not indexed; the record is
metadata-only (`paperclip ls /papers/<id>/sections/` lists no narrative sections
— usual for pre-2000 papers, and nothing else marks it); the rate limit or free
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
| dblp | computer science: identity, proceedings metadata, open-access `ee` links | `dblp.md` |

Two traps, both measured: CORE will hand you a record that carries the requested
DOI but is a different paper, so check the title; and without an API key CORE puts
`"Not available for public API users."` in the `fullText` field rather than
leaving it empty.

**dblp is on this rung for computer science only**, and it behaves unlike the rest
of it. It holds no full text and no abstracts, it must be entered by title *and*
first-author surname because its index contains no DOIs and a title alone can be
out-ranked off the result list, and outside CS it is a silent miss — so an empty dblp
result is "not applicable", never a finding. In exchange it does two things nothing
else on the ladder does: it resolves a CS paper's identity precisely, where Scholar
at rung 4 does not, and it carries the booktitle, editors and series of conference
proceedings that Crossref often has no record of. It also rate-limits hard and
silently, answering with a `dblp: error 500` HTML page after about a dozen quick
requests — not the HTTP 429 its own FAQ documents — so query it a couple of times
per paper and no more, and leave at least 4 seconds between requests, which is
the `Crawl-delay` in its `robots.txt`. Anything bulk belongs in its XML dump, not
in the API. `dblp.md`.

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

Only once rungs 1–3 have come up empty. For a computer science paper, try dblp on
rung 3 first and expect it to win: measured on the same title, dblp returned the
right paper at rank 1 of 2 hits where Scholar did not have it in the top 3 of
122,000. Scholar indexes material the open indices miss — theses, technical reports, old scanned journal runs, author copies on
personal pages — and its `[PDF]` link points at a free copy when one exists.

There is no official API. `scholar.md` has the scraping recipe, verified against a
live page, and the paid SerpApi alternative. Scholar rate-limits aggressively and
will serve a CAPTCHA; when that happens, stop rather than working around it — but
its other refusal, the results-free HTTP 200, is transient far more often than not.
Retry that one over the next five minutes, in parallel with other work, before
concluding the rung is unavailable.

## Rung 5 — web search

For the cases Scholar also misses: a publisher's own free-access page, a lab or
personal site, a conference proceedings archive, a government or standards body.
Search the exact title in quotes, plus `filetype:pdf` or the author's surname.

Anything found here needs its identity confirmed against the metadata from rung 3
before it is quoted — a file with the right title may be a different version, a
preprint, or a slide deck.

## Rung 6 — shadow libraries, last resort only

Only when rungs 1–5 have all failed and the paper genuinely has no open copy.
None of these is an open service; all hold unauthorized copies. Full detail,
including every measured trap, is in `shadow-libraries.md`; `scihub.md` covers the
`scihub-cli` wrapper.

Hard rules, from the project standards:

- Verification-only. Quote it in `verification/bib.md` and nowhere else.
- The mirror URL goes in `verification/bib.md`, never in the `.bib` entry.
- Keep the file outside the repository. Never commit it.
- APS `journals.aps.org` blocks automated fetching. Do not fight it.

### Order within the rung

1. **LibGen** — the only one with a real JSON API, and it needs no key:
   `json.php?object=e&fields=*&doi=<DOI>` gives the edition and its file md5s,
   then `object=f&fields=*&ids=<f_id>` gives `extension` and `filesize` before you
   commit to a download. Use `libgen.li`.
2. **Sci-Hub** — `sci-hub.ee` first, it carries the search form; then `.ru`, `.su`,
   `.box`; then `.al`, `.mk`. Manual fallback: `https://sci.bban.top/pdf/<DOI>.pdf`
   with a browser User-Agent.
3. **Anna's Archive** — `/dyn/` endpoints only, since the HTML sits behind
   DDoS-Guard. The download half needs **paid membership**, so this is a dead end
   unless the user already has a key.
4. **welib.org**, then Z-Library — browser only, human in the loop.

### Check the mirrors before concluding a paper is unavailable

Mirrors churn, and an HTTP 200 proves nothing — `sci-hub.tf` answers 200 and
redirects to an ad landing page. Run the content-verifying checker:

```bash
scripts/allpapers-mirrors              # every service
scripts/allpapers-mirrors libgen       # one service
scripts/allpapers-mirrors --slum       # plus what open-slum.org reports
```

<https://open-slum.org/> is the live status source, checking every 5 minutes. Its
`PROTECTED` status means "behind an anti-bot challenge", i.e. browser-only. It has
no API, it reports `UP` for hosts that serve nothing usable, and it disagrees with
direct measurement in both directions — so use it to narrow candidates, then
verify. Do not use `sci-hub.pub` or `scihub.help`: both are stale and both list
domains that are dead.

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
labeled as abstract-level verification, not full text. `verification.md` has the
rule; `other-indices.md` has the field.
