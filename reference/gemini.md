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

**Verified live on 2026-08-26**, once a key was available. A real grounded call
through `allpapers-search --gemini-only` returned, and the parsing is correct: the
answer text, the `search_queries` Gemini actually issued, and the citation list all
came out intact. The `interactions` endpoint answered; the `generateContent`
fallback was exercised separately. Three things measured that the docs do not spell
out:

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
  and DOI, confirmed afterwards by `allpapers-locate`, but that confirmation step
  is the point: the output prints an `allpapers-locate` command per identifier for
  exactly this reason.

## Getting a key

Free and instant at <https://aistudio.google.com/apikey>. Then:

```bash
scripts/allpapers-setup --set gemini_api_key=...
```

or set `GEMINI_API_KEY` in the environment. Without one, `--gemini` reports the
403 and the paperclip half of the search still runs.

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
