# Unpaywall

Answers one question well: **is there a legal free copy of this DOI, and where?**
It is built on Crossref, tracking roughly 120M DOI records ("Search all 120M of
our articles" — Unpaywall's own site bundle, read 2026-08-25). It does not host
anything; it points at publisher pages and repository deposits.

Run by OurResearch, who also run OpenAlex — and as of the "Walden rewrite" the two
are literally the same data. OpenAlex's own documentation puts it plainly:
"Unpaywall is not a separate database. Since the Walden rewrite, Unpaywall records
are served from the same OpenAlex data that powers everything else — Unpaywall is a
legacy-compatible *format* over that data, kept stable for the large ecosystem built
on it." Their advice for new code is to call OpenAlex directly and use the Unpaywall
format only when talking to tools that already speak it. There is no deprecation
notice, and the endpoint answered normally on 2026-08-25.

Practical consequence: **Unpaywall covers Crossref DOIs only.** DataCite DOIs are
excluded, on the reasoning that nearly all DataCite-registered works are open
anyway. So an arXiv paper looked up by its `10.48550/arXiv.…` DOI returns nothing
here — that is by design, not a miss. Go to arXiv directly for those.

## The API

```
GET https://api.unpaywall.org/v2/{doi}?email=you@example.org
GET https://api.oadoi.org/v2/{doi}?email=you@example.org     # alias, same data
```

The `email` parameter is **required** — without it the API returns HTTP 422
(confirmed 2026-08-25). It is a contact address for abuse handling, not
authentication; there is no key and no signup. `allpapers-setup` stores it.

The `api.oadoi.org` host is the one the official browser extension calls
(`extension/unpaywall.js`), and it returns 200 for the same requests.

### Confirmed defect

`GET /v2/search?query=...&email=...` returns **HTTP 500** on every variation
tried, with and without `is_oa`, on both hosts (rechecked 2026-08-25). Unpaywall
is a DOI-lookup service in practice. To search by title, resolve the title to a
DOI first — OpenAlex is better at that — and then look the DOI up here.

## Response

Top level:

```
doi, doi_url, title, genre, published_date, year, publisher,
journal_name, journal_issns, journal_issn_l, journal_is_oa, journal_is_in_doaj,
is_oa, oa_status, has_repository_copy, is_paratext,
best_oa_location, first_oa_location, oa_locations, oa_locations_embargoed,
z_authors, data_standard, updated
```

Each entry in `oa_locations`:

```
url, url_for_pdf, url_for_landing_page,
host_type, version, license, evidence, is_best,
oa_date, updated, endpoint_id, pmh_id, repository_institution
```

The two fields that decide what you do next:

- **`host_type`** — `publisher` or `repository`.
- **`version`** — `publishedVersion`, `acceptedVersion` or `submittedVersion`.
  Only `publishedVersion` is the paper of record. An `acceptedVersion` is
  post-peer-review but pre-typesetting, so page and line numbers will not match
  the journal; a `submittedVersion` is a preprint and may differ in substance.
  **Say which version you read** when a claim depends on the exact wording.

`oa_status` is `gold`, `hybrid`, `bronze`, `green` or `closed`. `bronze` means
free to read on the publisher's site with no open licence, so it can disappear.

Take `url_for_pdf` when present, `url_for_landing_page` otherwise — but remember
the format rule: a repository landing page sometimes offers XML or HTML that
parses better than the PDF beside it.

### How the extension decides its badge colour

From `extension/unpaywall.js` in the official extension: `host_type == "repository"`
→ green; otherwise `journal_is_in_doaj` → gold; otherwise bronze. Useful as a
compact summary of where a copy actually lives.

## Finding a DOI on a page

The extension's own detection order, worth reusing when scraping a publisher page
for an identifier. Meta tag names checked, in order:

```
citation_doi, doi, dc.doi, dc.identifier, dc.identifier.doi,
bepress_citation_doi, rft_id, dcsext.wt_doi
```

Then `*[data-doi]` attributes, but only when exactly one distinct DOI appears on
the page; then links matching `https?://doi.org/(10\.\d+/.*)`; and a
ScienceDirect-specific `SDM.doi = '...'` pattern.

## Rate limits

Unpaywall's own API page, under a "Rate limits" heading, says only: "Please limit
use to 100,000 calls per day. If you need faster access, you'll be better served by
downloading the entire database snapshot for local access." That is a request, not
a documented enforcement threshold — nothing in their published text describes what
happens if you exceed it, and this skill has not tested it. Bulk work should use the
snapshot.

Unlike OpenAlex, the Unpaywall endpoint is not metered: the response carries no
rate-limit headers at all (checked 2026-08-25), and it stays free with no key.
