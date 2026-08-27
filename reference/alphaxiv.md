# alphaXiv — AI paper summaries, and arXiv full text as Markdown

> **quickarxiv.org is alphaXiv.** It is a 302 shortcut, nothing more:
> `quickarxiv.org/abs/<id>` → `www.alphaxiv.org/overview/<id>`. Use the
> alphaXiv URL in anything scripted; the shortcut has a bug, below.

alphaXiv is an arXiv-only reading layer. Everything here was measured on
2026-08-26 with `curl`; nothing in this file is inferred from the site's
marketing copy.

Two endpoints matter, and **neither needs a key, an account or a browser**.
Both answer `text/markdown` to a plain GET. Neither appears in alphaXiv's own
API documentation, which covers only the MCP server described at the end.

| URL | What it is | Coverage measured |
|---|---|---|
| `www.alphaxiv.org/overview/<arxiv-id>.md` | an **AI-generated** report on the paper | 3 of 6 sample papers |
| `www.alphaxiv.org/abs/<arxiv-id>.md` | the paper's **full text**, PDF text layer as Markdown | 6 of 6 sample papers |

Both are arXiv-only. A DOI, PMCID or PMID returns
`{"status":404,"unhandled":true,"message":"HTTPError"}` — measured for
`10.1038/nature14539`, `PMC3084216` and `26017442`. There is no route in for a
paper that is not on arXiv.

## `/overview/<id>.md` — the quick check, and never a citation

This is the "what is this paper about" layer, and the reason to reach for
alphaXiv at all. It is a long-form report, roughly 20–25 KB, with a stable
six-section structure measured identical across papers:

```
### 1. Authors and Institution(s)
### 2. How This Work Fits into the Broader Research Landscape
### 3. Key Objectives and Motivation
### 4. Methodology and Approach
### 5. Main Findings and Results
### 6. Significance and Potential Impact
```

The web page carries a shorter structured version of the same material —
`summary`, `originalProblem[]`, `solution[]`, `keyInsights[]`, `results[]` — but
only the long report is exposed as `.md`.

**It is written by a model, and the file does not say so.** Two independent
confirmations that it is generated:

- alphaXiv's own client code labels this content in the UI with the tooltip
  string `aiGeneratedContent: "AI generated content"`, and stores it under the
  field name `intermediateReport`.
- alphaXiv's MCP documentation describes `get_paper_content` as returning, by
  default, "a structured AI-generated intermediate report optimized for LLM
  consumption".

The trap is that **the disclosure lives only in the web UI**. Fetch the `.md`
and you get a confident, well-organized "Research Paper Analysis" with no
marker anywhere in the file saying a model wrote it — `grep -ci 'AI-generated'`
returns 0 on the ones measured. A later session reading that file has no way to
tell it from something a person wrote.

So, as a hard rule:

- **Never quote it.** Not in `verification/bib.md`, not in an answer, not as a
  paraphrase attributed to the authors. It is not the paper's words and it is
  not even the authors' abstract.
- **It is weaker evidence than an abstract**, not stronger. An abstract is what
  the authors wrote; this is a model's reading of a PDF extraction. It does not
  qualify as abstract-level verification either — it does not qualify as
  verification at all.
- **What it is good for:** deciding whether to spend the fetch. It answers "is
  this the paper I want, is the method what I assumed, is the result the one
  being cited at me" well enough to save reading the wrong paper. Every claim
  it makes is a hypothesis to confirm against the real text.

Missing reports 404 cleanly and machine-readably, with the version pinned:

```
No intermediate report available for 0704.0001v2
```

Coverage skews to papers that get read. Present for `1706.03762` (Transformer),
`hep-th/9711200` (Maldacena) and `2608.24646` (a trending 2026 preprint); absent
for `astro-ph/0501171`, `0704.0001` and `1205.7018`. Do not build anything that
assumes a report exists.

## `/abs/<id>.md` — full text, at PDF-extraction quality

Every paper tried returned one, including old-style identifiers that other
tooling fumbles:

| Identifier | Bytes |
|---|---|
| `1706.03762` | 40,056 |
| `hep-th/9711200` | 51,613 |
| `astro-ph/0501171` | 93,629 |
| `0704.0001` | 104,205 |
| `1205.7018` | 174,151 |
| `2608.24646` | 176,103 |

Versions are pinnable and the text genuinely differs: `1706.03762v1.md` is
37,402 bytes against `v7.md`'s 40,056, and a bare ID serves the latest. A
version that does not exist (`v99`) returns the JSON 404 above. Pin the version
when a quote has to be reproducible.

**This is the PDF text layer, not the LaTeX.** It sits at `PDF (text layer)` on
the format ladder — below arXiv's submitted source and below arXiv's LaTeXML
HTML — and it earns that place:

- **Equations are destroyed.** No file in the sample carries any math markup at
  all — no LaTeX, no `\frac`, no delimiters. The only `$` characters found
  anywhere in nine papers were three currency amounts in the prose of the GPT-3
  paper, and even those came out as `paid $ 12`. The Transformer paper's central
  formula arrives as seven lines of debris:

  ```
  Attention(Q, K, V ) = softmax( 
  QK
  T
  √
  d
  k
  )V (1)
  ```

- **Word splitting varies by an order of magnitude, and it tracks the PDF's
  fonts, not the paper's age.** A 1995 paper came back clean; a 2005 one came
  back unreadable.

Its real value is convenience: one GET, no download, no `pdftotext`, no
temporary directory. Reach for it when arXiv's source is a PDF-only submission,
when LaTeXML HTML does not exist, or when you want the prose and the math does
not matter.

### Check the damage before quoting from it

The signature of a broken extraction is a lone capital letter, not `A` or `I`,
followed by a lowercase word — `D aniel`, `T he`, `A strophysical`. Ordinary
math variables do not produce that pattern; broken embedded fonts do.

```bash
curl -sS "https://www.alphaxiv.org/abs/$ID.md" > paper.md
python3 -c '
import re,sys; t=open("paper.md",encoding="utf-8",errors="replace").read()
n=len(re.findall(r"\b[B-HJ-Z] [a-z]{2,}",t)); w=len(t.split())
print(f"{1000*n/max(1,w):.1f} splits per 1000 tokens")'
```

Measured, and eyeballed to confirm the metric matches reality:

| Per 1000 tokens | Meaning | Papers measured |
|---|---|---|
| under 1 | clean; quote from it | `1706.03762` (0.2), `2005.14165` (0.4), `quant-ph/9508027` (0.5) |
| 1 – 10 | mostly fine, damage is localized; read the passage you want before quoting it | `1512.03385` (1.0), `1205.7018` (1.5), `gr-qc/9310026` (2.5), `hep-th/9711200` (5.9) |
| over 10 | unusable for quotation | `cond-mat/0009244` (28.3), `astro-ph/0501171` (65.0) |

The two worst cases are not subtle. `astro-ph/0501171` opens
`Subm itted to T he A strophysical Journal`, with the title rendered
`D ET EC T IO N O F T H E B A RY O N A C O U ST IC PEA K`.
`cond-mat/0009244` both splits and joins: `w here`, `com m ute`,
`m echanicalexpectation`, `w illbe crucialfor`. Above 10, drop to arXiv source
or the PDF; do not try to repair the text.

Note that `hep-th/9711200` scores 5.9 and yet reads perfectly in the body — its
damage is concentrated in the title page. That is exactly why the middle band
says *read the passage*, rather than trusting or discarding the whole file.

## quickarxiv.org, and its one bug

The redirect rewrites to `/overview/` using the **second** path segment,
whatever that segment happens to be. Every hop below was traced on 2026-08-26:

| Requested on quickarxiv.org | 302 to | then | Ends at |
|---|---|---|---|
| `/abs/1706.03762` | `/overview/1706.03762` | 308 | `/abs/1706.03762`, **200** ✓ |
| `/pdf/1706.03762` | `/overview/1706.03762` | 308 | `/abs/1706.03762`, **200** ✓ |
| `/1706.03762` | `/` | — | the homepage, **200** |
| `/abs/hep-th/9711200` | `/overview/hep-th` | 308 | `/abs/hep-th`, **404** |

The second hop is alphaXiv's own and not part of the bug: `/overview/<id>` 308s
to `/abs/<id>` for every identifier, old-style included, so the reading page
lives at `/abs/`.

The bug is quickarxiv's first hop. **The bare ID is the dangerous case** — the
identifier is dropped and the homepage answers 200, so nothing in the response
says the lookup missed. An old-style ID at least fails loudly, losing everything
after the archive name and ending in a 404.

Neither affects the two `.md` routes, which are not redirected at all:
`/overview/hep-th/9711200.md` and `/abs/hep-th/9711200.md` both answer 200
directly. Use alphaXiv URLs, and treat quickarxiv.org as a thing to type in a
browser rather than a thing to script.

## Politeness and terms

`robots.txt` is `Allow: /` for every agent, disallowing only `/?` and
`/signin?`, so the two `.md` routes are fair game. No `RateLimit-*` or
`Retry-After` header is sent, and eight sequential GETs of the same document all
returned 200 in 0.15–0.70 s. Responses are `cache-control: no-store`,
`cf-cache-status: DYNAMIC`, so each request costs them real work — keep it to
what the task needs.

## The MCP server, for completeness

alphaXiv documents a Model Context Protocol server at
<https://www.alphaxiv.org/docs/mcp>: endpoint `https://api.alphaxiv.org/mcp/v1`,
Streamable HTTP, OAuth 2.1 by default or `Authorization: Bearer <key>` with a key
made under Settings → API Keys. Nineteen tools, of which four matter here —
`discover_papers`, `get_paper_content` (the report by default, `fullText: true`
for the raw extraction), `answer_pdf_queries` (returns page-level XML built for
citation), and `read_files_from_github_repository`.

It is not wired into this skill, deliberately. It needs an account, and its
research tools "count against your assistant quota", where the two `.md` routes
need neither. Reach for it only if a user has already set it up and wants it
used; `answer_pdf_queries` is the one tool with no keyless equivalent here.
