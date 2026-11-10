# Fourth source: spacing investigation

Baseline: `a02fb0cc0de0b3e977feee36800cfeccc0d0e8dd`, Booksmith 0.2.0. Private original: *Tempo do Desprezo*, 227 PDF pages. The original PDF, intermediate model, complete report, manifest and actual EPUB were available. Original PDF SHA-256 is retained in the private evidence. Narrative, PDFs and bundles are not committed.

## Root cause and decision

Systematic defect in extraction, specifically line reconstruction, before block joining or EPUB serialization. `extract.py` discarded every whitespace glyph, then reconstructed spaces solely for gaps >max(1.5pt, .18 × row font size). An explicitly encoded space can be narrower under overlapping glyph metrics/positioning. Its presence was lost even though both parsers decoded the separator.

Page 2 uses separate text-showing operators and a ToUnicode mapping `<0003> <0020>` for explicit spaces. At the first affected boundary, the right glyph starts at 38.506012pt and the previous glyph ends at 35.834823pt: gap 2.671189pt, below the 2.7pt threshold for 15pt text. The literal space has x0=34.754342pt, x1=38.506012pt. Other confirmed sample gaps are 2.581149pt. An advance inferred only from nonspace glyph bounding boxes does not replace explicit text evidence.

PDF rendering and the pypdf/pdfplumber extractions show the separators. The old source-line ledger, block text and actual XHTML all contain the fusions. The actual XHTML exactly matches the bad model, explaining why serialization/accounting previously passed. PDF pages 2 and 42 were visually inspected; this is targeted source review, not visual certification of every page.

Preserve literal whitespace between adjacent glyphs using the existing row geometry; collapse consecutive separators to one space. Keep the geometric fallback threshold unchanged. Log every newly recovered below-threshold separator with source line, output offset, gap, threshold and PDF whitespace boxes. No dictionary, title, page, phrase or author-specific runtime rule was added. No global threshold reduction or lexical repair is justified.

## What “220 occurrences” actually meant

The old `word_spacing` emitted one finding per page, only where nonspace characters agreed with pypdf. It did not count individual boundaries. All 220 flagged pages were expanded and classified:

| Original page-finding category | Pages |
| --- | ---: |
| Confirmed lost literal separators, no additional punctuation difference | 203 |
| Confirmed losses plus punctuation-only differences | 16 |
| Only punctuation difference, no confirmed fusion (page 107) | 1 |
| Total | 220 |

Those pages contain **1,859 confirmed lost separators on 219 pages** and **22 punctuation-only differences on 17 pages**. The latter are immediately before commas/periods, have no explicit whitespace and have gaps from -0.7503pt to 0.3301pt; 21 coincide with a font transition. They are not word fusions. No space was inserted for them.

Page 227 was outside those 220 findings: pypdf and geometric extraction disagree about the reading order of promotional headings, preventing global character alignment. Its old line `p227-l4` also lost a literal space (`Aespada` → `A espada`), independently confirmed by the local pypdf line and original glyphs. The correction restores that separator too. Consequently, **1,860 literal separators are recovered on 220 pages**. Whole-page spacing certification for page 227 remains inconclusive; do not manufacture aligned boundary counts for it.

## Distribution

Page numbers are PDF physical pages, one-based. Regions were assigned during source inspection, never used by the motor. [Complete numeric page ledger](spacing-pages.csv).

| Region | Pages | Automated confirmed losses | Literal spaces recovered | Pages with recovery |
| --- | --- | ---: | ---: | ---: |
| Front matter | 1–5 | 10 | 10 | 1 |
| Chapters, including epigraphs | 6–225 | 1,847 | 1,847 | 217 |
| Copyright/promotional material | 226–227 | 2 | 3 | 2 |
| Total | 227 | 1,859 | 1,860 | 220 |

The issue is distributed through the narrative, not concentrated in special pages. Chapter-region pages 64, 107 and 138 have no confirmed loss. Pages 42, 129, 167 and 204 each have 18 automated confirmed losses. Punctuation differences occur on pages 2, 6, 25, 45, 48, 95, 107, 115, 116, 117, 119, 139, 145, 146, 185, 196 and 226.

## Traceable examples

IDs refer to the original source ledger and remain stable after reconversion. PDF/extractor expected text was checked against the actual old/new XHTML, not just the model. Multiple defects can share a source line.

| PDF page | Source line | Block | PDF / pypdf / corrected EPUB | Old extraction / old EPUB |
| --- | --- | --- | --- | --- |
| 2 | p2-l3 | b4 | A presente obra | Apresente obra |
| 2 | p2-l4 | b5 | em pesquisas | empesquisas |
| 2 | p2-l4 | b5 | bem como | bemcomo |
| 2 | p2-l11 | b12 | em nosso | emnosso |
| 42 | p42-l2 | b580 | Circulam rumores | Circulamrumores |
| 227 | p227-l4 | b3447 | A espada | Aespada |

Page 2 line boxes: p2-l3 [25,143.49,558.487,158.49], p2-l4 [25,161.49,586.25,176.49], p2-l11 [25,334.74,562.239,349.74]. Page 42 p42-l2: [47.51,34.74,530.725,49.74]. Full private JSON retains page, line, block, box, normalized-character offset, produced text and expected/candidate examples for each classified boundary. Offsets count normalized nonspace Unicode characters, not PDF bytes; transformation offsets count output string characters before insertion.

## Independent audit and treatment

`book_epub/spacing.py` compares three streams only after exact nonspace alignment: reconstructed lines, literal PDF glyph text, and pypdf text. A missing separator is blocking only with literal-whitespace evidence and independent-parser corroboration. Punctuation-only differences without literal whitespace are tolerable for word-fusion checks. Other missing/extra boundaries remain review items. Unalignable pages remain inconclusive.

New bundles retain literal glyph text from the original PDF, before geometric reconstruction. Read-only `audit-spacing ORIGINAL.pdf BUNDLE` rereads both original parsers, rejects a source SHA mismatch, and works with the original fourth-test bundle without changing it. Historical bundles without the literal ledger are unavailable for retrospective spacing certification unless the original PDF is supplied. The auditor does not trust the reconstructed line text as its only source.

`source_word_boundaries` additionally replays line joins and authorized hyphen transformations without stripping spaces. This catches block-only losses even if the source ledger is correct. Existing exact serialized text, image, navigation, package, style and conformance checks remain active.

The old fourth-test output receives **Intervenção necessária** under the new source re-audit. It must be reconverted. The corrected output remains **Revisão recomendada**, including page 227 and pre-existing layout/editorial ambiguities; it is not universally certified textually faithful. Inconclusive examples must be reviewed against the source; there is no automatic candidate replacement, complete bundle editor, or content correction through `refine`.

## Reproduction and limits

```bash
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
python -m book_epub audit-spacing ORIGINAL.pdf OLD_BUNDLE > PRIVATE_AUDIT.json
PYTHONPATH=. python acceptance/check_spacing.py ORIGINAL.pdf OLD_BUNDLE NEW_BUNDLE PRIVATE_EVIDENCE.json
```

The source checker asserts geometry/line IDs/nonspace text, block identities/source memberships/roles/hierarchy/order, and image bytes are unchanged. Reversing only the logged literal-space insertions must reproduce every old source line exactly. Its output includes full per-page counts and private examples; do not publish narrative data. For earlier books, baseline extraction is executed with the exact approved `extract.py`, not with edited expected text. See the executed results below.

This is a deterministic mechanism defect, demonstrated by independent authored PDFs with compressed explicit spaces across Times/Helvetica/Courier at 8/12/24pt. Synthetic cases also cover geometry-only spacing, contiguous words without spaces, adjacent punctuation, legitimate hyphenation, line/paragraph breaks, ligatures, ambiguous boundaries, bad source ledgers, block-only corruption, legacy evidence and parser-order disagreement. They are not a representative PDF corpus or an external blind evaluation.

Literal glyph decoding still shares pdfminer/pdfplumber with reconstruction; pypdf provides a different parser, not an infallible oracle. Whole-page alignment conservatively abstains on order differences. Positive/zero-width/overlapping positioning and unmarked geometric spacing remain inherently uncertain in some PDFs. The fixed geometric fallback can still misclassify PDFs without explicit separators. No general success rate or exhaustive visual/device certification is claimed.

## Executed validation

**86 tests passed**, no failures/errors/skips, with EPUBCheck 5.3.0 enabled. Ten spacing-focused test methods were added, including nine font/size combinations. An explicit execution of the exact baseline extractor failed all nine compressed-space combinations; the revised extractor reproduced all nine literal expected strings. This is an authored mechanism regression, not blind corpus evidence. After the final diagnostic/hash-guard assertions, the ten spacing methods passed again; compile and whitespace checks also passed.

| Real original reconverted | Pages / source lines / images | Literal spaces newly recovered | Regression evidence |
| --- | --- | ---: | --- |
| O Último Desejo | 190 / 7,649 / 3 | 0 | All source lines, blocks and image assets identical to exact baseline extraction. Full editorial hierarchy remains uncertified, as before |
| A Espada do Destino | 232 / 9,603 / 2 | 0 | Six parent headings / 48 Roman subdivisions; lines/blocks/assets identical to baseline; all EPUB members byte-identical to approved revised EPUB |
| O Sangue dos Elfos | 231 / 8,044 / 3 | 0 | Seven chapter headings; lines/blocks/assets identical to baseline; all EPUB members byte-identical to approved revised EPUB |
| Tempo do Desprezo | 227 / 9,256 / 6 | 1,860 | Seven chapters; only logged literal spaces differ; source memberships, geometry, nonspace characters, hierarchy, block roles and images unchanged |

Earlier real books show **no occurrence of this proven literal-space-loss class** in these runs. They still contain other parser-spacing differences: a marker in the first book; an email-label boundary and one unaligned page in the second; markers/quotation boundaries in the third. Those remain conservative review items. Punctuation-only differences are separated. Successful earlier books do not excuse the fourth book's confirmed losses.

All four actual EPUBs passed EPUBCheck 5.3.0 with **zero fatal/error/warning/usage**. Source accounting, exact reconstructed word boundaries, nonspace text/order, image/style accounting, actual serialized text/images and ZIP/navigation/CSS checks passed. They remain **Revisão recomendada** because their independent editorial/layout ambiguities are not resolved by conformance. Rebuilding source text does not authorize or imply installed-skill materialization.

The original fourth bundle remains intact. PR #9 stays draft; no merge, new PR, installed-skill update or bundle editor is part of this change.
