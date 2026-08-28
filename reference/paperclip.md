# paperclip

A hosted, read-only virtual filesystem over full-text literature, driven from
bash. **11,624,272 papers** as of 2026-08-25: PMC 8,014,647, arXiv 3,106,926,
bioRxiv 413,666, medRxiv 89,033. Plus regulatory documents, clinical trials,
protein records and patents.

That figure is from `paperclip sql`. The CLI's own `ls /` labels the same
directory **"3.4M+ scientific papers"** — a 3.4x disagreement inside one tool's
output — and labels `trials/` "110K+" where the published corpus description says
over a million. **Treat the `ls /` labels as decoration and count with SQL.**

It is first on the ladder because the full text is already extracted, split into
sections and **line-numbered**, so a quote comes back citable as `#L45-L52` with
no parsing. Reading one section costs roughly 200 tokens; loading a whole paper
costs about 40k. Never `cat` a paper you could `grep`.

## Install and auth

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
paperclip login                    # browser sign-in
paperclip --version                # verified against 0.7.38
```

Non-interactively, set `PAPERCLIP_API_KEY` or pass `--api-key`. If the user
exhausts the free allowance, keys are at <https://paperclip.gxl.ai/keys>.

## Use the CLI, not the REST API

The transport underneath **is** a REST call, and it can be driven directly:

```
POST https://paperclip.gxl.ai/api/cli/execute
Authorization: Bearer <Firebase ID token>
{"command": "search", "raw": "-s arxiv -n 3 'attention is all you need'"}
```

The server parses `raw` as the tail of a shell command line. Confirmed working
against the live service: it returned HTTP 200 with
`{cwd, exit_code, output, result_data, result_id, elapsed_ms, download_url,
download_filename}`.

Despite that, **install the CLI and use it.** The client is 38,006 lines of
Python, and the parts that are not argument parsing are things a direct REST
integration would have to rebuild:

- **Auth is an OAuth 2.0 PKCE browser flow** producing a Firebase ID token that
  expires on a timer. The client refreshes it against `/api/oauth/token` whenever
  a request comes back 401, transparently.
- **The endpoint depends on the auth type.** With an API key against a remote
  server the client does *not* call `/api/cli/execute` at all — it posts JSON-RPC
  `tools/call` to `/papers` (or `/mcp` under OAuth) with
  `{"command", "description", "skip_truncation": true}`. A REST-only integration
  breaks for exactly the users who hit the free limit and got a key.
- **Results are truncated unless you ask for more.** The client re-fetches
  `/api/cli/results/{id}` whenever the inline payload is marked truncated or holds
  fewer papers than the reported count, and sets `skip_truncation` on the MCP
  path. Skip that and you silently lose results with no error.
- **`output` is ANSI-colored terminal prose**, not data. `result_data` is
  structured for some commands (`search` returns `papers[]` with `document_id`,
  `source`, `pub_year`, `title`, `authors`) but is absent for others — `ls`
  returned `result_id: None`.
- **Long commands need per-command timeouts** — up to 3500s for search workflows
  and structured maps, 7500s for exhaustive extraction. A default HTTP timeout
  kills them.

Other endpoints the client uses, for reference: `/api/cli/results`,
`/api/cli/results/{id}/page`, `/api/cli/results/import`, `/api/library/*`,
`/api/paper-repos/*`, `/api/user/upload`, `/api/user/documents`,
`/api/user/mcp/bash`. Base URL is overridable with `PAPERCLIP_BASE_URL`.

Run `paperclip skill` for the full built-in guide, and
`paperclip <command> --help` for any single command.

## Layout

Every document is a directory: `meta.json`, `content.lines` (full text, one
numbered line per line), `sections/`, `figures/`, `supplements/`.

ID prefixes `PMC`, `arx_`, `bio_`, `med_`, `fda_`, `tri_`. Paths:
`/papers/`, `/fda/{us,jp,eu}`, `/trials/{us,cn,jp,eu,intl}`, `/proteins/`,
`/patents/`, `/clipboard/` (your uploads), `/.gxl/` (the only writable path).

`/patents/` is searchable as `-s patents` and is not in the older skill docs.

## Commands that matter here

```bash
paperclip lookup doi 10.1038/nature14539     # exact metadata match
paperclip lookup arxiv 1706.03762            # NOT the 10.48550 DOI — see below
paperclip lookup pmc PMC3084216
paperclip search -s papers -n 250 "<query>"  # -s is mandatory; -n 250 always
paperclip grep <pattern> /papers/<id>        # regex over body text
paperclip scan FILE "p1" "p2" -C 5           # multi-pattern with context
paperclip ls /papers/<id>/sections/
paperclip head -n 40 /papers/<id>/content.lines
paperclip sql "SELECT ... FROM documents"    # titles and abstracts only, not bodies
```

Every search prints a result ID `s_xxxxxxxx`. `--from <id>` re-runs the next
command against exactly that set, so the productive loop is broad search →
`grep --from` to narrow → read → `grep --from` the same set again. Narrowing
inside a held set beats re-querying.

Query wording drives result quality more than any flag: the embedding model is
fine-tuned on abstracts, so a pasted abstract works best, one or two sentences
describing the *method or problem structure* next best, and bare keywords worst.
`--ranking analogical` finds the same structural method in unrelated fields.

### The rest of the surface

Rarely needed here, but there is no other place that lists them:

```bash
paperclip ask-image /papers/<id>/figures/f1.png "what does the y axis measure?"
paperclip ask-image ... --fn describe|extract-data   # prose, or the numbers
paperclip fetch <url-or-doi>            # download into /clipboard/ using your browser cookies
paperclip import refs.bib               # a bibliography, local PDFs, or a paper's
paperclip import <paper-id>             #   reference list via Semantic Scholar
paperclip upload FILE --into FOLDER     # the ONLY way to persist a file you generated
paperclip cp /papers/<id> /clipboard/x/ # zero-copy corpus link
paperclip skills show proteins          # read before any protein SQL
paperclip skills show paperclip-meta-analysis   # read before a systematic review
```

`paperclip repo` (alias `git`) tracks a paper collection plus *verifiable claims*;
`repo commit` re-checks each claim against the full text and marks it `[OK]` or
`[X]`. Subcommands: `init`, `add <id> "claim" [--lines L45-L52]`, `commit -m`,
`status`, `log`, `checkout`, `branch`, `merge`, `export bibtex|ris|csv|markdown`,
`history`, `citations`. **Do not start one unless the user asks** — this skill's
own `verification/bib.md` is the record, and while a repo is checked out every
search is written to its audit trail.

**`reference/search.md` is the full treatment** of the three lookup kinds, the
four rankings, result limits, sort order, the narrowing filters new in 0.7.38
(`--bool`, `--full-text`, `--has-full-text`, `--has-section`, `--exclude-*`,
`--year-min/max`) and the stateful `--from` loop. Read it before any sweep.

## Extraction quality (measured 2026-08-27)

Checked `arx_1706.03762` (129 lines) and `arx_1205.7018` (1002 lines, 101
numbered equations) line by line against the authors' arXiv LaTeX source.

**The LaTeX paperclip returns is reconstructed from the built PDF, not the
authors' source.** `\mathrm{Attention}` comes back as `\text{Attention}`; a bare
`\frac{QK^T}{\sqrt{d_k}}` gains `\left(...\right)`; `...` becomes `\dots`;
`\ref` and `\citep` are resolved to their printed numbers; equation numbers are
appended as `\quad (N)`, which exist only on the rendered page; author macros
(`\dmodel`, `\mrt`, `\eps`) arrive expanded. Content commented out in the `.tex`
is correctly absent — a source parser has to handle comments, a reader of the
PDF never sees them.

For reading, this beats raw source in two ways: the macros are already expanded,
and cross-references are resolved to numbers you can follow. Every equation
checked against source was mathematically equivalent, with no invented symbols
anywhere in the sample; in one place it emitted `\sin` where the authors had
written a bare `sin`.

**It is not verbatim, though.** A quote of a paper's own markup comes from
`scripts/arxiv-source`, never from `content.lines`.

Four fidelity defects, all measured:

- **A numbered equation can vanish silently.** In `arx_1205.7018` the numbered
  equations run 1.1 → 6.32 complete *except* 4.1, while the prose at L430 still
  reads "Now, using formula (4.1) for `\alpha_2`, we get the expressions for the
  jumps:" — a live reference to content that is not there. One loss in 101, with
  no marker of any kind. Cross-check against source whenever one specific
  equation carries the claim.
- **HTML entities leak into the math.** `arx_1205.7018` carries 393 of them
  (`&lt;` ×158, `&gt;` ×58, `&amp;` ×177), so an inequality arrives as
  `0 &lt; p &lt; \infty`, and the `&` alignment characters of `align` and
  `cases` arrive as `&amp;`. `arx_1706.03762` had 5, so it scales with math
  density. Unescape entities before treating the output as LaTeX.
- **Tables lose every cell boundary.** The Transformer's results tables run
  together as prose, so a number cannot be tied back to its row and column. Read
  tables from the source or the PDF.
- **Footnotes are placed by page position, not logical position.** Transformer
  footnote 4 lands inside §3.2.2 as `4To illustrate`, where it sat on the
  printed page rather than where it is referenced.

### Print-era papers are abstract-only, and nothing says so

Sampled 30 PMC papers with `pub_year` between 1950 and 1995. Every one returned
metadata and abstract, and **zero equations**. `content.lines` and `sections/`
have exactly the same shape as a full extraction and `meta.json` is silent, so
an agent that does not check reads an abstract and believes it read the paper.

Line count is not the tell — two of the sample returned 178 and 111 lines, but
they are conference-abstract volumes whose lines are affiliations and reference
entries. **The tell is `sections/`:**

```bash
paperclip ls /papers/<id>/sections/   # no narrative sections -> abstract only
```

A metadata-only record lists nothing but `Title`, `Metadata`, `Authors`,
`Affiliations`, `Abstract`, `Categories`, `Keywords`, `References` and
`Figures`. A real extraction lists narrative sections — `Introduction`,
`Methods`, `Results`, or the paper's own numbered tree. When there are none,
fall through to rung 2.

Little usable text is lost. Of those same 30 papers, 9 have a genuine OCR dump
at Europe PMC's `fullTextXML` (inside a `<preformat>` element of type
`pmc-pdf-text`) and 21 have only a stub reading "The Full Text of this article
is available as a PDF (N KB)" plus a reference list. Where the OCR dump exists
its equations are destroyed anyway — from PMC2225855, a sigma read as `E`,
subscripts stranded on their own lines, and one fraction scattered over four:

```
-d2 V dE F
=-=-E Zici (2)
dx
2 dx i
```

So the reference list is the real loss, not the math. For equations out of a
print-era paper there is no text route at all: read the PDF visually.

## Measured defects (v0.7.38, checked 2026-08-25)

- **Look arXiv papers up by arXiv ID.** `lookup doi 10.48550/arXiv.1706.03762`
  returns "No documents found"; `lookup arxiv 1706.03762` finds `arx_1706.03762`.
  The DataCite DOI is not indexed.
- **`lookup` exits 0 even when nothing was found.** Gate on the output containing
  a document ID, never on the exit code.
- **`lookup --json` ignores the flag** and prints the same human text.
- **`cat` silently truncates a large file to about 1000 characters.** Measured
  on `/papers/arx_1706.03762/content.lines`, 129 lines and 40,019 bytes: `cat`
  returned 33 lines and 1,974 bytes, exit 0, headed `[~9784 tokens total,
  showing first ~1000 chars]`; `head -n 500` returned all 130 lines and 40,019
  bytes. The banner is easy to scroll past, and nothing fails. Small files are
  not truncated — a 2.5 kB `meta.json` came back whole — so the behavior is
  size-dependent and will not show up in a quick test. **Use `cat --full`,
  `head -n <big>`, `sections/`, `grep` or `scan`; never trust a bare `cat` for a
  whole paper.** `--full` returns the whole file, but it is absent from
  `cat --help`, which lists only `-n`. The banner then suggests two remedies and
  **the second does not work**:

  ```
  cat --full FILE           # correct — all 129 lines, 40,011 bytes
  cat FILE > output.txt     # what the banner advises — writes 1,967 bytes
  ```

  The file that second command produces ends with the banner's own suggestions
  instead of the end of the paper.
- **`SELECT COUNT(*)` returns one row per backend, not a total.** `SELECT COUNT(*)
  FROM documents` printed three rows — 502699, 3106926, 8014647 — which must be
  summed by hand. `GROUP BY source` gives the four-row breakdown and was stable
  across four consecutive runs; an earlier run on this build omitted the arXiv
  backend, which has not reproduced since.
- **`-n` defaults to 20, and `--help` says 100.** Re-measured on 0.7.38: a bare
  search returned exactly 20, `-n 250` returned exactly 250. Nothing warns that
  the rest existed, so **always pass `-n 250`** for any sweep.
- **`-c/--count` is a no-op** — it returns the full list anyway.
- **`search --help` refuses to print help without `-s`.** It answers
  `Error: search requires a source flag (-s).` and lists the sources, exit 0. To
  see the option list, run `paperclip search -s pmc --help`.
- **The head of a `--sort date` list depends on the query**, so it is not an index
  frontier. Measured heads on 2026-08-25 ranged from 2026-04-01 to 2026-07-15
  across three queries and three backends. The previously recorded future-date
  defect did not reproduce in six sweeps. See `reference/search.md`.
- **The sandboxed shell blocks `rm`, `curl`, `wget`, `ssh`, `sudo`**, and does not
  support `for`/`while` loops or `xargs`. Use `bash '...'` for pipes and
  redirection into `/.gxl/`.
- **While a repo is checked out, every search is written to its audit trail.** Run
  `paperclip repo checkout -` before unrelated exploratory work.
- `paperclip update` regenerates `.claude/skills/paperclip/SKILL.md`, so never
  hand-edit that file — and note that this recreates the standalone `paperclip`
  skill that `allpapers` replaced. If it reappears after an update, delete
  `~/.claude/skills/paperclip/` again.
