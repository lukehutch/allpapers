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

**Not verified**: the response parsing. Nothing on this machine has a Gemini API
key, so no successful call has been made and the code that walks the response has
never seen a real one. It is written to the shapes given in the Google docs and
the `Search_Grounding` cookbook notebook. If it misparses, that is the first place
to look — `--json` prints whatever came back.

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
