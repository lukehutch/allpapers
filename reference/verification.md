# Verification records

Finding a paper is half the job. The other half is leaving behind a record that
lets someone else — or you, six months later — confirm that what the citing text
says about a paper is what the paper actually says. Two files do that, both living
in a `verification/` directory beside the `.tex` file they belong to:

- `verification/bib.md` — the citation record. One entry per `.bib` key.
- `verification/equations.py` — the numerical record. Every equation recomputed.

These requirements come from `~/Work/papers/new/STANDARDS.md`. They are reproduced
here so the skill is usable in a project that does not have that file.

---

## `verification/bib.md`

For **every** citation in the `.bib` file that the `.tex` file actually cites:

### 1. Source verification

The paper must be **downloaded and read**. Acceptable sources, in priority order:

1. LaTeX source from arXiv
2. HTML source
3. PDF of the published version
4. PDF of the preprint

Record **every** URL that contributed, not just the one you read the body from:
the metadata indexes, each artefact fetched, and the channels located but not
taken. A record naming one location hides where the rest of the entry came from,
and the disagreement between two of them is often the thing worth catching. This
priority order is the same one `scripts/allpapers-locate` ranks by, and it exists
for a concrete reason: LaTeX
carries equations as equations and section structure as markup, so a quote pulled
from it is exact and its locator is unambiguous. A PDF gives you whatever the text
extractor guessed.

`scripts/allpapers-fetch` does all of this in one call: it fetches every form
that exists, writes them under `verification/source/<citationKey>/`, and records
the URLs. For an arXiv paper on its own, `scripts/arxiv-source <id>` does the
`mktemp -d` / fetch `/src/` / unpack dance and prints where it put the files. See
`reference/arxiv.md`.

### 2. Full bibliographic metadata

Record all authors (full names), exact title, journal, volume, pages, year, DOI
and arXiv eprint ID. Then proofread what you wrote against the paper's own title
page — diacritics intact, no mojibake, capitals that carry meaning brace-protected
(`{{Zur Elektrodynamik bewegter K{\"o}rper}}`, or a `.bst` will lowercase the
German nouns). The full checklist is in `SKILL.md`; the case-folding mechanics are
in `reference/bibtex.md`.

**Every entry must be cross-checked against an authoritative index** — Crossref,
INSPIRE-HEP, NASA ADS, Google Scholar or the publisher's own page. Search by title
and/or DOI; if one index blocks automated access, use another. The index entry is
the authoritative cross-reference. Any disagreement between the `.bib` entry and
what you verified — from **both** the paper itself and the index — gets flagged
and corrected.

Never write a `.bib` entry from memory. `scripts/allpapers-bibtex <identifier>`
queries INSPIRE-HEP, Crossref, DataCite, arXiv, PubMed and Google Scholar at once,
merges them field by field, and prints every disagreement it had to resolve. The
merged entry goes in the BibTeX block of the record below, which is the canonical
copy — the `.bib` file is generated from it. See `reference/bibtex.md` for the
per-field trust order and the traps it works around.
For pre-DOI physics, NASA ADS is the authority on old Annalen-style volume
numbering.

### 3. Supporting quotes

For every claim the `.tex` file makes about a reference, include a **verbatim**
quote from that paper that supports it, with a page, section, equation number or
line locator. Copy-paste it; do not retype it. If a claim cannot be supported by a
verbatim quote, flag it as unsupported.

### 4. Attribution verification

If the `.tex` file attributes a specific result, formula or finding to the cited
authors, the quote must show that **those authors** actually derived or stated it.
Attributing a result from paper A to the authors of paper B is a critical error,
and it is the error this step exists to catch.

### 5. No hallucinated citations

Every citation must correspond to a real, published paper with the stated authors,
title and venue. The record must demonstrate the paper exists — which it does
automatically, if you actually fetched and quoted it.

---

## The sourcing flow

Discovery and acquisition are separate problems. This flow is empirically proven
(SGM quote back-fill, 2026-06: about 90 keys sourced with zero no-free-source
failures). `reference/ladder.md` is the same ladder as an operational sequence;
this is the channel-numbered version the verification record refers to.

**A. Discovery — finding related work and prior art**

1. **Paperclip semantic search** — `paperclip search -s abstracts "query" -n 250`.
   Re-run with several phrasings; different wordings surface different
   neighbourhoods. Treat hits as leads, not endorsements: read before citing.
2. **Google Scholar** by plain web fetch — good at surfacing legitimate free PDF
   mirrors via its `[PDF]` sidebar links. Use sparingly, roughly once per key, to
   avoid CAPTCHA. It is a discovery tool, not an identity resolver: see
   `reference/scholar.md`.
3. **Crossref keyword search** (`api.crossref.org/works?query.bibliographic=…`)
   and **OpenAlex** (`api.openalex.org/works?search=…`) as API-friendly fallbacks.

**B. Metadata authority — before writing any `.bib` entry**

4. **Crossref by DOI** — `curl https://api.crossref.org/works/<doi>`. NASA ADS and
   INSPIRE-HEP for physics records Crossref lacks.

**C. Full-text acquisition — work down until one succeeds**

5. **arXiv**, whenever an eprint exists: paperclip mirror first (line-numbered and
   greppable), else the LaTeX source, else the PDF.
6. **Publisher free text** — gold-OA pages, free publisher PDFs, official excerpts
   (`assets.cambridge.org` book excerpts give verbatim front matter and section
   text for closed books).
7. **Unpaywall** — `api.unpaywall.org/v2/<doi>?email=…`.
8. **Semantic Scholar** —
   `api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=abstract,openAccessPdf,externalIds`.
   Some AIP/IOP abstracts are publisher-elided.
9. **PubMed eutils** for Nature/Science/PNAS abstracts —
   `eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<pmid>&rettype=abstract`.
10. **Legitimate institutional copies** — government labs, university course and
    lab pages, author homepages, rights-holding foundations. Record the URL
    actually used; flag personal or translator sites as provenance-unverified and
    spot-check their text against a second channel.
11. **Public-domain archives** for pre-1930 classics — `archive.org` (fetch the
    `_djvu.txt` OCR layer of full-view scans), Wikisource, Gallica, official
    journal back archives. Mark OCR restorations in brackets.
12. **Shadow-library mirrors** — permitted once 5–11 have failed, and preferred
    over settling for snippet- or abstract-level verification. See
    `reference/scihub.md` for the conditions.
13. **Google Books / Scholar snippets** — page-anchored snippets for closed books
    when nothing better exists. Locator-level verification only.
14. **OpenAlex abstract reconstruction**, when no full text can be had anywhere:
    `curl https://api.openalex.org/works/doi:<doi>` and rebuild the abstract from
    `abstract_inverted_index` by sorting word positions. This rescues old paywalled
    AJP/IOP/Springer papers whose abstracts are deposited but displayed nowhere
    free.

**D. Hard rules**

- Shadow-library use is **verification-only**: never redistribute, never commit
  the fetched file, and never use a mirror as the reference's locator. The `.bib`
  entry carries the DOI, journal or arXiv ID; the mirror URL appears only in
  `verification/bib.md` as the access record. Cross-check the fetched copy against
  Crossref (title page, volume, pages) — mirrors occasionally pair the wrong PDF
  with a DOI.
- Some publishers, notably APS (`journals.aps.org`), block automated fetching.
  **Do not fight the block** — use the arXiv version, or channels 7–9, 12, 14.
- A quote goes into the record only if copied verbatim from text **actually fetched
  in this session**; at most about 40 words per quote; every quote carries a
  locator. When quoting a translation, name the translator and the source.
- If every channel through 14 fails, record `NO-SOURCE` with the list of channels
  tried, and verify the claim against the publisher-deposited abstract (8, 9 or 14)
  if one exists. **Do not silently downgrade verification.**
- For each citing context in each `.tex` file, record a per-context verdict:
  `SUPPORTED` / `PARTIAL` / `NOT SUPPORTED`, noting when a claim is jointly carried
  by co-cited keys.

---

## The two-step workflow

A search returns candidates; only some of them earn a place in the permanent
record. `scripts/allpapers-fetch` therefore separates retrieval from commitment,
and nothing is written into `verification/` until you have judged the paper.

```bash
# 1. fetch everything retrievable into a temp directory
scripts/allpapers-fetch "10.1038/nature14539" --stage

# 2a. relevant: copy it in and say why, with the quotes that carry the claim
scripts/allpapers-fetch 10.1038/nature14539 --promote /tmp/allpapers-LeCun_2015pmr-ab12cd \
    --justification "..." --claim "..." --quote "verbatim text@p.436" --status VERIFIED

# 2b. it looked relevant and is not: record that, keep no files
scripts/allpapers-fetch 10.1038/nature14539 --reject --justification "..."

# 2c. it was cited and no longer is
scripts/allpapers-fetch 10.1038/nature14539 --retire --justification "..."
```

`--stage` prints the staging directory and the two follow-up commands with the
paths already filled in. For a single known paper you are certain about, omit
`--stage` and it fetches straight into `verification/source/<citationKey>/`.

`--justification` is required for `--promote`, `--reject` and `--retire`. It is
the field a future session reads to avoid redoing the judgment, so a bare "not
relevant" wastes the record.

**Record a rejection only for a paper that genuinely looked relevant.** A search
hit the title and abstract rule out is not written down at all. The file is a
note about a real judgment call, not a search log.

### What lands in `verification/source/<citationKey>/`

Every retrievable form, best-first, plus the evidence that they are what they
claim to be:

| File | What it is |
|---|---|
| `latex/` | the unpacked arXiv submission — the best format there is |
| `<key>-arxiv-src.tar.gz` | the exact bytes arXiv served, before unpacking |
| `content.lines` | paperclip's extracted text, line-numbered, so quotes cite as `#L45` |
| `<key>.pdf` | the PDF, fetched even when better formats exist |
| `<key>.bib` | the merged entry, same as the one in `bib.md` |
| `PROVENANCE.json` | every URL tried, what answered, sizes, sha256 digests |

Add `--no-pdf` to skip the PDF, `--no-abstract` to skip the abstract lookup.

---

## File format

The record below is real output, not a sketch. `allpapers-fetch` writes it; hand
edits are expected on top of it, particularly the claims and quotes.

````markdown
# Citation Verification Record

## Vaswani:2017lxt

```bibtex
@inproceedings{Vaswani:2017lxt,
  author        = {Vaswani, Ashish and Shazeer, Noam and ...},
  title         = {Attention Is All You Need},
  booktitle     = {31st International Conference on Neural Information Processing Systems},
  year          = {2017},
  doi           = {10.48550/arXiv.1706.03762},
  eprint        = {1706.03762},
  archiveprefix = {arXiv},
  url           = {https://arxiv.org/abs/1706.03762}
}
```

- **Verified authors**: Vaswani, Ashish and Shazeer, Noam and ...
- **Verified title**: Attention Is All You Need
- **Journal**: 31st International Conference on Neural Information Processing Systems (2017)
- **DOI**: 10.48550/arXiv.1706.03762
- **arXiv**: 1706.03762
- **Metadata cross-checked against**: DataCite, INSPIRE-HEP, arXiv
- **Source URLs**:
  - `https://doi.org/10.48550/arXiv.1706.03762` — metadata (DataCite)
  - `https://inspirehep.net/api/arxiv/1706.03762` — metadata (INSPIRE-HEP)
  - `https://scholar.google.com/scholar?hl=en&as_epq=Attention+Is+All+You+Need&as_occt=title` — metadata (Scholar (no usable record))
  - `https://export.arxiv.org/api/query?id_list=1706.03762` — metadata (arXiv)
  - `https://arxiv.org/src/1706.03762` — latex → `latex/`
  - `/papers/arx_1706.03762/content.lines` — content.lines → `content.lines`
  - `https://arxiv.org/pdf/1706.03762` — pdf → `Vaswani:2017lxt.pdf`
  - `https://arxiv.org/html/1706.03762` — html at arXiv, located but not fetched
- **Abstract** (paperclip meta.json):

  The dominant sequence transduction models are based on complex recurrent or
  convolutional neural networks in an encoder-decoder configuration. ...

- **Justification**: Introduces the transformer architecture the method section
  builds on; needed for the claim that attention alone suffices.
- **Claims supported**:
  - Claim: The architecture dispenses with recurrence and convolution entirely.
    Quote: "We propose a new simple network architecture, the Transformer, based
    solely on attention mechanisms, dispensing with recurrence and convolutions
    entirely." (#L11)
- **Status**: VERIFIED
- **Local copies**: `source/Vaswani:2017lxt/`
  - `latex/` — latex, 2,425,070 bytes
  - `content.lines` — content.lines, 40,012 bytes, sha256 43a41ddca219
  - `Vaswani:2017lxt.pdf` — pdf, 2,215,244 bytes, sha256 bdfaa68d8984
- **Indexes with no record**: Crossref, Scholar
- **Notes**: —
````

Field by field:

| Field | Why it is there |
|---|---|
| the BibTeX block | `bib.md` is the canonical home of the entry. The `.bib` file is generated from it, not the other way round |
| **Metadata cross-checked against** | requirement 2 — which authoritative indexes agreed |
| **Source URLs** | *every* location that contributed: each metadata index, each artefact fetched and where it was written, and each channel located but not fetched. One URL would hide where the rest came from |
| **Abstract** | recorded whenever any index has one, with the index named. It is what a later session reads to re-judge relevance without re-fetching |
| **Justification** | why this paper is or is not relevant to the question asked |
| **Claims supported** | requirement 3 — one verbatim quote per claim, with a locator |
| **Local copies** | the files, with byte counts and sha256 prefixes, so a later session can tell whether the copy on disk is the one that was quoted |
| **Not retrievable** | channels that were tried and failed, with the reason |
| **Indexes with no record** | silence is a finding: an index that has never heard of the paper is worth knowing about |

The abstract ladder, cheapest good source first: paperclip `meta.json` →
PubMed `efetch` → arXiv Atom `<summary>` → Crossref (JATS markup stripped) →
OpenAlex `abstract_inverted_index` rebuilt by sorting word positions.

### The two other record types

Both live in the same file under their own `##` heading, with the records
themselves at `###` so the nesting stays unambiguous:

```markdown
## Examined and rejected

### LeCun:2015pmr

**Examined and rejected — evaluated as a citation candidate and declined. Do not
re-fetch this paper to answer the same question.**

... same fields ...
- **Reason for rejection**: Surveys deep learning broadly; the claim here is
  about attention specifically, which this review predates.
- **Quotes checked**: none — the decision rests on the metadata and abstract
  above, so no full text was read
- **Status**: REJECTED — examined and not cited
- **Local copies**: none kept — the paper was not cited

## Retired entries

### Some:2019key

**Retired — no longer cited. The entry below is complete, so it can be restored
verbatim if it is needed again.**
```

- **Examined and rejected** — papers fetched and evaluated as citation candidates
  but declined. Record the verified metadata, the abstract, the verbatim quotes
  actually fetched, and why it was rejected.
- **Retired entries** — keys removed from the `.bib` file after becoming
  orphaned. Record the full BibTeX entry, so it can be restored verbatim, and why
  it is no longer used.

A record is placed by its section and replaced by its key: re-running with a
different disposition moves the record rather than duplicating it, and the quotes
already recorded for every *other* paper are left untouched, because that is the
part that took real work.

## When to update it

- A `.tex` file is created → create `verification/bib.md` and verify every citation.
- A citation is added → verify it and add its record.
- A claim referencing a citation is modified → re-verify against the source and
  update the quotes.
- A candidate paper is examined but rejected → record it under "Examined and
  rejected".
- A `.bib` key becomes orphaned → either cite it where it genuinely adds value, or
  move it to "Retired entries" with the reason.

**All new citations must be fully source-verified before they go into the `.tex`
file.** Not after.

---

## `verification/equations.py`

Every `.tex` file also needs a Python script beside it that:

1. **Computes all key equations numerically.** Every equation producing a numerical
   value or prediction is independently computed to full precision.
2. **Verifies dimensional consistency** by tracking units through the computations.
3. **Cross-checks intermediate results**, not just final ones, and does so **by an
   independent route** wherever possible: a SymPy symbolic check against the
   numerical evaluation, an alternative derivation, or a known limiting case. A
   script that only transcribes the paper's algebra into Python checks the
   transcription, not the mathematics — this is the requirement most often missed.
4. **Reports discrepancies** as a clear PASS/FAIL per check, printing expected
   versus computed values and the relative error.
5. **Stays current** — updated whenever an equation in the `.tex` file changes.

The connection back to this skill: when a paper you have fetched states a numerical
result you are relying on, the quote goes in `bib.md` and the recomputation goes in
`equations.py`. A source quote proves the author said it; the recomputation proves
it is true.
