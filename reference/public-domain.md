# Public-domain archives

Old papers — anything published before the open-access era and never re-issued —
are often missing from every index on rungs 1–3 of `ladder.md`, but many of them
exist as legal scans of the original printed volumes. They sit on rung 5, with web
search, and come before shadow libraries (rung 6). They are legal sources, so a quote
taken from one may be used in the paper like any other source; the shadow-library
rules do not apply.

**Which works qualify.** In the United States a work published before 1931 is in the
public domain as of 2026; the cutoff moves forward by one year every 1 January
(95 years from publication). Elsewhere the term usually runs to 70 years after the
author's death, so a scan can be public domain in the US and not in Europe. The
archive decides what it shows; do not try to get around a "lending only" or
"search only" restriction.

Everything below was measured on 2026-10-04 with the Chrome User-Agent from
`SKILL.md`.

---

## The OCR rules

Most of these archives give you two things for each page: a scanned **image** and
an **OCR text layer** generated from it. The text layer is what you search, but it
is not the text of the paper. OCR of old type is frequently wrong. The Google scan
`annalenderphysi01unkngoog` reads, on its first page, "prcscrvod for gcncrations
on library shclvcs" for "preserved for generations on library shelves", and that
is clean modern type. Fraktur, the long s (ſ), ligatures, diacritics, sub- and
superscripts and mathematical symbols do worse.

1. **Use the OCR layer to find the passage, never as the quotation.** Check every
   quote taken from an OCR layer against the rendered page image, character by
   character, including punctuation, accents and symbols. Correct the quote to
   what the image shows.
2. **Mark restorations in brackets.** If you supply a character the image does not
   show (a torn corner, text lost in the binding), put it in square brackets in
   the quote: `the velocity of l[i]ght`. A character you correct from a wrong OCR
   reading is not a restoration; just write what the image shows.
3. **If the scan leaves a character in doubt, do not quote.** When a mark on the
   scan (a stain, show-through from the other side, broken type, a smudge) leaves
   a character or punctuation sign uncertain, paraphrase that sentence in the
   paper instead of quoting it, and record the uncertainty in
   `verification/bib.md`: which characters, the two or more possible readings, the
   page, and the image URL.
4. **Record the check.** The `verification/bib.md` entry names the archive item,
   the URL of the page image the quote was checked against, the printed page
   number as read from the image, and the words "checked against page image".
   OCR-derived page numbers are guesses (see archive.org below); read the number
   off the image.

Wikisource pages at the highest proofreading level are the one exception to rule 1;
see below.

---

## archive.org

Fully scriptable, no key. It holds Google Books scans of 19th-century journal
volumes and the `sim_` ("Serials in Microfilm") runs of journals into the 20th
century; searching `Annalen der Physik` for 1905 returns
`sim_annalen-der-physik_1905_16_1` and its siblings.

```bash
# search
curl -s 'https://archive.org/advancedsearch.php?q=title%3A%28Annalen+der+Physik%29+AND+year%3A1905&fl%5B%5D=identifier&fl%5B%5D=title&rows=50&output=json'
# list an item's files
curl -s 'https://archive.org/metadata/<id>/files'
# the OCR text layer of the whole item
curl -sL 'https://archive.org/download/<id>/<id>_djvu.txt'
# one page image, by leaf number (0-based scan index, not the printed page)
curl -sL -o page.jpg 'https://archive.org/download/<id>/page/n<leaf>.jpg'
```

Other useful files in the listing: `<id>_hocr.html` (OCR with the position of every
word on the page, which tells you which leaf a passage is on) and
`<id>_page_numbers.json`, which maps each `leafNum` to a `pageNumber`. That mapping
is itself an OCR guess with a confidence score — in the `sim_annalen` item above,
leaf 40 is page "29" at confidence 71 — so confirm the number on the image.

Measured: both items above have `access-restricted-item` unset and serve their
`_djvu.txt` (HTTP 200, 1.38 MB for the Google scan); page images arrive as full
scans (2648×4492 pixels). If `access-restricted-item` is `true`, the item is
lending-only: the text layer and images are not available, and that is the end of
this route.

## Wikisource (de, en, fr)

Volunteer transcriptions, each page tied to the scan it was typed from. The German
Wikisource is especially strong for 19th- and early 20th-century physics and
mathematics.

```bash
# search the transcribed pages (namespace 102 on de, 104 on en and fr)
curl -s 'https://de.wikisource.org/w/api.php?action=query&list=search&srsearch=Zur%20Elektrodynamik%20bewegter%20K%C3%B6rper&srnamespace=102&format=json'
# the article's wikitext; on de the {{Textdaten}} header gives the original citation
curl -s 'https://de.wikisource.org/w/index.php?title=Zur_Elektrodynamik_bewegter_K%C3%B6rper&action=raw'
# proofreading level of one transcribed page
curl -s 'https://de.wikisource.org/w/api.php?action=query&titles=Seite:Einstein-Elektrodynamik.djvu/1&prop=proofread&format=json'
```

The page namespace is `Seite:` on de and `Page:` on en and fr. Each transcribed page
carries a proofreading `quality` from 0 to 4. **Quality 4** ("Fertig" on de,
"Validated" on en, "Validée" on fr) means two different people have checked it
against the scan; the measured page `Seite:Einstein-Elektrodynamik.djvu/1` is at 4.
A quality-4 page may be quoted without your own character check, though a spot
check of the quoted sentence against the scan is still cheap. Treat quality 3
("proofread", one person) and below like an OCR layer: apply the OCR rules above.

## Gallica (Bibliothèque nationale de France)

Strong for French journals, including the *Comptes rendus* of the Académie des
sciences. Partly scriptable:

- **Search** (`https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=dc.title%20all%20%22comptes%20rendus%22`)
  works, but measured, it answered once and then returned
  `Access Denied: 403 Access Interdit` for about two minutes. Space requests out.
- **The text layer** (`https://gallica.bnf.fr/ark:/12148/<ark>.texteBrut`, or
  `/<ark>/f<page>.texteBrut` for one page) sits behind an ALTCHA "Vérification de
  sécurité" page that answers HTTP 200. Browser only, human in the loop.
- **Page images** come through by IIIF:
  `https://gallica.bnf.fr/iiif/ark:/12148/<ark>/f<page>/full/full/0/native.jpg`
  returned a 2592×3508 scan at 300 dpi. These are enough for the image check
  even when the text has to be read in a browser.

## Official journal back archives

Many societies and publishers have scanned their own back runs. These are the
authority for the printed text, so prefer them to a third-party scan when you can
reach them.

| Archive | Covers | Measured |
|---|---|---|
| `journaldephysique.org` | *Journal de Physique* and its predecessors | DataDome captcha — browser only |
| `numdam.org` | French mathematics journals | 200, browsable |
| `eudml.org` | European mathematics journals, links to the hosting archive | 200, browsable |
| HathiTrust | US research-library scans | catalog API works (`catalog.hathitrust.org/api/volumes/brief/oclc/<n>.json`); full-view pages behind a Cloudflare challenge — browser only |
| Biodiversity Heritage Library | natural history | Cloudflare challenge — browser only |

`zbMATH Open` (`api.zbmath.org`) is not an archive, but its API returns
mathematics records back to the 19th century with links to the digitized copy,
which is often the quickest way to find one.
