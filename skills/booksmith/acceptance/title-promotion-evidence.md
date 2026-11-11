# Conservative structural promotion — fifth private-source review

Review date: 2026-11-10 (America/Fortaleza). Booksmith remains 0.2.0 and provisional in draft PR #9. No merge, release, installed Skill update or deployment is part of this change.

## Confirmed cause and pipeline trace

The original fifth bundle and a source reconversion reproduce the extra title `15-08917 CDD-891.8`, source `p264-l8`, block `b3428`, previously in `chapter-0009.xhtml`. This is catalogue information, not a narrative title. The original PDF's last page was rendered and visually inspected; the two codes sit at opposite horizontal ends of the same baseline. This is a source-layout observation, not a lexical blacklist.

1. `extract.py` groups glyphs by baseline and reconstructs an ordered line, with explicit spaces preserved. The two distant codes become one line; its bounding box spans both ends. Extraction must retain this content. Changing its text or deleting it would be the wrong repair.
2. The line has size 5.996, local/body reference approximately 6.0, font `AAAAAD+f1kvcjzl-1cn-fhf-26v9eoeboqz9`, no bold/italic spans. There is no large-font evidence. Its horizontal box is `[25.0, 227.306]` on a page of width 252.1802: the box midpoint is 126.153, almost exactly the page midpoint 126.0901. The detector therefore treats it as centered despite its two separated components.
3. `local_headings()` sees isolation and uppercase (`str.isupper()` ignores digits and punctuation). It emits only `uppercase_layout`, level 1. This is a reasonable candidate signal but insufficient confirmation. No explicit label, repeated title family, contents echo or narrative subdivision corroborates this line.
4. `document_structure()` previously initialized its final heading map directly from these local candidates. Document-wide corroboration added/overrode headings but did not require corroboration for remaining candidates. The presence of seven confirmed chapters neither confirmed nor excluded the extra candidate. No fixed chapter count should be introduced.
5. `extract()` trusted membership in that map and created a `heading` block. `package.chapters()` split on level 1, and `navigation_entries()` added the resulting heading. Those serializers correctly followed the erroneous editorial model; they were not the source of the decision.
6. `audit_editorial()` independently reread source-line evidence and flagged `ambiguous_title`. Review findings allow usable EPUB output; they neither demoted the block nor withheld the package. Thus an uncertainty already known to the auditor became an effective editorial decision before review.

The repair belongs at hierarchy consolidation, with supporting source-evidence and audit changes. The geometric detector and space reconstruction remain intact.

## Decision policy and false-negative controls

Local candidates and confirmed headings are now separate. `pending_titles` records proposed level, local evidence and reason for deferral. It is diagnostic state, not a navigation list.

| Decision | Evidence and behavior |
| --- | --- |
| Confirmed structural title | Explicit isolated label; corroborated repeated typographic family; established parent/Roman structure; or distinctive isolated large title followed by a smaller body run. Unnumbered, unique titles can qualify. Confirmed headings retain the existing two-level hierarchy and navigation behavior. |
| Ambiguous candidate | Local visual signal without enough corroboration. Preserve exact text/spans in an ordinary paragraph and record `ambiguous_title`, `decision=deferred`, source/page/block and candidate evidence. No heading, file boundary or navigation entry is created by the candidate. |
| Ordinary/nonstructural content | Preserve source text and reading order through ordinary reconstruction. Known source-backed front/back matter retains its existing role. Absence of heading evidence does not authorize dropping material. |

Specific safeguards:

- The lack of negative narrative evidence no longer confirms a title by itself.
- Strong size contrast plus a body run can confirm a single unusual or unnumbered title. A title/subtitle stack is followed through to body text; title styles at both levels are considered when ranking repeated families. Short initial body lines do not invalidate the surrounding run.
- A title followed by corroborating I/II subdivisions can anchor a single-work title family without requiring repeated anthology cycles. Peers in an already corroborated non-Roman style can qualify when followed by smaller continuous body text, including a short initial dialogue turn. Style repetition alone cannot establish this anchor.
- Predominantly numeric strings do not receive typography-only lexical support: alphabetic characters must outnumber digits for those routes. This is a general weak-content feature, not a CDD/ISBN/editor/publisher vocabulary. It does not prove the string nonstructural; unusual numeric/symbolic titles remain candidates and may require review. Explicit labels/Roman structure are separate positive routes.
- No source names, page positions, catalogue identifiers or expected number of chapters occur in runtime logic. Expected book-specific titles, page numbers and hashes occur only in private-source acceptance oracles.
- An old test that treated an unlabelled duplicate of `THE END` as sufficient title confirmation now expects an unresolved candidate. A repeated phrase alone is not a demonstrated source contents entry. A separate test still verifies ordinary terminal-formula handling.

The bounded numeric criteria are explicit: local isolation uses a gap greater than 0.65 times the local body size (or a page boundary); size candidates require at least 1.25 times the local body size. Standalone confirmation requires at least 40 characters across a following same-page body run at less than 85% of the title size. Family peers require the exact rounded size/font key of a confirmed non-Roman anchor, a following body size below 95% of the title size, at least 40 characters in a contiguous run, successive gaps no greater than 0.75 times its size and font sizes within 10% of its first line. These are bounded layout signals, not universal publishing thresholds. An additional strong afterword remains a heading even after explicit narrative chapters; recognized chapters provide context, not a maximum count.

In the four earlier baseline conversions, the anthology and two novels had no structural review findings. The first book had four ambiguous unnumbered interlude titles. Their source typography matches already corroborated narrative titles and leads into ordinary body runs, sometimes beginning with a short speech. The new family confirmation preserves all four, together with every other earlier heading. No analogous catalogue-code heading was found in those baseline heading lists. The first book's entire hierarchy has not been independently certified; absence of that specific defect is not proof that all other editorial decisions are correct.

The auditor recomputes these decisions from source lines, ignoring stored `pending_titles` and heading-evidence claims. Deferred candidates remain visible even after demotion. A legacy/model-mutated unsupported promotion is reported as `unsupported_promotion`; this remains a review finding, not proof that the content is semantically invalid. Source-backed contradictions still block. Automatic prevention happens during reconstruction; the read-only auditor does not silently edit an existing EPUB. Reconversion is required to change its structure.

## Complementary material and architecture boundary

The source body and both terminal publishing pages all use approximately 6.0-point text. The existing backmatter rule requires a terminal run uniformly below 85% of the document body size plus rights/catalogue evidence. It stops before collecting these same-font pages, so it never reaches its semantic conjunction. The source has rights/catalogue indicators; it fails the font requirement. This explains why credits and catalogue material remain inside the final narrative XHTML.

The architecture already supports `content_role=frontmatter/backmatter`, preserved order and separate XHTML/navigation for positively recognized regions. This fix deliberately does not relax that terminal-page gate or invent a same-font catalogue parser. Doing so safely needs region-level evidence for a narrative-to-publication transition, including mixed pages, standalone afterwords, references, illustrations and title-only books. That is future work. Until then, uncertain complementary content stays in place in the reading stream. Its survival does not mean its role is certified.

## Independent tests and reproduction

`tests/test_title_promotion.py` adds eight authored synthetic-PDF cases covering numeric chapters with/without contents, single unnumbered titles, isolated titles, repeated large arbitrary identifiers, cataloguing-like terminal data, deferred uppercase candidates, a real afterword, anchored short-dialogue transitions and two-level title/subtitle books. Assertions use literal expected title lists/levels and actual serialized navigation, not a classifier-generated expected model. A deliberate model/evidence mutation verifies that audit does not trust recorded predictions.

Existing source-corruption, images, spaces, paragraphs, hierarchy, three-level limitation, Romans, contents, refinement and historical compatibility tests remain in the full suite. Synthetic cases are not real-book results.

Commands (from `skills/booksmith`; output directories must be new):

```bash
EPUBCHECK_JAR=/path/epubcheck-5.3.0/epubcheck.jar python -m unittest discover -s tests -v
python -m book_epub convert ORIGINAL.pdf NEW_BUNDLE --title 'Source title' --language pt-BR --profile kindle --epubcheck-jar /path/epubcheck-5.3.0/epubcheck.jar
PYTHONPATH=. python acceptance/check_title_promotion.py BASELINE_ROOT NEW_ROOT
PYTHONPATH=. python acceptance/check_anthology.py NEW_ROOT/2
```

The five regression inputs are the original private PDFs, not regenerated text fixtures. Each was converted from source before and after the change. `check_title_promotion.py` pins source hashes and authored expectations for the six-tale anthology and the three seven-chapter novels. The first book is an exact preservation regression, not a newly certified hierarchy. It verifies unchanged source/image ledgers, paragraph text/order/emphasis, spacing findings, actual EPUB member bytes for earlier books, literal fifth-book catalogue text in its new XHTML, expected navigation and real EPUBCheck counts. Source/prose-containing models and conversion bundles must remain private and must never be committed to Git.

## Executed results

The final full suite passed **94 tests**, with no failures, errors or skips, in 264.219 seconds, with real EPUBCheck 5.3.0 available. Compilation and `git diff --check` passed. Eight new test methods supplement the previous 86. Real-source outcomes are separate from these synthetic tests.

| Original private PDF | Pages | Headings before → after | Content XHTMLs before → after | Images | EPUB preservation |
| --- | --- | --- | --- | --- | --- |
| O Último Desejo | 190 | 62 → 62 | 14 → 14 | 3 | Entire EPUB byte-identical to baseline; complete hierarchy still not certified |
| A Espada do Destino | 232 | 54 → 54 (6 tales + 48 subdivisions) | 8 → 8 | 2 | Entire EPUB byte-identical; existing independent anthology oracle passes |
| O Sangue dos Elfos | 231 | 7 → 7 | 9 → 9 | 3 | Entire EPUB byte-identical; literal chapter/page oracle passes |
| Tempo do Desprezo | 227 | 7 → 7 | 8 → 8 | 6 | Entire EPUB byte-identical; literal chapter/page oracle passes |
| Batismo de Fogo | 264 | 8 → 7 | 9 → 8 | 4 | Only the uncorroborated catalogue title is demoted; original text/order/spans and extraction/image ledgers preserved |

The fifth output has one front-matter entry and seven narrative chapter entries, with starts at source pages 6, 39, 81, 110, 140, 180 and 216. `b3428` is an ordinary paragraph in `chapter-0008.xhtml`; `chapter-0009.xhtml` and its catalogue navigation entry no longer exist. The catalogue text is preserved literally. Same-font credits/catalogue material stays at the end of the seventh narrative chapter rather than receiving an unjustified automatic backmatter boundary.

Every real output has zero fatal/errors/warnings/usage issues in EPUBCheck 5.3.0, and no blocking findings. Source-line accounting, text/order/word boundaries, images, emphasis, serialized text, package/navigation/CSS all pass. All five remain **Revisão recomendada**. The fifth retains the same five inconclusive spacing findings (four geometric/extractor disagreements and one unaligned page); there is no newly detected confirmed literal-space loss. Its 247 aligned spacing findings and 27 punctuation-only differences also remain unchanged. Earlier spacing review counts are respectively 1, 2, 3 and 1. No spacing disagreement is silently rewritten.

All five final reports record the same engine implementation fingerprint: `2aa75eb85599003f25976310f0d15fa70f7ed25ec27a2f36fde34b4d2d88d91b`. The baseline fifth extraction/blocks/images/editorial context also exactly reproduce the original private fifth-test bundle. Machine-readable source hashes, output hashes, conformance counts and regression results are in `title-promotion-results.json`.


## Remaining limits and generalization assessment

This is a bounded correction to the promotion contract, not a complete editorial classifier. Alphabetic metadata in strong title typography can still imitate a legitimate title. Same-size singleton titles, titles followed by a separate-page opening, purely numeric or symbolic titles, weakly signalled subtitles and arbitrary title-only contents matching can remain pending or escape detection. False negatives are traded for explicit review, not silent deletion. EPUB navigation does not currently offer a human promotion editor; approval of a pending candidate needs future structured editorial refinement or source reconversion with reviewed evidence, not CSS/nav-label edits.

The engine supports at most two inferred levels; deeper source structure requires review. Standalone Roman headings still use the existing bounded sequence audit. Front/back matter identification is incomplete. Shared source-evidence parsing creates common-mode risk; independent authored oracles and adversarial mutations reduce but do not remove it. Five related private books and a small synthetic set are not a representative success rate across publishing formats.

EPUBCheck validates conformance only. Exact unchanged EPUB bytes in the earlier books demonstrate preservation relative to the approved baseline, not literary/editorial certification. No physical Kindle or Send to Kindle test is claimed; remaining inconclusive spacing/layout findings are retained. Full textual fidelity is not certified.
