# Booksmith 0.2.0 — explicit-chapter novel acceptance

Executed 2026-11-10 on `feat/book-to-epub-mvp`, continuing draft PR #9 from `d435429b057272b6c88720a357467c7cce8b336d`. No merge or installed-materialization change. This supplements previous evidence; historical results are not overwritten. Private PDFs, narrative extracts, images and bundles are not committed.

## Confirmed cause

The original 231-page source and its first conversion bundle were available. Source PDF p. 122 was also rendered and inspected. The original chapter index contains seven ordinal chapter labels at one level. The retained ledger records body prose at 14.4pt, smaller epigraphs/letters at 10.8pt and chapter labels at 16.56pt.

The old `profiles` function took the character-weighted font mode of long lines on each page. It chose 10.8pt on pp. 122, 123 and 125; p. 124 retained 14.4pt. Small-font epigraphs and letters therefore made ordinary 14.4pt prose satisfy the 1.25× font-size heading test. That test did not require isolation or exclude recurring body typography. The old bundle contains exactly 56 narrative headings in this region.

The explicit-label regex accepted digits/Romans but not written ordinals: `CAPÍTULO QUINTO` did not match. On p. 122 the fifth title acquired `font_size` evidence and was demoted by comparison with the larger 20.16pt title-page font. Other chapter openings had only uppercase-layout evidence, so the conditional font-based demotion did not apply to them. This explains the inconsistent level of the fifth chapter, rather than merely correlating the defect with font variation.

Front-matter recognition and the audit were centred on repeated title/I/II cycles. This novel has explicit chapters rather than those cycles. Neither its original contents nor its prose headings contradicted a checked invariant, so the old main audit returned `editorial_structure: pass`. Valid EPUB links and EPUBCheck only confirmed serialization/conformance of that incorrect model.

## Small structural correction

`book_epub/evidence.py` provides source-only facts, without importing block predictions or book identifiers. It is a bounded shared vocabulary for classifiers and the auditor, not a second document framework.

- Anchor a smaller page-local font mode to the dominant document body size only when that size is actually present in at least three long lines on the page. Keep wholly smaller-font pages local.
- Require isolation for font-size heading candidates and reject narrative counter-evidence. Adjacent same-style prose and recurring body typography are measured directly from source lines; dash-led dialogue adds contrary evidence.
- Recognize full explicit label families using PT/EN written cardinal/ordinal numbers one through ten, digits and valid Roman numerals. Repeated families constrain levels independently of cover typography. Part/chapter families preserve two-level nesting; deeper structures require review.
- Corroborate repeated isolated large title styles followed by smaller body prose across pages. This preserves previously approved conventional named chapters without approving every lone typographic candidate.
- Compare ordered explicit labels with the original sparse contents, generalizing the existing anthology-contents mechanism. Confirmed front matter preserves every line/image in a dedicated XHTML without narrative headings.
- Preserve anthology title/Roman cycles. Terminal uniformly smaller publishing pages need both rights and ISBN/CIP evidence; remove the arbitrary 35-line ceiling. A body-sized terminal closing formula remains text rather than becoming another chapter, unless earlier source occurrence contradicts that inference.

Explicit family constraints take precedence over local font ranking, including title/Roman corroboration. Packaging, image capture, paragraph text replay, profile CSS and bundle schemas remain unchanged. No title/page/block allowlist occurs in runtime code. Source-specific identifiers occur only in acceptance oracles.

## Editorial auditing and quality

The auditor reconstructs source facts from the line ledger. It ignores saved `heading_evidence` and saved editorial predictions, compares source constraints with actual block kinds/levels/roles and checks raw neighbouring narrative lines. Shared lexical parsing can still have common-mode defects; independent literal oracles, model corruption tests and PDF inspection complement it.

Confirmed wrong-level/missing explicit chapters, contradicted matter roles, and prose headings with both recurring body style and adjacent narrative continuity are blocking. Isolated dialogue-like titles, abnormal heading concentrations, source-contents disagreement, unsupported depth and uncorroborated typography require review. Every finding includes source lines, pages, block IDs and a reason; prose findings include neighbouring source IDs and negative evidence.

Reauditing the old novel bundle flags all 56 narrative headings: 47 blocking contradictions and nine review ambiguities. It also detects the wrong fifth level, 13 incorrect front-matter roles, three abnormal-density regions, a closing heading and 42 unseparated publishing-information lines. The overall state becomes **Intervenção necessária**, and presentation-only refinement withholds its defective EPUB while preserving model bytes. The nine uncertain individual diagnoses are not relabelled as proven merely because manual inspection identified their defect.

The three quality states remain. Successful conformance never cancels a blocking editorial defect. `editorial_structure: pass` now means only that the implemented checks found no contradiction, not universal editorial certification.

## Executed results

| Private source | Validation actually executed | Result |
| --- | --- | --- |
| O Sangue dos Elfos, 231 pages | Original PDF reconversion; literal seven-chapter oracle; original-bundle source/image equality; paragraph/dialogue samples; actual XML/spine/nav/image/style/text accounting | Seven level-one chapters; 56/56 false headings removed; three images; nine content XHTMLs |
| A Espada do Destino, 232 pages | Original PDF reconversion; existing literal anthology oracle; original accepted bundle comparison | Six main tales; 48 level-two Romans (8/9/4/10/8/9); two images; eight content XHTMLs |
| O Último Desejo, 190 pages | Original PDF reconversion; compare all 7,649 source-line records against schema-1 diagnostic; source/serialized text, order, styles and image inventory | Three images (pp. 1, 2, 188) preserved; source fields identical; no integrity failures. Full editorial hierarchy is not certified by this regression |

The novel chapters start on source pages 4, 33, 57, 83, 122, 154 and 188. Front matter contains the cover/title page/printed contents; publishing information is separate on pp. 230–231. Nine top-level navigation entries correspond to front matter, seven chapters and publishing information. No subordinate narrative headings remain. The closing formula is preserved as text inside the final chapter.

The 56 prior false-heading source lines map to paragraphs/quotes. Source lines p122-l15/l16 reconstruct one prose paragraph; p122-l17/l18 reconstruct one wrapped dialogue turn; p122-l14 begins a separate turn. The oracle asserts these boundaries independently of the motor's classifier. This is targeted paragraph acceptance, not an exhaustive literary reading.

For the novel and anthology, source-line ledgers and image assets/provenance equal the previous bundles exactly. Text audit replays every retained line and logged dehyphenation; style audit replays non-whitespace bold/italic characters. Serialized text/order/images/semantics, actual navigation hierarchy and destinations pass. Rebuilding all three EPUBs from their models reproduces every package member byte.

EPUBCheck **5.3.0**, actually executed on all three final EPUBs: **zero fatal/errors/warnings/usage**.

| Output | SHA-256 |
| --- | --- |
| Novel EPUB | `dfb6e56390287e8178b6de68ca5f13853af33bc53c60d00bbb3ec733fd4ac994` |
| Anthology EPUB | `c15b84b2b52986720902eef1a56f25c96d16f540b061fc8434329d46ecab32dc` |
| First-book EPUB | `20b0b376a6b68b2203b552dc9b1dafe5128d0d16fc91ea3f79aba6da6e8dae92` |
| Runtime implementation | `ba80ac7e32d553d0fbfdc971270f14c7ee46b33846dcf2fa12d18220a5bb57a6` |

The anthology EPUB is byte-identical to its previously accepted final EPUB when metadata/options match. Source SHA-256 for the novel: `1ea6d7fc34a67469c6fc27177c8a16638ee7d7dab455dd2c12048b136b39d3dd`.

Complete suite: **76 tests, zero failures/errors/skips**, including real EPUBCheck and the pinned historical-engine schema-1 refinement test. Fourteen new tests supplement the existing 62: twelve development pattern/mutation checks and two independent PDF validation tests (one has cardinal/Roman subcases). Validation generators use different titles, fonts, layout and chapter numbers, and do not call the development generator. They were defined before their first execution; their passing results did not drive per-source fixes. They are small authored fixtures, not a blinded representative corpus or a general success-rate estimate.

Positive/negative coverage includes epigraphs smaller than prose, legitimate whole-page font changes, explicit ordinal/cardinal/Roman labels, no contents, ambiguous isolated dialogue titles, recurring named-title styles through the prior prose regression, named anthologies with Roman subdivisions, wrong/missing levels, promoted pre-text, forged heading evidence, dense false headings, original-contents divergence and unsupported hierarchy depth.

Original editorial acceptance also passes: 14 expected blocks, two images, five expected heading levels; refinement changes only CSS and leaves model bytes unchanged. Actual previous schema-2 anthology refinement preserves model and non-CSS/nav members and remains usable; the defective novel bundle remains loadable but is withheld on new proven defects. Schema-1 evidence is not retroactively upgraded.

All three private books remain **Revisão recomendada**. For the novel, residual diagnostics include hyphens, possible quotes/indents, paragraph/page boundaries, small text and token-spacing disagreements. No editorial-structure contradiction remains under the implemented checks. The first book still has uncertain typographic headings: its text/image regression must not be misrepresented as complete hierarchy approval. Physical Kindle, Send to Kindle, landscape, exhaustive visual comparison and universal image accessibility were not tested.

Environment: Python 3.12.14, Java 21.0.13; dependencies remain pinned in requirements-lock.txt. Engine version stays 0.2.0 in this unmerged PR; implementation hashes distinguish revisions.

## Generalization and sustainability

1. **Reusable decisions already supported:** immutable source accounting, style/image preservation, explicit label-family precedence, repeated source patterns, original-contents corroboration and independent contradiction checks. These operate on editorial classes, not particular books. The small evidence layer is justified by the conflict between local typography and document structure; a broad refactor was unnecessary.
2. **Fragile heuristics still present:** character-length and isolation thresholds, character-weighted font modes, minimum recurrence/page counts, exact font-family signatures, sparse-front-matter limits, quote/paragraph geometry and exact contents echoes. Contents with leaders/page numbers or decorated/multi-line labels are not fully parsed. Written numbers beyond ten, unknown languages, same-style unmarked titles and three-plus-level structures remain outside confident reconstruction.
3. **Reasonably supported:** selectable horizontal single-column prose, conventional explicit chapters, epigraphs and smaller embedded letters, plus demonstrated two-level anthologies with Roman subdivisions and uncomplicated raster illustrations. These three real books and authored fixtures establish bounded regressions, not coverage of most published books.
4. **PDF-inherent limitations:** visual layout often omits paragraph/title semantics, reading intent and quotation structure. Identical geometry can encode different structures; opaque fonts and ambiguous hyphens cannot always be resolved deterministically. Better evidence can reduce uncertainty, not recover information absent from the source.
5. **Bundle vs motor:** a repeatable contradictory source pattern belongs in a tested motor change. A one-off ambiguous title, intentional irregular numbering, unusual paragraph break or editorial preference belongs in a reviewed source-backed bundle correction. Presentation-only changes already use `refine`; structural corrections require a separate audited operation. A narrow bundle patch/review interface is a future option, not implemented here. Never add a book-name/page exception to bypass ambiguity.

The goal that new conventional books normally need no commits is now an explicit design constraint. These changes demonstrate generalization across equivalent patterns. They do **not** yet demonstrate exceptional rather than recurring human intervention: all three real books retain review findings, and no representative independent corpus has been measured. A larger fixed evaluation set should precede a reliability claim.

## Reproduction

From `skills/booksmith/`, with the private source files/bundles supplied separately:

```bash
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
PYTHONPATH=. python acceptance/run_editorial.py /path/NEW_EDITORIAL_OUTPUT /path/epubcheck.jar
PYTHONPATH=. python acceptance/check_novel.py /path/NEW_NOVEL_BUNDLE /path/OLD_NOVEL_BUNDLE
python acceptance/check_anthology.py /path/NEW_ANTHOLOGY_BUNDLE /path/OLD_ANTHOLOGY_BUNDLE
PYTHONPATH=. python acceptance/check_first_book.py /path/NEW_FIRST_BUNDLE /path/OLD_DIAGNOSTIC_BUNDLE
```

Reconvert originals using the documented CLI and a fresh output directory before applying these oracles. Synthetic tests are not substitutes for the real-source commands above. No OCR, translation, generative rewriting, new input formats or automatic bundle editor was added. PR #9 remains draft awaiting user review before any materialization.
