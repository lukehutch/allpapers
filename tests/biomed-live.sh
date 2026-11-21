#!/bin/bash
# Live test of the biomedical sources: the bioRxiv probe and paperclip's UUID IDs in
# allpapers-locate, and the Europe PMC and PubMed backends of allpapers-search.
# Needs the network and paperclip. Each check is held to 60 s.
here=$(dirname "$0")/..
fail=0
ok() { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=$((fail + 1)); }

out=$(timeout 60 "$here/scripts/allpapers-locate" 10.1101/760983 2>/dev/null)
grep -q '/papers/fb37af04-6c0e-1014-9fac-9ce395c656a4' <<<"$out" \
  && ok "locate lists the paperclip copy of a bioRxiv paper" || bad "no paperclip row for 10.1101/760983"
grep -q 'xml *bioRxiv *https://www.biorxiv.org/content/early/2019/09/08/760983.source.xml' <<<"$out" \
  && ok "locate lists bioRxiv's JATS XML" || bad "no bioRxiv JATS row"
grep -q '10.7554/elife.51691' <<<"$out" \
  && ok "locate lists the published version" || bad "no published-version row"

json=$(timeout 60 "$here/scripts/allpapers-search" --no-paperclip -n 20 --json \
  --pubmed-query '"Pancreatic Neoplasms"[MeSH] AND "Metformin"[MeSH] AND Meta-Analysis[pt]' \
  --europepmc-query 'TITLE_ABS:(metformin AND "pancreatic cancer") AND SRC:PPR')
python3 - "$json" <<'PY' || fail=$((fail + 1))
import json, sys
d = json.loads(sys.argv[1])
t, rows = d["totals"], d["results"]
checks = [
    ("PubMed MeSH + [pt] query finds at least 10 records", t.get("pubmed", 0) >= 10),
    ("Europe PMC SRC:PPR finds preprints", t.get("europepmc", 0) >= 1),
    ("every Europe PMC row is a preprint",
     all(r["source"].startswith("PPR") for r in rows if r["found_by"] == ["europepmc"])),
    ("every row has an identifier", all(r["id"] for r in rows)),
    ("no backend failed", not d["notes"]),
]
for label, good in checks:
    print(("ok   " if good else "FAIL ") + label)
sys.exit(sum(not g for _, g in checks))
PY
echo "failed: $fail"
exit $((fail > 0))
