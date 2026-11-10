# Booksmith 0.2.0 — acceptance evidence

Executed 2026-11-10 with Python 3.12, locked dependencies, Java and EPUBCheck 5.3.0. This evolves MVP commit `856e4a70e2312568161876cb3737ba4622432cb7` from PR #9. No deployment replacement, merge or private book content is included.

## Reproduce

From `skills/booksmith/` in the full Git checkout:

```bash
python -m pip install -r requirements-dev.txt
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
PYTHONPATH=. python acceptance/run_editorial.py /path/NEW_OUTPUT /path/epubcheck.jar
```

The historical compatibility regression obtains original 0.1.0 files from the pinned Git commit, builds a real old-format bundle and refines it with the new engine. Its model remains byte-identical. Generated acceptance outputs stay outside the tracked tree.

## Automated evidence

**56 tests passed**, with real EPUBCheck configured and no skips. Editorial regressions supplement the 32 MVP tests.

| Area | Executed evidence |
| --- | --- |
| Structure | Authored expected paragraphs; page-local margin changes; wrapped dialogue with/without whitespace after dash; uppercase headings; two typography levels; nested Roman subdivisions; exact separators |
| False-positive controls | Uppercase prose and a body sentence beginning “Chapter 2” remain body text; sentence-ending page breaks cannot silently establish paragraph boundaries |
| Typography | Mixed roman/italic/bold-italic exact text/style; deliberately removed emphasis rejected |
| Images | Cover/internal illustration, repeated resource occurrences, bleed/clipping, visible transparency masks, 90-degree orientation, failed capture, text overlap, internal scan ambiguity |
| Corruption | Missing/duplicate/displaced occurrence, changed PNG bytes, extra XHTML image; manifest, cover and source-position checks |
| Portrait presentation | 3:4, 2:3 and 1:2 cover ratios at 360×640 and 768×900: first-page image bounds and no extra pages |
| Refinement | Chapter/image/OPF/model invariants; real historical schema-1 compatibility; earlier source findings retained |
| Refusal | Empty/invalid source, columns, internal scan risk and proven serialized defects withhold EPUB |
| Diagnostics | 1,000 repeated ambiguities: one bounded summary group, all 1,000 records retained in JSON |
| Independence | Original golden expectations, independent extractor, deliberate corruption and external EPUBCheck; agreement is not proof of editorial equivalence |

## Authored editorial acceptance

`run_editorial.py` creates an original three-page PDF with cover, uppercase title, two Roman subdivisions, wrapped paragraph, two unspaced em-dash turns, illustration, italic text, separator, second chapter, subtitle and different page margins.

- **Aprovado**; exactly **14/14 expected blocks**, including **2/2 images**.
- Five expected headings at their two levels; subordinate headings stay in the parent XHTML chapter and nested navigation.
- EPUBCheck: **0 fatal, 0 errors, 0 warnings**.
- Refinement changes only CSS; model and other members are byte-identical.
- Source/output sampled visually via MuPDF at 360×640 and 768×900: readable, unclipped cover, headings, paragraphs, dialogue, italics, illustration and separator.
- Initial cover pagination artifacts were detected and corrected using source-relative, aspect-bounded percentage image widths. Tall-cover fixtures check the correction; this is not a universal reader/viewport guarantee.

## Private full-book regression

The user-provided textual PDF has **190 pages and three raster occurrences**. Historical MVP and final engine processed identical source bytes and metadata. Source SHA-256: `950d810c1d6eee93ae7c79d7662c17f635fe465fa85356b3e7440d38b35c5d25`.

| Evidence | MVP 0.1.0 | Booksmith 0.2.0 |
| --- | --- | --- |
| Quality | Intervenção necessária | Revisão recomendada |
| EPUB | Withheld | Generated |
| Images | Three unsupported-image blockers | Three captured/serialized/source-position-checked occurrences |
| Headings | One | 16 level-one, 50 level-two |
| Source text accounting/replay | Reports only | Pass |
| Serialized text/order/images/typography | Not run | Pass |
| Independent per-page character comparison | 190 passes | 190 passes |
| EPUBCheck | Not run | 0 fatal, 0 errors, 0 warnings |
| Findings | 2,920 entries | 314 entries, 19 summary groups |
| Indented-run/short-boundary ambiguities | 1,353 / 1,151 | 27 / 11 |

The heading counts include front matter; they are **not an independently certified chapter count**. Allcaps front matter can resemble narrative headings; source evidence remains in the model. Ordered line accounting does not establish that every paragraph boundary or inferred heading is editorially correct.

Remaining review occurrences: 33 ambiguous retained hyphens, 27 quotation/indent candidates, 25 uncertain page continuations, 11 short paragraph boundaries, 7 token-spacing disagreements, 4 small-text cases, 4 quotation-punctuation cases, one vector-graphics limitation. These are uncertainties, not proven content loss. Device testing is unavailable/tolerable.

Visual sampling compared a source chapter opening to its reflow: uppercase title, Roman subdivision, paragraphs and initial dialogue turns appeared correctly separated. This is not a complete 190-page editorial audit. Text/images, EPUBs, screenshots and complete reports remain private; only aggregates and reproduction instructions are versioned.

## Limits

No Kindle hardware, Send to Kindle, browser or landscape acceptance was executed. Rasterization is 144 DPI; source encoding/resolution and accessibility semantics are not guaranteed. Internal image-only illustrations can require intervention because they resemble scans. Overlapping compositions, arbitrary vector reconstruction, OCR, advanced tables/formulas and linked notes remain outside scope.

Font-name style evidence, invisible mixed paragraph boundaries and unmarked same-font titles remain limitations. Real-book classification stays **Revisão recomendada**: fewer findings and EPUBCheck success do not justify approval. The installed ChatGPT preview remains unchanged.
