# allpapers

An agent skill for finding and retrieving the full text of scientific papers.
It installs into Claude Code, the Codex CLI and Antigravity (`agy`) — see
[Install](#install).

It merges the older `paperclip` and `scihub-cli` skills, adds CORE and Unpaywall,
adds arXiv LaTeX source retrieval, and arranges every source into one priority
ladder. The organising rule is that **a parseable text format is worth more than a
convenient one**: LaTeX and JATS XML carry equations, section structure and
reference lists that PDF text extraction destroys.

## The three rules

Everything below follows from these. They are ordered: when two pull against each
other, the earlier one wins.

1. **Prefer parseable source.** PDF text extraction silently mangles equations,
   loses section boundaries, splits ligatures and reorders multi-column text.
   LaTeX and JATS do not. Reaching for a PDF when LaTeX exists means quoting from
   a worse copy for no reason.
2. **Follow the ladder.** Cheap, open, already-extracted sources first; bootleg
   copies only when nothing else has it. Do not skip rungs to reach the bottom
   faster — the lower rungs are slower, less reliable, and in one case not open at
   all.
3. **Nothing is cited until it is recorded.** Any paper supporting a claim goes
   into `verification/bib.md` with its composite BibTeX entry, every source URL
   used, its abstract, a justification, and verbatim quotes with locators. Papers
   examined and *rejected* get an entry too: knowing a dead end was already
   explored is worth as much as an inclusion.

Rule 1 is enforced in code. `allpapers-locate` sorts every location it finds by
`FORMAT_RANK`, best first:

```
extracted text  ›  LaTeX  ›  XML  ›  HTML  ›  PDF  ›  unknown
```

Within the XML tier, prefer authored JATS over a GROBID machine parse of a PDF —
the two share a rank in the code but not in quality. A scanned PDF with no text
layer is the worst case of all and needs reading by eye.

## Install

The skill is a single directory with a `SKILL.md` at the top. Claude Code, the
Codex CLI and Antigravity all load skills the same way and all three follow a
symlink, so one checkout can serve every agent you use and a single `git pull`
updates all of them.

```bash
git clone https://github.com/lukehutch/allpapers.git ~/Work/allpapers
```

| Agent | Skills directory | Link it in |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | `ln -s ~/Work/allpapers ~/.claude/skills/allpapers` |
| **Codex CLI** | `$CODEX_HOME/skills/`, i.e. `~/.codex/skills/` | `ln -s ~/Work/allpapers ~/.codex/skills/allpapers` |
| **Antigravity** (`agy`) | `~/.gemini/skills/` | `ln -s ~/Work/allpapers ~/.gemini/skills/allpapers` |

All three at once:

```bash
for d in ~/.claude/skills ~/.codex/skills ~/.gemini/skills; do
  mkdir -p "$d" && ln -sfn ~/Work/allpapers "$d/allpapers"
done
~/Work/allpapers/scripts/allpapers-setup          # asks once for what it needs
```

Prefer a copy to a symlink? `cp -r ~/Work/allpapers ~/.codex/skills/allpapers`
works just as well; you then update each copy yourself.

Each agent picks the skill up on its next run — none of them need a restart
beyond starting a fresh session.

### How those three paths were established

Not by convention — measured on this machine on 2026-08-26, because a wrong
directory fails silently:

- **Codex.** Its own preinstalled `skill-installer` skill states: *"Installs into
  `$CODEX_HOME/skills/<skill-name>` (defaults to `~/.codex/skills`)"*, and
  `$CODEX_HOME/skills/` appears as a path template in the binary. Confirmed end
  to end: after linking, `codex exec "list your available skills"` printed
  `allpapers` alongside the built-ins. Codex has no `skills` subcommand — the
  directory *is* the interface.
- **Antigravity.** `strace` on a real `agy -p` run shows it opening
  `~/.gemini/skills/allpapers/SKILL.md` — through the symlink. Its own built-ins
  live in `~/.gemini/antigravity-cli/builtin/skills/`, and it also probes
  `~/.gemini/antigravity-cli/skills` and `~/.gemini/config/skills{,.json,.txt}`.
  Note the directory is `~/.gemini/`, not `~/.antigravity/`: that second one
  holds only the VS Code-style editor config.
- **Claude Code.** `~/.claude/skills/` — the documented location.

### Replacing the older paperclip and scihub-cli skills

allpapers supersedes both. Keeping them installed alongside it is not harmful but
it does put three overlapping skill descriptions in front of the model, which
makes the choice between them arbitrary. Remove them:

```bash
rm -rf ~/.claude/skills/paperclip  ~/.claude/skills/scihub-cli \
       ~/.codex/skills/paperclip   ~/.codex/skills/scihub-cli \
       ~/.gemini/skills/paperclip  ~/.gemini/skills/scihub-cli \
       ~/.agents/skills/paperclip  ~/.agents/skills/scihub-cli
```

`~/.agents/skills/` is a shared cross-tool location some installers also write
to, which is why it is in the list.

Removing the *skill* does not remove the *tool*: `paperclip` and `scihub-cli`
stay on your PATH and allpapers keeps calling both. Only the competing
instructions go away.

One thing to know: **`paperclip update` regenerates its own skill file**, so it
will recreate `~/.claude/skills/paperclip/` and `~/.agents/skills/paperclip/`.
Re-run the removal after updating paperclip if you want it gone for good.

### Running `agy` from a script

`agy` asks gnome-keyring for its stored credentials, and on a desktop session the
unlock dialog takes the terminal — the command then blocks with no output and no
prompt. Presenting the session as a remote login with no display makes it use its
own token store instead:

```bash
export DISPLAY=""
export SSH_CLIENT="127.0.0.1 12345 22"
export SSH_TTY="/dev/pts/0"
agy
```

`allpapers-search` sets those three itself whenever it shells out to `agy`, so
this matters only when you run `agy` by hand.

## Configuration

### The four ways to set anything

```bash
scripts/allpapers-setup                        # interactive — prompts only for what is missing
scripts/allpapers-setup --check                # status of every credential
scripts/allpapers-setup --set email=me@example.org core_api_key=...
scripts/allpapers-setup --env                  # emit `export` lines for a shell
```

Or set the environment variable for any setting directly — `allpapers-setup`
reads the environment and folds those values into the config, so a key already
exported never gets asked for.

### Where it lives

`~/.config/allpapers/config.json`, mode 0600. Override the directory with
`ALLPAPERS_CONFIG_DIR`. The email address and the CORE key are additionally
mirrored into `~/.scihub-cli/config.json`, so `scihub-cli` picks up the same
values and nobody is asked twice.

Nothing is ever asked for twice, and every key is scrubbed out of URLs before
they are printed or written to `bib.md`.

### What `--check` tells you

Every credential reports `set` or `MISSING`, which services use it and whether
they require it, and where to register for one — for the ones you already have
as well as the ones you do not, so the output doubles as the sign-up list. It
closes with the services that need no key at all. Exit 0 means everything
essential is present; exit 1 means the email address — the one required value —
is missing.

```
paperclip                 : OK (logged in; paperclip, version 0.7.38)
email                     : set (required)
                            used by: Unpaywall: required. OpenAlex, Crossref: optional, but joins their polite pools. scihub-cli: reuses it for Unpaywall
                            register: no registration — any address you own. https://unpaywall.org/products/api documents the requirement
openalex_api_key          : MISSING (optional)
                            used by: OpenAlex: optional; required for its cached full text
                            unlocks: OpenAlex's cached full text (GROBID TEI XML for ~49M works, $0.01/file) ...
                            register: https://openalex.org/users  (free, instant)
...
No key or registration needed for:
  paperclip              browser sign-in on first use; free tier, then https://paperclip.gxl.ai/keys
  arXiv                  no key, no registration
  Crossref               no key; the email above joins the polite pool
  ...
```

Running `allpapers-setup` with no arguments prints the same catalogue and prompts
only for what is still missing.

Everything works without the optional keys, just less well.

| Setting | Used by | Cost | Where to register | What it buys |
|---|---|---|---|---|
| `email` | **Unpaywall: required.** OpenAlex, Crossref: optional, joins their polite pools. scihub-cli reuses it | — | No registration — any address you own. The requirement is documented at <https://unpaywall.org/products/api> | Unpaywall answers at all; politer treatment from OpenAlex and Crossref |
| `core_api_key` | **CORE: optional**, but anonymous CORE returns no full text | free, instant | <https://core.ac.uk/services/api#form> | CORE full text — **verified**: with a key, records return real text (38,460 and 68,513 characters in one test); anonymous returns the literal string `"Not available for public API users."`. Raises the quota from 100 to **1,000 tokens/day** — see the tier table below |
| `openalex_api_key` | **OpenAlex: optional**; required for its cached full text | free, instant | <https://openalex.org/users> | OpenAlex's cached GROBID TEI XML (~49M works, $0.01/file) and a $1/day metadata budget instead of the anonymous $0.10/day |
| `gemini_api_key` | **Gemini grounded search: required for the `api` backend.** Not needed for the `agy` backend | free tier | <https://aistudio.google.com/apikey> | Grounded web search — real Google Search queries returning answers with citations, reaching papers a plain web search misses |
| `ncbi_api_key` | **PubMed, PMC, NCBI eutils: optional**, raises the rate limit | free | <https://account.ncbi.nlm.nih.gov/> → Account settings → API Key Management | NCBI eutils at 10 requests/sec instead of 3. The anonymous limit is enforced and returns HTTP 429 mid-sequence, which reads as a lookup failure rather than a rate limit |
| `semantic_scholar_api_key` | **Semantic Scholar: optional**, raises the shared-pool rate limit | free, but manually reviewed — expect a wait | <https://www.semanticscholar.org/product/api#api-key> | Higher Semantic Scholar rate limits |
| `serpapi_key` | **Google Scholar: optional**; without it Scholar is scraped and will eventually serve a CAPTCHA | 100 free searches/month, then paid | <https://serpapi.com/users/sign_up>, key at <https://serpapi.com/manage-api-key> | Google Scholar via SerpApi instead of scraping. Only worth it if Scholar blocks and the paper matters |

Any setting can also be given as an environment variable: **the setting name in
upper case** — `CORE_API_KEY`, `GEMINI_API_KEY`, `SERPAPI_KEY` and so on. The one
exception is `email`, whose variable is `ALLPAPERS_EMAIL` rather than `EMAIL`, to
avoid colliding with the shell variable of that name. The environment overrides
the config file.

These services need no key and no registration at all: **arXiv**, **Crossref**
(the email above just joins the polite pool), **Europe PMC**, **DataCite** and
**OpenAIRE**, **LibGen** (`json.php` is open), **Sci-Hub**, and **Anna's Archive**
for the `/dyn/` JSON endpoints — a donor account at
<https://annas-archive.org/donate> unlocks fast downloads but nothing here needs
it. **paperclip** signs in through the browser on first use rather than taking a
key, and only needs one from <https://paperclip.gxl.ai/keys> if you exhaust the
free tier.

### CORE's tiers — a key is not the whole story

CORE meters in **tokens**, not requests. From its own documentation: "a simple
query will cost you 1 token while more complex queries will cost you between 3 to
5 tokens", and recommender, scroll-search and bulk queries cost more. So the daily
figures below are not request counts.

| User type | How to obtain | Rate limit |
|---|---|---|
| Unauthenticated | nothing | **100 tokens/day**, max 10/minute |
| Registered personal | the CORE API form | **1,000 tokens/day**, max 25/minute |
| Registered academic, *not* at a Supporting or Sustaining institution | the CORE API form | **5,000 tokens/day**, max 10/minute |
| Registered academic at a Supporting or Sustaining institution, and non-academic organisations | the CORE API form | negotiated — CORE estimates **~200k tokens/day** |

So a free personal key buys 1,000 tokens a day. The ~200k figure needs an academic
affiliation whose library actually supports CORE; it is not something you can
register your way into. Register at <https://core.ac.uk/services/api#form>.

Watch the response headers rather than counting calls yourself —
`x-ratelimit-limit`, `x-ratelimit-remaining` and `x-ratelimit-retry-after` (an ISO
timestamp) come back on every call. Measured with a registered personal key on
2026-08-26: `x-ratelimit-limit: 10`, which matches the per-minute bucket rather
than the documented 25/minute for that tier — so trust the headers over the table.

**paperclip** is a separate install, and the highest rung of the ladder depends on
it:

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
paperclip login
```

If its free usage is exhausted, an API key from <https://paperclip.gxl.ai/keys>
goes in `PAPERCLIP_API_KEY`. Exhaustion is a fall-through condition, not an error:
the ladder continues at the next rung.

## How it works

Seven tools plus a set of reference documents:

| Tool | What it does |
|---|---|
| `scripts/allpapers-setup` | First-run credential setup and status check. Asks once, stores in `~/.config/allpapers/config.json`. |
| `scripts/allpapers-locate` | Queries paperclip, arXiv, Unpaywall, OpenAlex, CORE and Europe PMC **concurrently** for one paper and prints every free full-text location, ranked most-parseable first. |
| `scripts/allpapers-search` | Keyword (BM25), semantic (vector), hybrid and analogical search over paperclip's 11.6M full texts, optionally alongside Gemini grounded web search — through the Gemini API or, with `--gemini-backend agy`, through the Antigravity CLI and no API key. |
| `scripts/arxiv-source` | Downloads an arXiv paper's submitted source into a `mktemp` directory and unpacks it, handling all three payload shapes arXiv serves. |
| `scripts/allpapers-bibtex` | Builds one composite BibTeX entry by merging INSPIRE-HEP, Crossref, DataCite, arXiv, PubMed and Scholar field by field, then normalising it. |
| `scripts/allpapers-fetch` | Fetches source *and* PDF into `./verification/source/<citationKey>/` in the current directory, and writes the `./verification/bib.md` record — staged first, promoted or rejected after you have read the paper. `--into` moves that directory, `--no-record` suppresses it entirely. |
| `scripts/allpapers-mirrors` | Checks which shadow-library mirrors are usable right now by verifying **content and final hostname**, not the status code, and can print what open-slum.org reports alongside. |

`reference/ladder.md` is the decision procedure the skill follows; the other
reference files hold the API details for each service, including the defects
measured in each one.

### The three kinds of lookup

Decide which one you are doing before you start. They use different tools and fail
in very different ways.

**Exact** — you know which paper you want:

```bash
scripts/allpapers-locate 10.1038/nature14539
scripts/allpapers-locate arXiv:1706.03762
scripts/allpapers-locate PMC3084216
scripts/allpapers-locate 26017442                      # PMID
scripts/allpapers-locate "Attention is all you need"   # resolves the title first
scripts/allpapers-locate 10.1038/nature14539 --json    # for scripting
```

Exit 1 means nothing free was found — the signal to move down the ladder.
Rate-limit and withheld-full-text messages print as `note:` lines and are *not*
counted as locations, so exit 1 really does mean nothing was found. Any row marked
`identity unconfirmed` needs its title checked before you quote it; see the
OpenAlex and CORE defects below for why that marker exists.

**Keyword** — you know the words that will appear:

```bash
scripts/allpapers-search --mode keyword "CRISPR base editing off-target" -n 250
scripts/allpapers-search --mode keyword --bool "(prime OR base) AND editing"
scripts/allpapers-search --mode keyword -e -t "Attention Is All You Need"
```

**Semantic** — you know the idea, not the words:

```bash
scripts/allpapers-search --mode semantic \
  "correcting for systematic under-reporting when the missingness mechanism is unknown"

scripts/allpapers-search --mode analogical "..."   # same method, unrelated field
scripts/allpapers-search --mode all "..."          # all four rankers, merged
```

Query wording matters more than any flag. The embedding model is fine-tuned on
abstracts, so the best input is a full abstract pasted verbatim; the next best is
one or two sentences describing the *method or problem structure* rather than the
topic. Bare keywords are the weakest possible input to a semantic ranker.
`--mode analogical` finds the same structural method in a different field, and is
the one search worth running even when you think you are done — the useful analogy
is usually in the community you would not have searched.

Two defaults quietly lose results: **always pass `-n 250`** (paperclip's real
default is 20, not the 100 its `--help` claims, and nothing warns you the rest
existed — `allpapers-search` defaults to 250 for this reason), and **think about
sort order** (`--sort date` is for recency sweeps, not for finding the single best
source; it discards relevance entirely and is refused alongside
`--min-similarity`).

Add `--gemini` to run Gemini grounded web search in parallel with paperclip, or
`--gemini-only` to skip paperclip. It returns *claims with citations*, so every
result is a lead to verify, never a source to quote. `--gemini-backend agy` runs
it through the Antigravity CLI instead of the API, using an ordinary Google login
rather than a billed key. If the output says *"no cited sources: this answer is
ungrounded"*, the model never searched and nothing in the answer may be relied on.

### Getting the full text

For anything on arXiv, the submitted source is the best format that exists:

```bash
dir=$(scripts/arxiv-source 1205.7018)     # unpacks into a mktemp directory
ls "$dir"/*.tex
```

The main file is usually the `.tex` containing `\documentclass`, or the one
`\input`/`\include` lines point into. Exit 3 means the author submitted a PDF
only and no LaTeX exists.

Everything else, in the order rule 1 implies:

- **paperclip** — read only what you need: `paperclip grep <pattern> /papers/<id>`,
  `paperclip scan`, `paperclip ls /papers/<id>/sections/`. Line numbers make quotes
  citable as `#L45-L52`. One section costs roughly 200 tokens against 40k for a
  whole paper, so never `cat` a paper you can grep — and `cat` truncates large
  files anyway (see the defects below).
- **Europe PMC JATS XML** — authored structure: sections, equations, references.
  Far cleaner than the PDF of the same article.
- **OpenAlex GROBID TEI XML** — a machine parse of the paper's own PDF. Costs $0.01
  against the OpenAlex budget, does no OCR, and its header and reference parsing
  makes mistakes: trust the body, re-check the metadata elsewhere.
- **PDF, when unavoidable** — `pdftotext -layout file.pdf -`. If that returns
  almost nothing, the PDF is a scan with no text layer: read it visually and
  re-check every quote character by character.

### The ladder, in short

1. **paperclip** — already-extracted, line-numbered full text. Fastest, and the
   line numbers make quotes citable as `#L45-L52`.
2. **arXiv LaTeX source** — the best format that exists for anything on arXiv.
3. **CORE and Unpaywall** — the two large open indices, plus OpenAlex and Europe
   PMC, which answer the same question from different angles.
4. **Google Scholar** — has no official API; the scraping recipe, the silent
   block that looks like an empty result set, and the paid SerpApi alternative are
   all documented in `reference/scholar.md`.
5. **Web search, and Gemini grounded search** — publisher pages, institutional
   repositories, theses, author copies. Gemini runs real Google Search queries and
   returns answers with citations, which reaches material paperclip's four backends
   do not index. Results are leads to verify, never sources to quote.
6. **Shadow libraries** — last resort only, when nothing above has a copy.
   Unlicensed, not open. Within the rung the order is **LibGen** (the only one
   with a real JSON API and no key), then **Sci-Hub**, then **Anna's Archive**
   (whose download half needs paid membership), then **welib.org / Z-Library**
   (browser only). Fetched copies are verification-only and must never be
   committed — arXiv's own terms forbid re-serving e-prints, and the reasoning
   applies with more force here.

   Mirrors churn constantly and an HTTP 200 proves nothing: `sci-hub.tf` answers
   200 and redirects to an ad landing page. Run `scripts/allpapers-mirrors` — it
   verifies content, not status — and consult <https://open-slum.org/> for live
   status. Detail in `reference/shadow-libraries.md`.

Full detail, including what to do when paperclip's rate limit is exhausted, is in
`reference/ladder.md`.

### The composite BibTeX entry

No single index is right about everything, so the entry is merged field by field
rather than taken whole from one:

```bash
scripts/allpapers-bibtex 10.1103/PhysRevD.59.043516
scripts/allpapers-bibtex arXiv:1706.03762 --bibmd     # as a bib.md record
scripts/allpapers-bibtex 10.1038/nature14539 --raw    # each index unmerged
```

Six indexes are consulted — INSPIRE-HEP, Crossref, DataCite, arXiv, PubMed and
Google Scholar — and each field is taken from the index most likely to be right
about that particular field. Disagreements are *printed* rather than silently
resolved, so they can be checked rather than assumed away.

Google Scholar is consulted on every lookup and trusted last for every field. It
sometimes carries a venue for grey literature no registration index has, so
skipping it loses information; but it does not reliably return the paper you asked
for even on an exact title-restricted query, so it never outranks a registration
record. Its contribution — or its silence — is reported either way.

Normalisations applied, each fixing something measured:

| Fix | Why it exists |
|---|---|
| Exotic spaces folded | APS deposits author initials separated by `U+2009` THIN SPACE and Crossref passes it through — 325 of them in the LIGO detection paper. Under pdflatex with `utf8` inputenc this is a *hard build failure*, not a cosmetic issue. Accents and curly quotes compile fine and are left alone. |
| Title case protected | `plain.bst` and friends run `change.case$` over the title and lowercase anything not braced. BibTeX has no idea what maths is, so `$N$` becomes `$n$` — Maldacena's paper renders as "The large n limit". Maths spans and mixed-case words (AdS, QCD, McDonald) are brace-protected. |
| DOI case restored | Crossref's BibTeX export lower-cases the DOI while its own `url` field keeps the registered casing. Nothing breaks, but the entry then disagrees with every other citation of the same paper. |
| Empty authors dropped | Crossref author arrays sometimes end with an empty name, which renders as a phantom final author. |
| Page labels | `pp. 436--444` for a range, but a bare `043516` for an APS article number — writing "pp." there claims a page range that does not exist. |
| Credentials scrubbed | API keys are stripped from every URL before it is recorded, so a key can never reach the committed record. |

Two traps merging cannot fix. The **reprint trap**: arXiv's Atom record carries a
`doi` and `journal_ref` that may point at a later reprint rather than the version
you read. The **identity trap**: every index here is keyed by the identifier you
supplied, so if that identifier is wrong, six indexes will agree confidently about
the wrong paper.

### Verification

Retrieval is only useful if the record of it survives. `reference/verification.md`
carries the project's citation-verification requirements: every cited paper is
downloaded and read, its metadata cross-checked against an authoritative index,
and every claim the citing text makes about it backed by a verbatim quote with a
locator — all recorded in a `verification/bib.md` beside the `.tex` file. Numerical
claims get the same treatment in `verification/equations.py`, recomputed
independently rather than transcribed. The file also holds the fourteen-channel
sourcing flow the ladder is derived from, and the hard rules about quoting,
shadow-library copies, and recording `NO-SOURCE` rather than quietly dropping to
abstract-level verification.

`allpapers-fetch` implements this as a two-step workflow, because a search result
is a candidate and not yet a source:

```bash
scripts/allpapers-fetch arXiv:1706.03762 --stage      # to a temp dir; nothing permanent
# read it, then one of:
scripts/allpapers-fetch arXiv:1706.03762 --promote /tmp/allpapers-… --justification '…' --quote '…@#L7'
scripts/allpapers-fetch arXiv:1706.03762 --reject     --justification '…'
```

A promotion puts the LaTeX source, the original tarball, the extracted
`content.lines`, the PDF, a `.bib` file and a `PROVENANCE.json` into
`verification/source/<citationKey>/`, and writes a `bib.md` record carrying the
composite BibTeX entry, every source URL used, the abstract, the justification, and
each claim with its verbatim quote and locator. A rejection writes the same record
minus the files, so the next reader knows the paper was examined and why it was
declined — which is worth as much as an inclusion and stops the dead end being
re-explored.

#### Where `verification/` is created, and how to move or silence it

**It is created in the current working directory**, as `./verification/`, the
first time a paper is kept, rejected or retired — so run `allpapers-fetch` from
the root of the paper or repository the record belongs to. Nothing is written
before then: a plain lookup, a search, or a `--stage` run touches only a temp
directory.

The layout is:

```
verification/
  bib.md                        the canonical record: entry, abstract, justification, quotes
  source/<citeKey>/
    <citeKey>.bib               the composite entry on its own
    latex/                      unpacked arXiv source, when any exists
    <citeKey>-arxiv-src.tar.gz  the tarball exactly as arXiv served it
    content.lines               paperclip's extracted, line-numbered text
    fulltext.xml                Europe PMC JATS, when the paper is in PMC
    <citeKey>.pdf               the PDF
    PROVENANCE.json             every URL fetched and what came back
```

Two switches control it:

| Switch | Effect |
|---|---|
| `--into DIR` | Put the directory somewhere else. Relative paths resolve against the current directory, so `--into ../shared/verification` and `--into /abs/path` both work. `$ALLPAPERS_VERIFICATION_DIR` sets the same thing once for a whole shell. |
| `--no-record` | Write nothing to it at all, and do not create it. The paper is fetched to a temp directory, the report and the composite BibTeX entry are printed, and the current directory is left untouched. |

`--no-record` is for looking something up without committing to it — checking
what a paper says, grabbing an entry for a `.bib` file, reading a candidate you
have no intention of citing. It cannot be combined with `--promote`, `--reject`
or `--retire`, since those modes exist only to write the record.

```bash
scripts/allpapers-fetch 10.1038/nature14539 --no-record        # nothing lands on disk here
scripts/allpapers-fetch 10.1038/nature14539 --into ~/refs      # ~/refs/bib.md instead
export ALLPAPERS_VERIFICATION_DIR=~/refs                       # for the rest of the shell
```

**A caveat on directory names.** Citation keys from INSPIRE-HEP contain a colon
(`Vaswani:2017lxt`), and the directory is named for the key exactly as specified.
Colons are legal on Linux and macOS but illegal in Windows filenames, so a
repository containing `verification/source/Vaswani:2017lxt/` will not check out on
Windows. If that matters for your repository, sanitise the directory name — the
key inside the `.bib` entry must not change.

### The report at the end

Every lookup finishes by telling the user, explicitly:

1. **Every source consulted, in order, with its outcome** — including the ones that
   returned nothing, and including rungs skipped because an earlier one succeeded.
   "paperclip: 3 hits" and "CORE: rate-limited, not consulted" are both findings.
2. **Where the search stopped and why** — found what was needed, or exhausted the
   ladder. If it exhausted the ladder, what the last resort returned.
3. **The full composite BibTeX entry** for every paper found, as written to
   `verification/bib.md`.
4. **Anything unverified** — an `identity unconfirmed` location that was used, a
   field only one index carried, a quote taken from a PDF text layer rather than
   source, a Scholar result that could not be checked because Scholar was blocking.

`allpapers-locate --json` and `allpapers-bibtex --json` give the material for 1
and 3 without re-running anything.

### Reference files

| File | Contents |
|---|---|
| `reference/ladder.md` | The priority ladder and what to do when a rung fails |
| `reference/paperclip.md` | The CLI, its REST transport, and why to use the CLI |
| `reference/arxiv.md` | LaTeX source retrieval, payload shapes, HTML, the Atom API |
| `reference/core.md` | CORE API v3, auth, rate limits, data-quality traps |
| `reference/unpaywall.md` | Unpaywall API, response shape, the broken search endpoint |
| `reference/search.md` | Ranking modes, result limits, sort order, how to word a query |
| `reference/other-indices.md` | OpenAlex, Crossref, Europe PMC, Semantic Scholar, NCBI, DOAJ, OpenAIRE |
| `reference/scholar.md` | Google Scholar URL patterns, the silent block, CAPTCHA handling, SerpApi |
| `reference/gemini.md` | Gemini grounded search: the API and `agy` backends, request shapes, citation extraction |
| `reference/bibtex.md` | The composite merge, the per-field trust order, every normalisation applied |
| `reference/scihub.md` | scihub-cli, its defects, mirror state, the manual fallback |
| `reference/shadow-libraries.md` | LibGen/Anna's Archive/Z-Library APIs, live mirror status, SLUM, the traps |
| `reference/verification.md` | `verification/bib.md` and `verification/equations.py` |

## How many papers are there?

Every number below was read from the service's own API or site on **2026-08-25**
— except the three shadow-library rows, measured **2026-08-26** — not from a
marketing page. The query used is given so each can be re-checked.

| Service | Records | What that counts | How it was measured |
|---:|---:|---|---|
| OpenAlex | 322,042,936 | all scholarly works | `api.openalex.org/works` → `meta.count` |
| CORE | 259,057,483 | works aggregated from repositories and journals | `api.core.ac.uk/v3/search/works/?q=*` → `totalHits` |
| Crossref | 185,829,151 | registered DOI records | `api.crossref.org/works?rows=0` → `message.total-results` |
| Unpaywall | ~120,000,000 | DOI records tracked for OA status | "Search all 120M of our articles" — unpaywall.org's own site bundle |
| PubMed | 41,056,331 | biomedical citations (abstracts, not full text) | eutils `esearch db=pubmed` |
| DOAJ | 13,487,985 | articles in indexed open-access journals | `doaj.org/api/search/articles` → `total` |
| PMC | 12,547,390 | full-text biomedical articles | eutils `esearch db=pmc term=all[sb]` |
| **paperclip** | **11,624,272** | **full text already extracted and line-numbered** | `paperclip sql` (see note below) |
| PMC open-access subset | 8,171,125 | the redistributable part of PMC | eutils `esearch term="open access"[filter]` |
| arXiv | 3,146,378 | cumulative submissions through 2026-08 | `arxiv.org/stats/get_monthly_submissions`, summed |
| Anna's Archive | 157,010,964 | papers (plus 71,400,751 books) | Wikipedia, 2026-08-20 — the service's own stats page is a JS bundle |
| Sci-Hub | 84,794,279 | "papers in Sci-Hub library" | front page of `sci-hub.ee`, 2026-08-26 |
| LibGen | *unmeasured* | — | no count is exposed on the front page or through `json.php` |

**Open-access subtotals**, also live from OpenAlex: 121,719,172 works are
`is_oa:true`, and 47,547,905 have `has_fulltext:true`. So of ~322M known works,
roughly 38% are open access in some form and about 15% have machine-readable full
text anywhere. That gap is the reason the ladder exists.

**OpenAlex now stores full text itself**, which is new and changes the ladder.
Counted the same way on the same day: **48,978,284** works have a cached GROBID TEI
XML parse (`has_content.grobid_xml:true`) and **52,396,004** have a cached PDF
(`has_content.pdf:true`). The XML is structured text — sections, paragraphs,
references — so it ranks above any PDF. Downloading either needs a free API key and
costs $0.01 per file against the account's daily budget.

paperclip's 11,624,272 is the sum of its three backends — PMC 8,014,647,
arXiv 3,106,926, and bioRxiv+medRxiv 502,699 (413,666 + 89,033). It has to be
summed by hand: see the defect note below.

### The overlap is large, and it is not incidental

These are not 900M distinct papers. The indices are layered on each other:

- **Crossref is the spine.** Unpaywall is built directly on it — it takes Crossref
  DOIs and asks, for each one, where a free copy lives. So Unpaywall's ~120M is a
  subset of Crossref's 186M, not an addition to it.
- **OpenAlex is a superset of Crossref**, adding records from PubMed, arXiv,
  institutional repositories and elsewhere that never got a Crossref DOI. It is
  run by the same organisation as Unpaywall and carries the same OA data.
- **CORE aggregates repositories**, so the same paper appears once per repository
  that holds it. Its 259M counts deposits, not distinct papers, which is why CORE
  returns several records for one DOI.
- **paperclip re-indexes PMC, arXiv, bioRxiv and medRxiv**, all of which are
  already inside OpenAlex and CORE. Its value is not corpus size but that the full
  text is already extracted, sectioned and line-numbered.
- **arXiv sits inside all of them**, and paperclip holds 3,106,926 of arXiv's
  3,146,378 submissions — about 98.7%.

A useful way to read the table: OpenAlex's 322M is close to the real number of
distinct known works, 121.7M of those are open in some form, and everything else
in the table is a differently-shaped view of that same population. Querying
several indices is still worth it, because they disagree about *where* the free
copy is, and one will often know a repository copy the others have missed.

## Keys, quotas and rate limits

Every number in the "free limit" column was **measured live on 2026-08-26** from
the service's own response headers unless it is marked otherwise. Values marked
*(their docs)* come from the service's published terms because the service returns
no rate-limit headers; values marked *(not measured)* are recorded for completeness
and were not verified here.

| Service | Key or registration | Free limit | Raised by |
|---|---|---|---|
| **paperclip** | Browser OAuth login; `PAPERCLIP_API_KEY` or `--api-key` for non-interactive use | free-tier usage cap | API key — <https://paperclip.gxl.ai/keys> |
| **Crossref** | none | **10 requests/second** (`x-rate-limit-limit: 10`, `x-rate-limit-interval: 1s`) | a `mailto:` in the User-Agent or query puts you in the polite pool — confirmed by `x-api-pool: polite-single`. Paid Metadata Plus exists *(not measured)* |
| **OpenAlex** | none, but a free key is worth having | **$0.10/day** — 1000 credits at 1 credit per metadata lookup, reset at midnight UTC (`x-ratelimit-limit-usd`, `x-ratelimit-reset`) | free key at <https://openalex.org/users> → **$1/day**; paid tiers $20/$100/$200+ per day |
| **Unpaywall** | no key, but `email=` is required on every call | "Please limit use to 100,000 calls per day" *(their docs)*; no rate-limit headers returned | bulk data dump for heavier use |
| **CORE** | free key | metered in **tokens**, not requests (a simple query costs 1, a complex one 3–5): **100 tokens/day** unauthenticated, max 10/minute, **and full text is withheld** | free personal key → **1,000 tokens/day**; academic → 5,000/day; academic at a CORE-supporting institution → negotiated, ~200k/day. See the tier table above |
| **Europe PMC** | none | no published limit; returns no rate-limit headers | — |
| **NCBI E-utilities** | none; free key available | **3 requests/second per IP**, enforced with HTTP 429 rather than throttling | free key at <https://www.ncbi.nlm.nih.gov/account/settings/> → **10/s**, passed as `&api_key=` |
| **Semantic Scholar** | none; free key available | a **shared** anonymous pool — a single cold call to `/paper/search` returned **429**, and succeeded on the immediate retry | free key — <https://www.semanticscholar.org/product/api#api-key> |
| **arXiv** | none | **1 request every 3 seconds, one connection at a time**, across all machines you control *(their terms of use)* | — (bulk access is via dumps, not a higher API limit) |
| **DataCite** | none | no published limit; returns no rate-limit headers | — |
| **INSPIRE-HEP** | none | no published limit; returns no rate-limit headers | — |
| **Google Scholar** | none — there is no official API | blocks by IP address, **invisibly** (HTTP 200, full page, no results) | paid SerpApi — `serpapi_key` |
| **Gemini grounded search** | **API key required**, free and instant at <https://aistudio.google.com/apikey> | per-model and per-day free-tier caps; see <https://ai.google.dev/gemini-api/docs/rate-limits> | paid tier |
| **LibGen** | **none** — metadata *and* download work unauthenticated | none published, none observed; no rate-limit headers | — |
| **Sci-Hub** | none | none — the constraint is availability, not rate | — |
| **Anna's Archive** | search needs none; details and downloads need your **account secret key** (the string you log in with) | free users get "slow downloads" with a countdown, browser only | **paid donation/membership** for fast downloads — the only paid tier among the shadow libraries |
| **Z-Library** | account required | daily download cap | paid tier raises the cap *(not measured)* |

Store keys with `scripts/allpapers-setup --set <name>=<value>`; run
`scripts/allpapers-setup --check` to see which are present. Keys are scrubbed
from every URL the tools print or write, so they never reach `bib.md`.

## Caveats by source

Each of these was reproduced against the live service. They are grouped by source
so you can read just the ones you are about to use; full detail is in the matching
`reference/` file.

### paperclip

- **`-n` defaults to 20, not the 100 its `--help` claims.** Measured at exactly 20
  on `pmc`, `arxiv`, `abstracts`, `trials/us` and `fda`, unchanged by `--all`, with
  `-n` honoured exactly up to 500. Nothing warns you the rest existed. **Always
  pass `-n 250`.**
- **`cat` on a large file truncates**, printing a banner such as
  `[~9784 tokens total, showing first ~1000 chars]`. Use `head -n 500`,
  `sections/`, `grep` or `scan` instead — reading one section costs about 200
  tokens against roughly 40k to load a whole paper.
- **`-c/--count` is documented as "count only (no results)" but is a no-op** — it
  returns the full list anyway.
- **`SELECT COUNT(*)` returns one row per backend**, not a total.
- **`lookup --json` ignores the flag** and prints human text anyway, and exits 0
  even when it found nothing.
- **Some records carry future publication dates** — a `2027-08-01` at the head of a
  date-sorted PMC list — so the top of `--sort date` is not reliably the newest
  real work. Sanity-check the head.
- **`sql` sees titles and abstracts, not bodies.** To find papers *containing* a
  string use `grep`, not `sql … ILIKE`.
- **While a repo is checked out, every search is written to that repo's audit
  trail.** Run `paperclip repo checkout -` before unrelated exploratory work.
- **The shell is sandboxed**: `rm`, `curl`, `wget`, `ssh` and `sudo` are blocked,
  and shell loops and `xargs` are unsupported. Use `bash '...'` for pipes and
  redirection into `/.gxl/`.

### CORE

- **CORE mis-attributes DOIs**, and it is not a rare edge case. Re-measured with a
  registered key on 2026-08-26: `q=doi:"10.1038/nature14539"` returned **three**
  results, of which only the second was that paper — the other two were a Spanish
  thesis on advertising campaigns and a Spanish software-engineering thesis, both
  carrying the DOI because it appears in their reference lists. A second DOI query
  returned 25 hits for one DOI. `allpapers-locate` therefore checks the title
  before trusting any CORE record.
- **A bare quoted phrase returns HTTP 500.** Reproduced twice each on 2026-08-26:
  `q="thematic analysis"` → 500, while `q=thematic analysis` → 200 (15,820,682
  hits) and `q=title:"thematic analysis"` → 200. **Quoted phrases must be
  field-qualified**; an unqualified one is a server error, not an empty result.
- **CORE withholds full text from anonymous users**, returning the literal string
  `"Not available for public API users."` in the `fullText` field. A key does fix
  this — verified: with a key, records came back carrying 38,460 and 68,513
  characters of real text. But **most records still return `fullText: ""`** — an
  empty string, not the refusal message — so with a key you can no longer tell
  "no text stored" from "not allowed" by reading that field.
- **`sourceFulltextUrls` does not reliably contain URLs.** Measured: a record whose
  `sourceFulltextUrls` was a one-element list holding a *reference-list citation
  string* — `"Álvarez Calleja, M. A. (s.f.). Denotación Y Connotación…"` — with a
  URL merely embedded at the end of the prose. Validate each element as a URL
  before fetching it.
- **The field names are camelCase throughout** — a snake_case guess silently
  returns nothing.
- **A trailing slash on the endpoint causes a 301** that drops the auth header.

### Unpaywall

- **`/v2/search` returns HTTP 500** on every variation tried. DOI lookup works
  normally.
- **Unpaywall covers Crossref DOIs only.** DataCite DOIs are excluded by design, so
  an arXiv paper looked up by its `10.48550/arXiv.…` DOI returns nothing. That is
  not a miss — go to arXiv directly.

### OpenAlex

- **OpenAlex mis-attributes DOIs too**, by the same mechanism as CORE. Of the five
  locations it lists for Braun and Clarke's "Using thematic analysis in psychology",
  only the journal's `publishedVersion` was that paper; two repository entries were
  confirmed to be entirely different articles. Neither index gives you a field that
  separates good matches from bad, so `allpapers-locate` marks every location it
  cannot prove — anything that is not a publisher `publishedVersion` and does not
  carry the work's own DOI, arXiv ID or PMCID in its URL — as
  `identity unconfirmed`.
- **OpenAlex is metered in dollars now**, which is easy to miss because nothing
  breaks until it does. Every response carries `x-ratelimit-limit-usd` and
  `x-ratelimit-remaining-usd`.
- **Its GROBID full text is a machine parse of a PDF and does no OCR**, so a
  scanned paper yields an empty or near-empty TEI body rather than an error.

### Europe PMC

- **The full-text path takes one segment, not two**:
  `…/webservices/rest/{PMCID}/fullTextXML`. Inserting a source segment 404s.
- Its JATS is authored XML, so it beats a GROBID TEI parse of the same paper even
  though both sit in the `xml` tier of the format ranking.

### NCBI (PubMed / PMC)

- **`idconv` only knows papers that are in PMC**, and reports everything else as a
  per-record `status: error` under an HTTP 200 and a top-level `status: ok`.
  Measured on a 20-PMID spread across 1953–2024 it resolved 10 DOIs where
  `esummary` resolved 18 — including Watson and Crick 1953, which it calls not
  found. Reading its silence as "no such paper" is the easy mistake.
- **The 3/s limit is enforced with HTTP 429 mid-sequence**, not by throttling.
  Batch identifier lists rather than looping.

### Semantic Scholar

- **A DOI lookup can 404 for a paper Semantic Scholar actually holds.** Measured:
  `/graph/v1/paper/DOI:10.1038/nature14539` returned
  `{"error":"Paper with id … not found"}` on all three path forms, yet a title
  search returned the paper — with `externalIds.DOI` set to `null`. Never read an
  S2 404 as "this paper does not exist"; fall back to title search.
- **The anonymous pool is shared and saturated.** A single cold call to
  `/paper/search` returned 429 and succeeded on the immediate retry, so retry logic
  is mandatory even for one-off lookups.

### arXiv

- **`/src/` is not always a tarball, and a 200 does not mean LaTeX.** It can be a
  bare gzipped `.tex`, or `application/pdf` when the author submitted no source at
  all — 6 of 45 papers measured on 2026-08-26. `scripts/arxiv-source` exits 3 in
  that case, and `scripts/allpapers-locate` now checks the payload type so a
  PDF-only submission is labelled `pdf` instead of sorting to the top as `latex`.
- **arXiv's HTML is a subset of source availability, not a fallback for it.**
  `https://arxiv.org/html/<id>` is converted from the submitted TeX, so a paper
  with no TeX has no HTML: across 45 papers `/html/` never once succeeded where
  `/src/` failed, and the 6 PDF-only papers 404ed on `/html/` 6 for 6. It is
  genuinely useful — it reaches back to at least 2000 (`math/0010150`) and saves
  unpacking a tarball — but do not spend a request on it after `/src/` fails. The
  reverse gap is the real one: 2 of 45 had source with no HTML backfilled yet.
- **Old-style arXiv IDs need their slash.** paperclip renders them stripped
  (`arx_math0010150` for `math/0010150`) and every arXiv endpoint 404s on that
  form. Both scripts restore it; before that fix the ID fell through to a title
  search for the literal string.
- **arXiv mints a DataCite DOI (`10.48550/arXiv.<id>`)**, so Crossref-based tools
  find nothing for it. Query DataCite, or use the arXiv ID directly.
- **Their terms forbid storing and re-serving e-prints** from your own servers.
  Local copies for verification are fine; redistribution is not.

### Google Scholar

- **Scholar is a discovery tool, not an identity resolver.** Live probes on four
  exact-title queries put the queried paper outside the returned results entirely.
  Use it to find copies, not to confirm which paper you are holding.
- **Scholar's block is invisible.** When it refuses a caller it returns HTTP 200
  and a full-size ~142 kB page with no CAPTCHA marker and no results —
  indistinguishable from "not indexed" unless you read the prose. Two further
  traps: the result-block class names appear 24 times in the page's own inlined
  CSS, so testing for their presence reports success on an empty page; and the
  message's apostrophe is entity-encoded (`can&#39;t`), so a literal string match
  never fires. Not User-Agent dependent — the address is what is refused.
- **The citation-export endpoints do not answer**: `output=cite` returned HTTP 404
  and `view_op=export_citations` HTTP 302 to sign-in. A lot of third-party code
  still documents these as the way to get BibTeX out of Scholar.

### Gemini grounded search

- **Grounding is the model's choice, and an ungrounded answer looks exactly like a
  grounded one.** Asked which paper introduced the Transformer architecture,
  `generateContent` returned HTTP 200, a correct answer, and no `groundingMetadata`
  key at all — no queries, no citations, no error. It answered from its own weights
  without searching. The same question aimed at recent work came back with eight
  grounded citations. So an empty citation list means *ungrounded*, not *nothing
  found*, and `allpapers-search` now prints that warning rather than a bare answer.
- **Citation URLs are opaque Vertex redirects** of the form
  `https://vertexaisearch.cloud.google.com/grounding-api-redirect/<token>`. They
  resolve in a browser, but the token says nothing about the destination, so they
  must never be recorded as source URLs in `bib.md`. Resolve to the real URL first,
  or record the identifier instead.
- **Model overload is a routine transient failure**, not a bug in your request:
  HTTP 500 on `interactions` and 503 on `generateContent`, both succeeding on
  retry.
- **Two backends, and only one of them is billed.** `--gemini-backend api` calls
  `generativelanguage.googleapis.com` and needs `GEMINI_API_KEY`, which bills a
  Google Cloud account — a Gemini subscription does not pay for it.
  `--gemini-backend agy` shells out to the Antigravity CLI instead, which signs
  in with an ordinary Google account, needs no key, and has the same Google
  Search behind it. `auto`, the default, uses the API when a key is configured
  and falls back to `agy`. Both were verified end to end on 2026-08-26, and so
  were both API endpoints: `interactions` returned text, the queries it ran and 4
  citations, and the `generateContent` fallback returned 8 citations out of
  `groundingChunks[].web` plus 3 `webSearchQueries`.
- **The `agy` backend returns prose, not grounding metadata.** The API reports the
  Google Search queries it ran and annotates each citation; `agy` returns a plain
  answer, so `allpapers-search` parses the links back out of the Markdown and the
  queries are simply not recoverable. The upside is that its links are the real
  destinations rather than Vertex redirect tokens.
- **`agy` hangs if gnome-keyring can grab the terminal.** Run it with `DISPLAY=""`,
  `SSH_CLIENT` and `SSH_TTY` set — see [Running `agy` from a
  script](#running-agy-from-a-script). `allpapers-search` sets those itself.
- **Grounded answers are leads, not sources.** `allpapers-search` prints an
  `allpapers-locate` command for every identifier it extracts, so each one gets
  confirmed against a real index before it is cited.
- **Identifiers in grounded answers arrive wrapped in Markdown.** A grounded answer
  writes a DOI as `` `10.48550/arXiv.1706.03762` `` or `**10.1038/nature14539**`,
  so the extraction regex has to exclude backticks, asterisks and pipes as well as
  prose punctuation — a captured trailing backtick lands in the printed shell
  command and opens command substitution on paste.

### Crossref and DataCite

- **Crossref lower-cases DOIs in its response.** The registered casing has to be
  recovered from the entry's own `url` — `10.1103/PhysRevD.59.043516`, not the
  lower-cased form.
- **DataCite returns `10.48550/ARXIV.…` in upper case** where the registered form
  is mixed case (`10.48550/arXiv.…`).

### Shadow libraries (Sci-Hub, LibGen, Anna's Archive, Z-Library)

Full detail in `reference/shadow-libraries.md`. The load-bearing ones:

- **HTTP 200 is not evidence of a working mirror.** `sci-hub.tf` answers 200 and
  redirects offsite to `arcade.now`, an ad/scam landing page; `sci-hub.hkvisa.net`
  redirects to `sci-hub.usualwant.com`. `yqrii5.org` and `wbsg8v.xyz` answer on 443
  but return a 129-byte "Link expired or invalid" — they are Anna's Archive
  signed-URL download edges, not browsable mirrors. `scripts/allpapers-mirrors`
  therefore verifies content and the final hostname, not the status code.
- **The published mirror lists are stale and wrong.** Both
  <https://www.sci-hub.pub/> and <https://scihub.help/> list `sci-hub.st`,
  `sci-hub.se` and `sci-hub.red` as working; all three were dead when measured, and
  neither site offers machine-readable output. Prefer <https://open-slum.org/>.
- **SLUM is the best status source, and still needs verification.** It checks every
  5 minutes and its `PROTECTED` status — meaning "behind a JS/anti-bot challenge" —
  is the single most useful signal, because it marks exactly the hosts `curl`
  cannot use. But it has **no API** (nine candidate JSON paths all return the same
  28 KB SPA 404 page; the status is inlined in the HTML), it reports `UP` for hosts
  that serve nothing usable, and it disagreed with direct measurement in both
  directions — it called `libgen.gl` DOWN while the API answered normally there.
- **Sci-Hub has only two live backends behind seven working names.** `sci-hub.ru`,
  `.su` and `.box` return identical hit counters; `.al` and `.mk` return identical
  text. Trying more domains after one fails buys very little. The set also flaps
  within a single session: `sci-hub.ru` served a full front page and then failed TLS
  about an hour later.
- **LibGen is the only shadow library with a real API** — `json.php`, no key, no
  signup. `object=e&fields=*&doi=…` returns the edition and its file md5s;
  `object=f&fields=*&ids=…` returns `extension` and `filesize`, which are **absent**
  from the edition record, so a DOI lookup alone cannot tell you whether you are
  about to fetch a 2 MB PDF or a 900 MB djvu.
- **`{"error":"No Request keys"}` has nothing to do with API keys.** LibGen calls
  the *record selectors* "Request keys", and the message is overloaded across two
  causes: no selector (`?object=e&fields=*`), or an invalid `object=` value even
  with a valid selector. Check the object name and the selector; authentication is
  never the problem.
- **LibGen escapes forward slashes in JSON** — `"doi":"10.1038\/nature14539"` — so
  matching on a plain DOI string silently finds nothing. This one bit the mirror
  checker during testing.
- **LibGen downloads need a one-time nonce.** `get.php?md5=…` alone 307-redirects to
  `/ads.php?md5=…`; that page embeds `get.php?md5=…&key=<NONCE>`. The key is
  single-use, so it cannot be cached.
- **Anna's Archive HTML is unusable by script, but `/dyn/` is not.** `/scidb/<doi>/`
  403s behind DDoS-Guard on every live domain, while `/dyn/torrents.json` (17.7 MB)
  and `/dyn/api/fast_download.json` answer normally. The latter **self-documents its
  full contract in its own 400 error body**; 400 means bad md5, 401 means the key is
  missing or not a member. Anna's Archive's own error text names **Wikipedia** as
  the authoritative list of its current domains.
- **Z-Library cannot be reached with `curl` at all** — three domains 307 to a gate,
  three return a Cloudflare 503 — and it assigns each user a personal domain after
  login, so there is no stable host to script against. `welib.org` is the usable
  member of that family.
- **`libstc.nexus` is not a service.** Every path returns the same 4,839-byte
  static "Nexus Bots" placeholder linking elsewhere; the real STC hub is
  `hub.libstc.cc`.
- **scihub-cli's block-page detector false-positives on live mirrors** — they serve
  real pages to a browser User-Agent — and then blacklists them for about 300
  seconds, persisted across runs, so an immediate retry dies with "All mirrors are
  unavailable". `-m/--mirror` is ignored by the router.
- **scihub-cli exits 1 if any identifier failed and 0 only when all succeeded**, and
  writes `download-report.json` only when something failed — so the file's absence
  is not evidence of a problem, and its presence is.
- **Old-journal PDFs are often image scans with no text layer** (`pdftotext` returns
  roughly 0 bytes). Read them visually and re-check quotations character by
  character.
