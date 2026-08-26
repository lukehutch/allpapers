# Gemini grounded search

A second discovery channel that sees the live web: Gemini runs real Google Search
queries and returns an answer annotated with the URLs it used. It covers the two
places paperclip cannot reach — anything published in the last few months, and
anything outside PMC/arXiv/bioRxiv/medRxiv.

Run it through `allpapers-search`:

```bash
scripts/allpapers-search --mode all --gemini "your query"   # corpus + web
scripts/allpapers-search --gemini-only "your query"         # web only
```

Two backends reach it. `--gemini-backend auto` (the default) takes the API when
`gemini_api_key` is set and otherwise shells out to `agy`; `api` and `agy` force
one. **The API key bills a Google Cloud account** — Antigravity and Gemini
subscription credits do not cover it — so a user who has signed into `agy`
already has grounded Google search at no extra cost. See *The agy backend* below.

## Honest status of this integration

**Verified**: the endpoint, that it requires a key, and that both documented
request shapes pass server-side validation. Probed live on 2026-08-25 with no key:

| Request | Result |
|---|---|
| `POST /v1beta/interactions` with `{model, input, tools:[{type:"google_search"}]}` | **HTTP 403** `PERMISSION_DENIED` — "Method doesn't allow unregistered callers" |
| `POST /v1beta/models/<model>:generateContent` with `{contents, tools:[{google_search:{}}]}` | **HTTP 403**, same message |
| `POST /v1beta/models/<model>:generateContent` with the *interactions* body | HTTP 400 — `Unknown name "input"`, `Unknown name "type" at 'tools[0]'` |

The 403s matter: the request got past payload validation and died at
authentication, so the paths and the field names are right. The 400 shows the two
APIs take genuinely different shapes and must not be mixed.

**Verified live on 2026-08-26**, once a key was available — *both* endpoints, each
parser run against its own real response:

| Endpoint | Measured |
|---|---|
| `interactions` | HTTP 200. `_parse_interactions` recovered the answer text, the `search_queries` Gemini issued and 4 citations |
| `generateContent` | HTTP 200. `_parse_generate_content` recovered 8 citations from `groundingChunks[].web` and 3 `webSearchQueries` |

Four things measured that the docs do not spell out:

- **Grounding is the model's choice, and an ungrounded answer looks identical.**
  Asked "which paper introduced the Transformer architecture", `generateContent`
  returned HTTP 200 with a correct, well-formatted answer and **no
  `groundingMetadata` key at all** — no queries, no citations, no error, nothing
  to distinguish it from a search that found nothing. The model answered from its
  own weights. The same question phrased for recent work produced eight grounded
  citations. So **empty citations mean "ungrounded", not "nothing found"**, and
  `allpapers-search` now says so in the output rather than printing a bare answer.
- **Citation URLs are opaque Vertex redirects**, not source URLs. They arrive as
  `https://vertexaisearch.cloud.google.com/grounding-api-redirect/<token>`. They do
  resolve — one was followed to HTTP 200 at `https://arxiv.org/abs/1706.03762` —
  but the token says nothing about the destination, so the URL cannot be read or
  deduplicated without following it. The API supplies the display domain
  (`arxiv.org`, `nips.cc`) as a separate field, which is what the output shows.
  **Never record the redirect as a source URL in `verification/bib.md`** — follow
  it and record where it lands.
- **Model overload is a routine transient failure.** One run failed with HTTP 500
  on `interactions` and HTTP 503 on `generateContent` — "currently experiencing
  high demand" — and the identical query succeeded on the next attempt. Both
  endpoints are tried before giving up, and both errors are reported. Retry rather
  than concluding the integration is broken; `GEMINI_MODEL` overrides the model if
  one stays saturated.
- **Grounded answers are still leads.** The measured run named a correct arXiv ID
  and DOI, confirmed afterward by `allpapers-locate`, but that confirmation step
  is the point: the output prints an `allpapers-locate` command per identifier for
  exactly this reason.

## The agy backend

`agy` is the Google Antigravity CLI. It is backed by Google Search, so it answers
the same kind of grounded question, using the user's existing Antigravity login
rather than a billed API key. `allpapers-search` calls it as

```bash
agy -p "<the same grounded-search prompt> <query>" --model gemini-3.7-flash-high
```

`gemini-3.7-flash-high` was the newest Flash tier `agy models` listed on
2026-08-26; `ALLPAPERS_AGY_MODEL` overrides it. High rather than medium or low
because a literature sweep is worth more reasoning than a chat reply.

**It hangs if you run it plainly from a script.** `agy` asks gnome-keyring for its
stored credentials; the unlock dialog takes the terminal and the run blocks
forever with no output at all. Presenting the shell as a remote SSH session with
no display makes it fall back to its own token store:

```bash
export DISPLAY=""
export SSH_CLIENT="127.0.0.1 12345 22"
export SSH_TTY="/dev/pts/0"
agy -p "your prompt" --model gemini-3.7-flash-high
```

`allpapers-search` sets all three in the child environment, so
`--gemini-backend agy` needs nothing from you. **Apply the same three exports to
any other `agy` call you make from a script.**

The tradeoff: `agy` returns prose, not structured grounding metadata. There is no
`webSearchQueries` list and no citation array — the URLs are parsed back out of
the markdown (titled `[text](url)` links first, then bare URLs), so `searched:`
is always empty on this backend and a source the model mentions without linking
is lost. When the structured citation list matters, use the API.

## Getting a key

Only needed for the `api` backend. Free and instant at
<https://aistudio.google.com/apikey>. Then:

```bash
scripts/allpapers-setup --set gemini_api_key=...
```

or set `GEMINI_API_KEY` in the environment. Without one, `--gemini` falls back to
`agy` if it is installed; if it is not, it reports the 403 and the paperclip half
of the search still runs.

Google's free tier is rate-limited per model and per day; grounded search
requests are billed as search-tool use on paid tiers. Check current limits at
<https://ai.google.dev/gemini-api/docs/rate-limits> before running a sweep.

## The request

```
POST https://generativelanguage.googleapis.com/v1beta/interactions
x-goog-api-key: <key>
Content-Type: application/json

{"model": "gemini-3.7-flash",
 "input": "Find peer-reviewed papers about <query>. For each, give title, authors, year, venue and DOI or URL.",
 "tools": [{"type": "google_search"}]}
```

The model is overridable with `GEMINI_MODEL`. Use a current model ID — Google
retires them, and a retired ID fails with 404 rather than falling back.

## The response

`steps[]`, each carrying either a search call or model output:

- `{"type": "google_search_call", "arguments": {"queries": [...]}}` — the queries
  Gemini actually issued. Worth printing: they often reveal a better phrasing of
  your own question than the one you supplied.
- `{"type": "model_output", "content": [{"text": ..., "annotations": [...]}]}` —
  the answer, with `annotations[]` entries of `type: "url_citation"` carrying the
  cited `url` and `title`.

`allpapers-search` collects the queries, the answer text and the citation URLs,
and prints citations as a numbered list beside the paperclip results.

## What it is good for, and what it is not

Good for: recent work, non-indexed venues, grey literature, "has anyone done X",
and finding the *name* of a thing so you can then search the corpus properly.

Not good for: identity. A grounded answer is a synthesis with citations attached,
and the citation may support the sentence loosely or not at all. **Never quote a
paper from Gemini's summary.** Take the URL or DOI it gives you, feed that to
`allpapers-locate`/`allpapers-fetch`, and quote the fetched text. This is the same
rule that applies to Google Scholar, for the same reason.

Also worth running a plain `WebSearch` in parallel. The two disagree often enough
to justify both: one returns a ranked list you scan yourself, the other returns a
claim you have to check.
