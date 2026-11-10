# Booksmith quality contract v2

## Findings and state

Every finding has a stable code, status (`pass`, `fail`, `inconclusive`, `unavailable`), impact (`blocking`, `review`, `tolerable`), explanation and evidence. Failures are observed defects. Inconclusive checks ran but did not establish the property; unavailable checks did not complete. No similarity score substitutes for accounting.

Any non-pass blocking finding → **Intervenção necessária**. Otherwise any non-pass review finding → **Revisão recomendada**. Otherwise → **Aprovado**. Approval describes implemented evidence, not guaranteed editorial equivalence.

| Situation | Required evidence and consequence |
| --- | --- |
| Empty/unreadable text, invalid glyph, detected columns, rotated text | Blocking; no incomplete EPUB |
| Raster images | Preserve each occurrence with source ID, page, original/visible bounding box, rendering transform, PNG payload, dimensions and SHA-256 |
| Source image outside media box | Preserve its visible intersection; record original geometry; no visible area is blocking |
| Image composition | Text/image or image/image overlap blocks; side-by-side text requires positioning review |
| First image-only page covering ≥60% of page | Preserve as a cover, with OPF cover-image metadata |
| Interior image-only page covering >60% of page | Blocking ambiguity: illustration vs scan requires source inspection; no OCR |
| Other image-only page | Preserve its image; no semantic classification required |
| Image capture failure or missing/duplicate/displaced occurrence | Blocking; never silently omit |
| Vector graphics | Review; raster occurrence capture does not claim arbitrary vector preservation |
| Independent extraction | Per-page ordered characters, ignoring whitespace/typographic ligatures only; disagreement is review, not proof of loss |
| Token spacing disagreement | Review even when characters match |
| Source text and order | Every retained line exactly once, in order; replay text and logged dehyphenations; blocking on mismatch |
| Typography | Replay non-whitespace styled characters against source spans; missing/altered bold/italic is blocking |
| Serialized EPUB | Exact text/block order, image bytes and references, heading tags, inline styles and separator class; blocking on mismatch |
| ZIP/package/navigation | ZIP/XML, mimetype, manifest, media types, spine, references, anchors, complete ordered nested TOC; blocking |
| CSS | Exact bounded responsive template; paragraph values finite 0–3 em; images max-width:100%, height:auto, with source-relative percentage widths and the long side capped to one content width for portrait presentation |
| EPUBCheck | Required for approval; errors block, warnings require review; missing/crashed/incomplete is review/unavailable or inconclusive |
| Physical reader/Send to Kindle | Explicitly disclose when untested; never infer device compatibility from conformance |
| Refinement | Model and all EPUB members except CSS/nav remain byte-identical; retain source findings, revalidate package/conformance |

## Reconstruction evidence

- Positioned characters retain page/line IDs, bounding box, size, font names and bold/italic spans. Group characters within 3 points vertically, infer spaces from gaps >max(1.5pt, 18% font size). No generative rewriting.
- A page-local body profile uses character-weighted common font size and body line extents. Changes of page margins do not become quote evidence. Repeated first-line offsets returning to the baseline are conventional paragraph indents.
- Heading evidence combines explicit labels, size ≥1.25× body size, short isolated uppercase text with centering/bold, and centered isolated Roman numerals. Two levels are inferred using relative typography and Roman subdivisions; ambiguous missing parents require review. Uppercase inside wrapped prose is insufficient. Same-font unmarked titles can remain undetected.
- Level-one headings start XHTML chapters; level-two headings remain within the parent chapter and appear in nested navigation. Front matter retains text and can receive inferred headings: automatic hierarchy is not an editorial oracle.
- Paragraphs use spacing >0.75× body size, a new first-line indent >0.75× body size, and conservatively flagged short terminal lines. A single em/en dash at line start, with or without following whitespace, establishes a new speech; its ordinary wrapped lines continue until another structural cue.
- Consecutive receded lines outside conventional indents are quotation candidates. Bilateral inset supports blockquote rendering; uncertainty remains review. Ordinary indentation alone does not assert a quotation.
- Across pages, join only with an unclosed sentence, full preceding line and no new indent. Otherwise preserve separation and flag uncertain continuation when no new first-line indent provides positive paragraph evidence; sentence-ending punctuation alone cannot prove a paragraph boundary.
- Pages without positive paragraph cues require review. Mixed layouts can still hide boundaries indistinguishable from wrapping.
- Soft hyphens are removed only at logged joined boundaries. Hard hyphens are removed only when the joined spelling occurs elsewhere in the source and the hyphenated form does not. Retain uncertain hard hyphens with review.
- Font-name evidence supports bold/italic tags; opaque font naming, unusual encodings, optical styles, superscripts and other typography may require inspection and are not claimed as universally reconstructed.
- Recognizable textual section separators retain their exact glyphs. Small-font notes, unlinked quotation punctuation and mathematical symbols remain text with review.
- Image crops render at 144 DPI through PDFium and preserve displayed clipping, color and masks in the visible region. This is a recorded rasterization, not preservation of the embedded original encoding, original resolution or selectable image text. No semantic alternative text is fabricated; empty image alt text does not assert accessibility equivalence. Image extraction/capture and decode/hash checks do not prove visual equivalence; visual acceptance remains sample-based. Portrait cover ratios 3:4, 2:3 and 1:2 are checked at 360×640 and 768×900; landscape layouts are not verified.
- Source image inventory is independent of successful capture. Image blocks must appear at the correct source-line position, exactly once per occurrence. Text accounting and image accounting are separate.

## Diagnostics and reproducibility

Markdown groups findings by code/status/impact/detail with counts, actions and at most three representative origin examples. Blocking and review risks precede tolerable checks. Complete findings, spans, image inventory and transformation records remain in JSON; normal layout transformations are not inflated into defects.

Stable IDs, ordered JSON, fixed ZIP timestamps and pinned dependencies preserve reproducible EPUB/model bytes for identical inputs/options. External checker paths/timing can differ. A new output directory is required for each revision.

## Compatibility and independent acceptance

New conversions use model schema 2, engine 0.2.0. Historical schema-1/engine-0.1.0 bundles are supported for presentation-only refinement without model migration or source re-extraction. Their earlier semantic limitations remain; compatibility never upgrades old evidence. Other schemas are rejected.

Authored golden fixtures assert expected text, paragraph boundaries and hierarchy independently of extraction. Negative tests remove, duplicate, move and corrupt text/images/styles/navigation. Real EPUBCheck must demonstrate approval on supported positive examples. The private full-book regression is evidence of one source only and is never published with its content or conversion bundle. No single fixture defines universal heuristics.
