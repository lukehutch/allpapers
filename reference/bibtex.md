# Building the BibTeX entry

`scripts/allpapers-bibtex <identifier>` prints one normalized entry, assembled
from every index that has the work. Everything below was measured against the
live services on 2026-08-25; each claim names the paper it was measured on so it
can be re-checked.

```bash
scripts/allpapers-bibtex 10.1038/nature14539
scripts/allpapers-bibtex arXiv:1706.03762 --prefer INSPIRE-HEP
scripts/allpapers-bibtex hep-th/9711200 --raw      # each index unmerged
scripts/allpapers-bibtex 10.1038/nature14539 --json
scripts/allpapers-bibtex 10.1038/nature14539 --bibmd   # a verification/bib.md stub
```

`scripts/allpapers-fetch` calls this internally, so a full record already carries
the merged entry. Use `allpapers-bibtex` on its own when you want the entry
without the download.

## Why merge instead of picking one index

Because no index is right about everything, and the ways each is wrong are
consistent enough to route around. Taking Crossref whole gives you a lower-cased
DOI and a flattened title; taking INSPIRE whole loses the issue number and the
publisher; taking arXiv whole dates a 1998 paper to 1997. Merging field by field
gives an entry that is right in every field, and printing the disagreements means
the choices are auditable rather than silent.

Every disagreement is reported on stderr:

```
% disagreement — year: took Crossref='1999' over INSPIRE-HEP='1999'; arXiv='1998'
% disagreement — title: took INSPIRE-HEP='A Time varying speed of light as a solution to c' over Crossref='Time varying speed of light as a solution to cos'
```

Read them. They are the cheapest way to catch an entry that is subtly the wrong
paper — and sometimes the only way: see the OpenAlex wrong-DOI case in
`other-indices.md`, where every index answers 200 with well-formed data and the
merged entry still dates a 2017 paper to 2025.

## Where each index answers

| Index | URL | Covers |
|---|---|---|
| INSPIRE-HEP | `https://inspirehep.net/api/arxiv/{id}`, `…/api/doi/{doi}`, `Accept: application/x-bibtex` | high-energy physics, including pre-arXiv |
| Crossref | `https://doi.org/{doi}` with `Accept: application/x-bibtex` | anything with a Crossref DOI |
| DataCite | the same URL — `doi.org` routes by registrant | 10.48550 (arXiv), Zenodo, Dryad |
| arXiv | `https://export.arxiv.org/api/query?id_list={id}` | preprints, plus the published DOI and `journal_ref` when the author set them |
| PubMed | `eutils…/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml` | biomedical records, including the many with no DOI |
| dblp | `https://dblp.org/search/publ/api?q={title}+{surname}`, then `https://dblp.org/rec/{key}.bib?param=1` | computer science: conference proceedings, their editors and series |
| Scholar | `https://scholar.google.com/scholar?as_epq={title}&as_occt=title` | venue strings for grey literature; last resort |

`doi.org` content negotiation returns the registration agency's own BibTeX, so
one request covers Crossref and DataCite both. Which agency answered is
determined afterward by asking `api.crossref.org` whether it knows the DOI —
that distinction matters, because the two agencies need different handling.

**efetch, not esummary, for PubMed.** Only efetch carries full author forenames;
esummary gives MEDLINE-style `WATSON JD`, which is not what a `.bib` entry wants.

## The per-field trust order

Each row was settled by fetching the same paper from every index and comparing,
not by reputation. `--prefer INDEX` promotes one index above the order for a
single run; `--single` skips merging entirely.

| Field | Order | Why |
|---|---|---|
| `pages` | INSPIRE, Crossref, PubMed, DataCite, arXiv | INSPIRE writes `436--444` already; Crossref emits a literal U+2013; PubMed abbreviates the closing page |
| `doi` | Crossref, INSPIRE, PubMed, DataCite, arXiv | Crossref *is* the registration record |
| `number`, `volume` | Crossref, PubMed, INSPIRE | INSPIRE routinely omits the issue number |
| `publisher`, `issn` | Crossref only | nobody else has them, and DataCite's publisher for an arXiv DOI is the string `arXiv` |
| `month` | Crossref, INSPIRE | |
| `eprint`, `archiveprefix`, `primaryclass` | arXiv, INSPIRE | arXiv is the registry of its own identifiers |
| `title` | INSPIRE, Crossref, PubMed, arXiv, DataCite | INSPIRE preserves LaTeX maths (`The Large $N$ limit`); the others flatten it to `The Large N Limit` |
| `journal` | Crossref, INSPIRE, PubMed | Crossref gives the full title, INSPIRE the physics abbreviation. Full is less ambiguous, and a `.bst` that wants the short form can abbreviate; going the other way needs a lookup. `--prefer INSPIRE-HEP` for the physics house style |
| `booktitle` | dblp, INSPIRE, Crossref | dblp carries the full proceedings title for a CS conference; Crossref often has no record of the volume at all |
| `editor`, `series` | dblp, Crossref | measured on `1706.03762`: dblp supplies all seven NIPS 30 editors, Crossref none |
| `author` | Crossref, INSPIRE, PubMed, arXiv, DataCite | the publisher deposits Crossref's list from the article itself |
| `year` | Crossref, INSPIRE, PubMed, arXiv, DataCite | arXiv and DataCite report the *submission* year. Measured on hep-th/9711200: 1997 against a 1998 journal date |
| `pmid` | PubMed | |
| `reportnumber` | INSPIRE | |
| `url` | Crossref, arXiv, DataCite | |

Two rules are structural rather than per-field:

- **A field listed with a single index is exclusive to it.** Naming only Crossref
  for `publisher` means no other index may supply it — without that, DataCite's
  `publisher = {arXiv}` leaks into the entry for a paper published in a journal.
- **Scholar is appended to every order, never listed inside one.** It fills holes
  no registration index can fill, and never outranks one. It is excluded outright
  from the identifier fields (`doi`, `pmid`, `eprint`, `issn`, `url`, …).

The **cite key** comes from the most-trusted index that has one — INSPIRE first,
because its `Author:YYYYxx` keys are the shared currency of the physics
literature and someone else may already be citing the paper by that key.

Fields dropped on sight: `copyright`, `abstract`, `language`, `keywords`,
`urldate`, `collection`, `note`, `bibsource`, `biburl`, `timestamp`. DataCite
returns arXiv's entire distribution license as `copyright`, and repeats subject
terms in `keywords` (`FOS: Physical sciences, FOS: Physical sciences`); the last
three are dblp's own bookkeeping, which says when dblp last touched the record and
nothing about the paper.

**dblp is queried by title *and* first-author surname, or not at all.** A title
alone can be out-ranked off dblp's own result list — see `dblp.md`. When no index
has yet supplied an author, `gather()` borrows the first surname from whichever
entry it already holds; when none does, dblp is skipped rather than guessed at.

## Normalizations applied

Each of these is printed as a `% normalised — …` line, so nothing is changed
silently.

| Fix | Measured on |
|---|---|
| U+2013 EN DASH in a page range → `--` | `10.1038/nature14539` returns `436–444` |
| single hyphen in a page range → `--` | general |
| MEDLINE abbreviated closing page → expanded (`436-44` → `436--444`) | PubMed records generally |
| numeric month → three-letter (`{6}` → `{jun}`) | DataCite on `1706.03762` |
| `10.48550/ARXIV.…` → `10.48550/arXiv.…` | DataCite on `1706.03762`; the registered form is mixed case |
| lower-cased DOI → the registered casing taken from the entry's own `url` | `10.1103/PhysRevD.59.043516` |
| `http://dx.doi.org/` → `https://doi.org/` | Crossref generally |
| trailing empty author dropped | `10.1103/PhysRevLett.116.061102` |
| U+2009 THIN SPACE and friends → a plain space | `10.1103/PhysRevLett.116.061102`, 325 of them |
| maths and mixed-case words in the title brace-protected | `hep-th/9711200` |
| URL-shaped cite key → `Author:YYYYxx` | DataCite keys entries on the whole DOI URL |
| reflowed to one field per line, values aligned | all |

**The lower-cased DOI is the subtlest of these.** Crossref's BibTeX export
returns `DOI={10.1103/physrevd.59.043516}` beside
`url={http://dx.doi.org/10.1103/PhysRevD.59.043516}` — the same DOI, two casings,
in one record. DOIs resolve case-insensitively so nothing breaks, but the entry
then disagrees with every other citation of the paper, and with the `**DOI**`
line of its own verification record. The fix takes the casing from the `url`
field when the two match case-insensitively.

**The thin space is the one that stops a build.** APS deposits author initials
separated by U+2009 THIN SPACE and Crossref passes it through, so the LIGO
detection paper arrives with 325 of them (`Abbott, B. P.`). Under pdflatex
with `utf8` inputenc that is not cosmetic — it is a hard error, measured:

```
! LaTeX Error: Unicode character  (U+2009) not set up for use with LaTeX.
```

Accented letters and curly quotes compile fine under the same setup (measured on
`é ’ ż ß ń ü à`), so only the exotic space characters are folded; the names keep
their diacritics. Zero-width characters are deleted outright.

**Title case protection matters more than it looks.** Most standard styles —
`plain`, `unsrt`, `abbrv`, `alpha` — run `change.case$` over the title and
lowercase everything not inside braces, and BibTeX has no idea what maths is.
INSPIRE deposits Maldacena's title as
`title = "{The Large $N$ limit of superconformal field theories and supergravity}"`,
where the outer brace group *is* the protection. Reading the value strips it, and
the entry then renders as **"The large n limit"** — the wrong title, since the
$N$ is the gauge group rank. Measured through a real `latexmk`/`plain.bst` build.

Only the parts whose case carries meaning are protected: maths spans, and words
with a capital after the first letter (`AdS/CFT`, `QCD`, `DNA`, `CRISPR-Cas9`).
Ordinary capitalized words are left alone — a style that sentence-cases them is
doing what the person who chose it asked for. A title that already contains
braces is never touched.

**The trailing empty author is the most damaging.** Crossref's author array for
the LIGO detection paper ends with an empty element, which reflows into
`… and Zweizig, J. and}`. BibTeX renders that as a blank final author. It is
easy to miss because the list is 1,011 names long. Note that the dangling
separator has no trailing space, so splitting on `" and "` yields no empty slot —
the check has to look for the trailing `and` explicitly.

## Protect capitals a `.bst` would destroy

Most `.bst` styles lowercase every word of a title but the first. In English that
is usually harmless. In **German it is wrong**, because German capitalizes all
nouns, and the same goes for any proper noun, acronym or chemical symbol sitting
mid-title in any language. BibTeX preserves whatever is inside braces, so the
capitals have to be braced in the `.bib` file.

Measured with `plain`, `plainnat`, `unsrt`, `alpha`, `ieeetr` and `apalike` — all
six fold the case, and both protections survive all six:

| In the `.bib` file | Rendered by `plain` |
|---|---|
| `title = {Zur Elektrodynamik bewegter K{\"o}rper}` | Zur elektrodynamik bewegter körper ✗ |
| `title = {{Zur Elektrodynamik bewegter K{\"o}rper}}` | Zur Elektrodynamik bewegter Körper ✓ |
| `title = {Zur {E}lektrodynamik bewegter {K}{\"o}rper}` | Zur Elektrodynamik bewegter Körper ✓ |

Either form works, and they differ in what they give up:

- **Brace the whole title** — one extra `{}` around the existing value. Quick, and
  the right choice when nearly every word needs protecting. It also freezes
  everything else about the title, so a style that would legitimately recase the
  rest can no longer touch it.
- **Brace each capital individually** — `{E}`, `{K}`. More work, but it protects
  exactly what needs protecting and leaves the rest of the line to the style. Note
  that an accented letter is already its own group: write `{K}{\"o}rper`, bracing
  only the `K`.

**The scripts protect some of this, and deliberately not this part.**
`protect_title()` braces maths spans and words carrying a capital after their
first letter — `{AdS}`, `{QCD}`, `{Ba-La-Cu-O}`, `{$N$}` — and prints a
`% normalised — title: brace-protected …` line when it does. It leaves an
ordinary initial capital alone, because a style that sentence-cases English is
doing what whoever chose it asked for. It also bails out entirely on a title that
already contains a brace, on the assumption that one has been hand-tuned.

That rule is right for English and wrong for German, and nothing in the pipeline
can tell the two apart: no index merged here marks a title's language.
`10.1002/andp.19053221004` therefore comes back exactly as the unprotected first
row above. **Non-English capitals are yours to brace by hand** — see the
proofreading pass in `SKILL.md`. The entry is wrong at the moment it is written,
not at the moment it renders, and nothing downstream will catch it.

## Two traps that merging cannot fix

**The reprint trap.** arXiv's Atom record carries a `doi` and a `journal_ref`
supplied by the author. When that DOI differs from the entry's, both are usually
live and both are in Crossref, but they name different journals — the paper was
reprinted. Measured on hep-th/9711200 (Maldacena), where the arXiv DOI names one
journal and the entry's another. `allpapers-bibtex` prints a warning naming both
and stops there, because which publication you are citing is a decision only the
citing author can make. The same applies when `journal_ref` names a volume the
merged entry does not.

**Identity.** Every index here is keyed by an identifier you supplied. If the
identifier is for a different paper than you think, every index will agree with
you, confidently. That is what the verbatim quote in `verification/bib.md`
exists to catch — see `reference/verification.md`, requirement 4.

## Credentials never reach the record

`scrub_url()` strips `email`, `mailto`, `api_key`, `key`, `tool`,
`access_token` and their variants from every URL before it is printed or written
to a file. The polite-pool parameters carry the user's own address, and
`verification/bib.md` is committed. A scrubbed URL is still re-fetchable; the
PubMed one records as

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=26017442&retmode=xml
```

## Reading the output

Entry on stdout, everything else on stderr, so `allpapers-bibtex … >> refs.bib`
does the right thing:

```
% indexes merged: Crossref, INSPIRE-HEP, arXiv
%   Crossref       <- https://doi.org/10.1103/PhysRevD.59.043516
%   INSPIRE-HEP    <- https://inspirehep.net/api/arxiv/astro-ph/9811018
%   Scholar (no usable record) <- https://scholar.google.com/scholar?...
%   arXiv          <- https://export.arxiv.org/api/query?id_list=astro-ph%2F9811018
%   author         <- Crossref
%   pages          <- INSPIRE-HEP
%   title          <- INSPIRE-HEP
% disagreement — year: took Crossref='1999' over arXiv='1998'
% normalised — doi: case restored from the url field
warning: Scholar contributed nothing: Scholar returned no parseable results
```

The first block is where each index answered; the second is which index won each
field; then disagreements, normalizations and warnings. `--json` returns the same
information as `indexes_consulted`, `index_urls`, `field_provenance`,
`merge_notes`, `normalisations` and `warnings`.
