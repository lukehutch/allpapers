#!/usr/bin/env python3
"""Offline test: allpapers-search and allpapers-locate read the identifiers out of
saved paperclip output (tests/fixtures/paperclip-*.txt, captured 2026-11-20), and
allpapers-search matches one paper across paperclip, Europe PMC and PubMed."""
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"


def load(name):
    spec = importlib.util.spec_from_loader(
        name.replace("-", "_"),
        importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(ROOT / "scripts" / name)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = load("allpapers-search")
L = load("allpapers-locate")
failed = 0


def check(label, got, want):
    global failed
    ok = got == want
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {label}: got {got!r}" + ("" if ok else f", want {want!r}"))


hits, setid = S.parse_search_output((FIX / "paperclip-search-abstracts.txt").read_text(), "hybrid")
check("abstracts set id", setid, "s_c947324a")
check("abstracts ids", [h["id"] for h in hits], ["88060771", "PMC4788143", "61898723"])
check("abstracts sources", [h["source"] for h in hits], ["pubmed", "PMC", "pubmed"])
check("abstracts dates", [h["date"] for h in hits], ["2012", "2016-03-11", "2016"])
check("abstracts authors of a PubMed record", hits[0]["authors"], "")
check("abstracts authors of a PMC record", hits[1]["authors"],
      "Chenwi M. Ambe; Amit Mahipal; Jimmy Fulp; Lu Chen; Mokenge P. Malafa")

hits, _ = S.parse_search_output((FIX / "paperclip-search-biorxiv.txt").read_text(), "hybrid")
check("biorxiv ids", [h["id"] for h in hits], ["bio_18dbbf8171e1", "bio_1d2304a17b12"])
check("biorxiv dates", [h["date"] for h in hits], ["2025-09-15", "2026-10-16"])

hits, _ = S.parse_search_output((FIX / "paperclip-lookup-biorxiv.txt").read_text(), "hybrid")
check("lookup uuid id", [h["id"] for h in hits], ["fb37af04-6c0e-1014-9fac-9ce395c656a4"])

check("locate ids in lookup output",
      L.paperclip_ids((FIX / "paperclip-lookup-biorxiv.txt").read_text()),
      ["fb37af04-6c0e-1014-9fac-9ce395c656a4"])
check("locate ids in search output",
      L.paperclip_ids((FIX / "paperclip-search-abstracts.txt").read_text()),
      ["88060771", "PMC4788143", "61898723"])

# Two 2016 papers as each backend reports them (PMIDs checked 2026-11-20).
pc_pmc = {"id": "PMC4788143", "title": "Effect of Metformin Use on Survival in Resectable "
          "Pancreatic Cancer", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4788143/"}
pc_pubmed = {"id": "61898723", "title": "Impact of Metformin on Advanced Pancreatic Cancer "
             "Survival: Too Little, Too Late?",
             "url": "https://doi.org/10.1158/1078-0432.ccr-15-2494"}
epmc = {"id": "PMID:26967162", "title": "x", "doi": "", "pmid": "26967162", "pmcid": "PMC4788143"}
pubmed = {"id": "PMID:26637275", "title": "Impact of metformin on advanced pancreatic cancer "
          "survival: too little, too late?", "doi": "10.1158/1078-0432.CCR-15-2494".lower(),
          "pmid": "26637275", "pmcid": ""}
check("merge: paperclip PMC id meets Europe PMC pmcid",
      bool(set(S.merge_keys(pc_pmc)) & set(S.merge_keys(epmc))), True)
check("merge: paperclip DOI url meets PubMed doi",
      bool(set(S.merge_keys(pc_pubmed)) & set(S.merge_keys(pubmed))), True)
check("merge: paperclip numeric id is not taken for a PMID",
      any(k.startswith("pmid:") for k in S.merge_keys(pc_pubmed)), False)
check("merge: different papers stay apart",
      bool(set(S.merge_keys(pc_pmc)) & set(S.merge_keys(pubmed))), False)

print("FAILED" if failed else "all passed", f"({failed} failing)")
sys.exit(1 if failed else 0)
