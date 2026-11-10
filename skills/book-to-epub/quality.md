# Quality contract v1

## Findings and state
Every finding has a stable code, status (`pass`, `fail`, `inconclusive`, `unavailable`), impact (`blocking`, `review`, `tolerable`), explanation and evidence. A failure is an observed defect. Inconclusive means a check ran but did not establish the intended property. Unavailable means it did not complete or was not available. Reports group these separately; the full JSON retains individual page/block evidence.

State is deterministic: any non-pass blocking finding -> **Intervenção necessária**; otherwise any non-pass review finding -> **Revisão recomendada**; otherwise **Aprovado**. Tolerable findings never downgrade by themselves. No confidence score or arbitrary global similarity threshold.

| Check / situation | Evidence and consequence |
| --- | --- |
| Empty or unreadable extraction | Blocking; no EPUB |
| Scan/image/rotated text/detected columns | Blocking unsupported source; no knowingly incomplete EPUB |
| Vector graphics | Review: may be decorative or meaningful; not silently classified as lost prose |
| Blank page with no text or graphic objects | Tolerable; page recorded, no blank reflow page required |
| Independent pypdf extraction | Per-page ordered character comparison ignoring whitespace and typographic ligatures only; divergence is inconclusive/review, not a proven loss |
| Source line accounting | Every retained line represented once in original order; failures blocking |
| Source text replay | Reconstructed block must match its source lines and logged dehyphenation; failures blocking |
| EPUB content | Actual serialized spine text and block IDs must exactly equal model; failures blocking |
| ZIP/XML/package/navigation | ZIP integrity, uncompressed first mimetype, container, manifest resources/IDs, spine order, valid links/anchors, complete ordered TOC; failures blocking |
| CSS | Exact bounded template with validated finite em values 0–3; no fixed font, width, viewport or margins; mismatch blocking |
| EPUBCheck | Required for approval. Errors/fatal -> blocking; warnings -> review; missing/crashed/timed out/no structured report -> unavailable or inconclusive/review |
| Ambiguous hard hyphen | Keep hyphen, join line break, review with source IDs |
| Consecutive indented lines | Preserve text as a run; review possible block quotation semantics |
| Small-font note / long paragraph >8000 chars / uncertain page continuation | Retain text and flag relevant ambiguity for review |
| Inline emphasis / mathematical symbols | Preserve plain text, flag unrepresented semantics for review |
| Unresolved numeric/Roman margin | Retain nonmatching page labels and recommend review; do not guess offsets |
| Word spacing disagreement | Compare whitespace-normalized token boundaries between extractors; review, never hide via character counts |
| No detected chapter | Single-entry TOC; review, because chapter structure is not verified |
| Physical reader or Send to Kindle not tested | Tolerable; explicitly disclose no device/service claim |
| Optional author absent | Tolerable by contract: omit author, never fabricate |
| Incremental refinement | Model and all members except CSS/nav unchanged; source findings persist; rerun serialized checks and EPUBCheck |

## Reconstruction rules
- Group positioned characters within 3 points vertically; spaces inferred from gaps greater than max(1.5pt, 18% font size). Retain page, bounding box, size and stable line IDs. Independent extraction guards against many spacing/ordering failures, but is not ground truth.
- Treat two or more line gaps above max(36pt, 3x font size) as unsafe multi-column/tabular evidence.
- Remove decimal page numbers only when in outer 8% and equal to the physical page index. Remove exact repeated non-heading margin strings only on at least max(3, ceil(60% of pages)) pages. Retain removed strings in the ledger.
- Recognize chapter/part/section labels with a number or Roman numeral, or lines under 140 characters at least 1.25x body size. The most frequent line size defines body size. Headings start chapters; deeper heading hierarchy is future work.
- Paragraph boundaries: vertical gap >0.75x body size, new indentation >1x body size, or a sentence-ending line >4x body size short of the body right edge. A short-line-only boundary is flagged for review; ragged nonterminal lines alone never split paragraphs. Across pages, join only with a full preceding line, no sentence-closing punctuation, and no new indentation. Record uncertain continuation.
- Remove a discretionary soft hyphen at a joined boundary. Remove a hard hyphen only if the joined spelling occurs elsewhere in the same source and its hyphenated spelling does not. No dictionaries or model guesses change spelling.

## Limits and verification independence
These rules are intentionally bounded, not a universal layout recognizer. Unusual PDFs can evade heuristics; approval is not proof of editorial fidelity. Source accounting cannot detect an extractor that never saw content. Independent extraction and layout screening reduce that risk; scans/graphics are separately screened. Golden fixtures originate from authored text with assertions independent of the extracted model. Corruption tests deliberately remove, duplicate, reorder and alter content and links.

Automatic approval must be demonstrated on simple positive fixtures with actual EPUBCheck. Negative tests must establish the expected diagnostic category, not merely any non-approved result. Browser preview is useful evidence of fluid layout, but not proof of Kindle rendering. Actual Send to Kindle submission remains separately authorized.
