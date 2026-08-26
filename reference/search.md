# Searching, as opposed to looking one paper up

`allpapers-locate` answers "where can I read *this* paper". This file is the
other half: finding papers you cannot yet name. Everything below was measured
against paperclip 0.7.38 on 2026-08-25.

Three kinds of lookup, and they need different tools:

| You have | Use | Result |
|---|---|---|
| A DOI, arXiv ID, PMID, PMCID | `allpapers-locate` / `allpapers-fetch` | exactly one paper |
| Words that appear in the paper | `allpapers-search --mode keyword` | many candidates |
| A description of the idea | `allpapers-search --mode semantic` | many candidates |

A search returns candidates, not citations. Nothing found this way goes into
`verification/bib.md` until it has been staged, read and judged — see
`reference/verification.md`.

## The two defaults that quietly lose results

**paperclip returns 20 results unless you ask for more.** Its own `--help` says
`-n/--limit N   Max results (default: 100)`. Measured on 0.7.38, a bare
`search -s pmc "CRISPR base editing delivery"` returned exactly **20** numbered
results; the same query with `-n 250` returned exactly **250**. Nothing in the
output says the other 230 existed. Always pass `-n`. `allpapers-search` defaults
it to 250.

**The default ranking is hybrid, which is not always what you want.** A hybrid
run blends lexical and vector retrieval, which is a good default and a poor
specialist. If you need every paper containing a specific gene name, hybrid will
dilute the lexical hits with semantic near-misses; if you are looking for an idea
by description, hybrid will drag in papers that merely share vocabulary.

## The four rankings

`--ranking` in paperclip, `--mode` in `allpapers-search`:

| Ranking | `--mode` | What it matches | Use it for |
|---|---|---|---|
| `bm25` | `keyword` | literal terms, TF-IDF weighted | gene names, method names, exact strings, boolean queries |
| `vector` | `semantic` | embedding cosine similarity | a described idea, a paraphrase, "papers like this abstract" |
| `hybrid` | `hybrid` | both, blended — **the default** | a first pass when you do not know which fits |
| `analogical` | `analogical` | the same structural method in another field | finding transferable methods; the useful hit is usually in a community you would not have searched |

`--mode all` runs all four and merges them, ranking a paper by how many rankings
found it. That consensus ordering is the single most useful thing here: a paper
that surfaces under both lexical and vector retrieval is almost always more
relevant than one that tops either alone. Measured on
`--mode all -n 8 -s pmc "CRISPR base editing delivery"`: 20 distinct papers, 9 of
them found by more than one ranker, and the multi-ranker group was visibly more
on-topic than the singletons.

**Query wording matters more than any flag**, because the embedding model is
fine-tuned on abstracts:

1. Best — paste a whole abstract verbatim.
2. Next — one or two sentences describing the *method or problem structure*:
   "correcting for systematic under-reporting when the missingness mechanism is
   unknown", not "CRISPR delivery".
3. Worst — bare keywords. These are what `bm25` wants, and they are the weakest
   possible input to `vector` and `analogical`.

So the mode should follow the query you actually have, not the other way round.

## Sort order

`--sort relevance` (default) or `--sort date` (newest first). Three things about
`date` change how you read the top of the list.

**The head of a date-sorted list depends on the query, so it is not an index
frontier.** Measured 2026-08-25, top hit of `-n 250 --sort date`:

| Query | PMC | bioRxiv | arXiv |
|---|---|---|---|
| `cell` | 2026-05-01 | 2026-04-01 | 2026-07-15 |
| `protein` | 2026-04-01 | 2026-04-01 | 2026-07-15 |
| `neural network` | 2026-04-01 | 2026-04-01 | 2026-07-15 |

Roughly one to four months behind the day it was run, varying by query and
backend. Do not read a given head date as "the corpus stops here" — a different
query surfaces something newer. What it does mean is that **a "latest work"
sweep run only here can miss the last few months**, so pair it with a web or
Gemini search, which see the live literature.

**arXiv results print a year only.** The display reads `arx_2607.11914 · arXiv ·
2026` while the document's own `meta.json` carries `"pub_date": "2026-07-15"`.
The sort key is finer than the display, so do not conclude from the printed
`2026` that the ordering inside a year is arbitrary — read `meta.json` when the
exact date matters.

**Vector score floors are refused with `--sort date`.**
`--min-embedding-similarity` is not valid alongside it; `--min-bm25-score` is.

The previously recorded defect that some records carry **future** publication
dates did **not** reproduce on 0.7.38 across six date-sorted sweeps: every head
was in the past. Sanity-check the head anyway; the check is free.

## Narrowing filters (0.7.38)

Cheaper than a second search, because they run server-side:

```bash
--bool                  # boolean expression; REQUIRES --ranking bm25
--full-text             # match phrases against body text, not just title
--has-full-text         # only papers with indexed body content
--has-section NAME      # e.g. Methods
--without-section NAME
--has-block-type TYPE   --without-block-type TYPE
--exclude-article-type TYPE   --exclude-source SOURCE
--exclude-journal NAME        --exclude-year YEAR
--year / --year-min / --year-max / --since 30d|6m|1y
--journal NAME          --category CAT        # PMC / bioRxiv respectively
-m any|all|50%|75%      # how many query terms must match
```

`--bool` without `--ranking bm25` is refused outright:
`search --bool: requires explicit --ranking bm25`. Verified working:
`--bool --ranking bm25 '"CRISPR" AND NOT "review"'`.

Score floors: `--min-bm25-score` and `--min-embedding-similarity`. **Each bounds
only its own retrieval leg**, so under hybrid, setting one leaves the other
unfiltered — pass both, or pair one with the matching `--ranking`. Neither is
valid with `-r` or `--ranking analogical`, and the similarity floor is also
rejected alongside `--sort date`. `allpapers-search` applies each floor only to
the rankings it is valid for, so `--mode all --min-bm25 70` does not fail the
vector leg.

## Result sets are stateful — this is the big lever

Every search prints `s_xxxxxxxx` and the set lives server-side. `--from` re-runs
the next command against exactly that set:

```bash
paperclip search -s pmc -n 250 "prime editing delivery"        # -> s_1a2b3c4d
paperclip grep -i "lipid nanoparticle" --from s_1a2b3c4d       # narrow
paperclip grep -i "in vivo" --from s_1a2b3c4d                  # narrow differently
paperclip filter --from s_1a2b3c4d "in vivo delivery in mice"  # LLM filter, in place
paperclip map --from s_1a2b3c4d "which delivery vehicle, which organ, what efficiency"
paperclip reduce --from <map_id> --strategy table --columns vehicle,organ,efficiency
```

Narrowing inside a held set beats re-querying: a grep into one section costs
roughly 200 tokens against about 40k to load a whole paper. Keep a `map` set to
3–10 papers and ask for enumerated fields, never "summarize".

Note `filter` **overwrites the set in place**; `grep --from` saves a new one. If
you may want the wide set back, grep rather than filter.

## Searching the live web alongside the corpus

paperclip cannot see anything published in the last few months, nor anything
outside PMC/arXiv/bioRxiv/medRxiv. Two channels cover that gap, and
`allpapers-search` can run one of them in the same command:

```bash
scripts/allpapers-search --mode all --gemini "your query"   # corpus + grounded web
scripts/allpapers-search --gemini-only "your query"         # web only
```

`--gemini` uses Gemini with Google Search grounding: it runs real search queries
and returns an answer annotated with the URLs it used. See `reference/gemini.md`
for the API, the key, and what is verified versus unverified there. A plain
`WebSearch` remains worth running in parallel — the two disagree often enough to
be worth both, and Gemini's answer is a synthesis while a web search is a list.

## Reading `allpapers-search` output

```
scripts/allpapers-search --mode all -n 250 -s pmc "CRISPR base editing delivery"
```

Rows are sorted by how many rankings found the paper, then by best rank within
any of them, and each row names the rankings that found it. `--json` gives the
same with `found_by`, `best_rank`, the paperclip document ID, the DOI or URL and
the abstract snippet, so the next step is usually to pipe an ID straight into
`allpapers-fetch <id> --stage`.
