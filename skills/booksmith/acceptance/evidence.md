# Historical MVP acceptance evidence — 2026-11-10

This document records engine 0.1.0 at commit 856e4a7. Its unsupported-image behavior and expected refusals are historical. Current results are in [Booksmith evidence](booksmith-evidence.md).

## Scope and reproducibility

Python 3.12, locked dependencies, EPUBCheck 5.3.0. The regression suite now has 32 tests; all passed, including real EPUBCheck approval on simple positive fixtures. New checks exercise ambiguous paragraph layouts with period, comma and no terminal punctuation, plus flattened subtitles and quotations. Existing spaced/indented positive cases continue to pass.

Real literary text was downloaded from these public-domain source editions, not invented to suit the converter:

| Text | Source | SHA-256 of downloaded text |
| --- | --- | --- |
| Lewis Carroll, Alice’s Adventures in Wonderland | https://www.gutenberg.org/files/11/11-0.txt | a3a27f8edbf7fcd9b8ba8435494440e24952deaa3e2f2d65192d4cb7ca403754 |
| Jane Austen, Pride and Prejudice | https://www.gutenberg.org/files/1342/1342-0.txt | 81300b79e8a8d65ac530a97578417d06137e3bbc90622a10a65e5036183d2500 |

For each work, the first two qualifying prose paragraphs of chapters I and II were selected, source line wraps removed, and the excerpts re-typeset with conventional paragraph spacing. Chapter labels were controlled as Chapter 1/2. These are **real prose in controlled PDFs**, not independently published PDF layout tests, complete-book conversions or proof of generalization. Source text/PDFs/EPUBs/screenshots remain outside the repository; only code and evidence metadata are committed.

Reproduce from this Skill directory after downloading the two source files as `alice.txt` and `pride.txt` into INPUT:

```bash
PYTHONPATH=. python acceptance/run_public_texts.py INPUT NEW_OUTPUT /path/epubcheck.jar
```

The source editions can change; compare hashes before claiming reproduction of this exact run.

## Results

| Check | Alice excerpt | Pride and Prejudice excerpt |
| --- | --- | --- |
| Classification | Revisão recomendada | Revisão recomendada |
| Paragraph reconstruction against source before PDF creation | 4/4 exact | 4/4 exact |
| Chapter headings and order | 2/2 exact | 2/2 exact |
| Serialized EPUB blocks against model | Pass | Pass |
| Spine, TOC completeness/order, internal links/anchors | Pass | Pass |
| EPUBCheck 5.3.0 | 0 errors, 0 fatal, 0 warnings | 0 errors, 0 fatal, 0 warnings |
| Semantic limitation | Possible quotation/dialogue: textual marks retained, no dedicated semantic markup | Same |
| Unavailable check | Device/Send to Kindle | Same |
| Visual sample | Source page 1 and EPUB chapter 1 at 360pt inspected via MuPDF | Same |

Visual inspection found readable text, expected paragraph separation, preserved punctuation and fluid width, without clipping in the inspected pages. It is sampling, not an exhaustive visual audit. No browser, Kindle or Amazon acceptance claim follows from MuPDF rendering.

PDF hashes: Alice `9562b0a5c399b2bf012fda7a9aeffdcef74e22d753c838c22a71b8296cee4952`; Pride `277503ced4e0f5fc578619f44f07070539cc327c191ae5f39281c6d83d9171c0`.

## Independently published PDF: negative acceptance

Source: https://www.planetebook.com/free-ebooks/alices-adventures-in-wonderland.pdf (111 pages). Download SHA-256: `c0d87d2223caaf30f56097ac701e4f9c74fb501a646e16bce1369a383f2bbd26`.

Executed the complete source through the converter with EPUBCheck configured. Result: **Intervenção necessária**, no EPUB generated. A raster image triggered the existing unsupported-content blocker. Independent extraction comparisons were inconclusive on all 111 pages; the source contains special typography, including a drop capital on page 4. These disagreements are not asserted as proven losses. Intermediate paragraph reconstruction (938 blocks) was not editorially approved or counted as an exact paragraph result.

Navigation, serialized EPUB and EPUBCheck were unavailable/not run because source screening prevented package generation; they are not failures of an existing EPUB. Visual inspection of source page 4 confirmed drop-cap/title typography and justified retaining this case outside the uncomplicated prose acceptance path. No output visual inspection was possible because there is no EPUB. The PDF and intermediate text remain outside the repository.

Reproduce using the linked source, then run the documented CLI with title, author, language en and the local EPUBCheck JAR. An exit code of 2 and a report-only bundle are expected. This is evidence of correct refusal of an unsupported real source, not successful full-book conversion.

## Residual acceptance limits

Fully uncued paragraph geometry is inherently ambiguous. It now receives review rather than approval, but an invisible boundary inside otherwise visibly segmented prose can still evade detection. Same-font subtitles and unmarked quotations cannot be reliably inferred. Review findings do not claim proven textual loss.

No protected/private document is included. Native ChatGPT materialization and merge remain deferred to user review. Successful conversion of an independently published simple PDF and complete-book editorial sampling remain additional acceptance coverage; the controlled excerpts above must not be described as completing those checks.
