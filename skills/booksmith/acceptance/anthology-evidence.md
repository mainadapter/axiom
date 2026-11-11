# Booksmith 0.2.0 — anthology consolidation acceptance

Executed 2026-11-10 on the PR #9 branch. This supplements `booksmith-evidence.md`; it does not replace historical evidence or update the installed ChatGPT materialization. No private book bytes, model, bundle or extracted narrative are committed.

## Root cause and change

Local heading inference ranked font sizes relative to the largest non-Roman heading anywhere in the book. A larger cover/title-page heading therefore demoted every narrative title to level two. The packaging correctly serialized that incorrect model: author, city/date and index were false structural entries, while narrative titles and Romans shared a level under a prefatory parent. Valid anchors and EPUBCheck did not expose this semantic defect.

The deterministic context pass now corroborates same-style titles immediately preceding I against recurring I/II narrative runs. It promotes narrative parents independently of cover size. Earlier sparse pages with an ordered echo of those titles confirm front matter; an additional cover occurrence of a story title does not invalidate the contents echo. Terminal uniformly smaller-font publishing pages with rights and ISBN/CIP identifiers are separated from the last narrative unit. These are bounded source-evidence rules, not a universal document model or book-title allowlist.

Model roles and source IDs retain the basis for separation. The source-context audit separately checks parent levels, Roman subordination/sequence and confirmed front/back-matter roles. Proven model contradictions block publication; unexplained sequences and uncertain front matter require review. Structured findings include source IDs, pages, block IDs and a reason; Markdown highlights editorial findings before generic diagnostics. Package navigation validation still checks the serialized hierarchy and destinations, without claiming editorial correctness merely from working links.

## Independent editorial oracle

Private textual PDF: *A Espada do Destino*, 232 pages, two raster occurrences. Source SHA-256: `a66781bdf21e4655ec577cc096608b282bd08ca49a01e523f5dacd214b330861`.

| Narrative unit | Source start page | Roman subdivisions | Result |
| --- | --- | --- | --- |
| O Limite do Possível | 4 | I–VIII | Main heading + subordinate entries; own XHTML |
| Um Fragmento de Gelo | 54 | I–IX | Main heading + subordinate entries; own XHTML |
| O Fogo Eterno | 81 | I–IV | Main heading + subordinate entries; own XHTML |
| Um Pequeno Sacrifício | 114 | I–X | Main heading + subordinate entries; own XHTML |
| A Espada do Destino | 152 | I–VIII | Main heading + subordinate entries; own XHTML |
| Algo Mais | 194 | I–IX | Main heading + subordinate entries; own XHTML |

Eight content XHTMLs: one front-matter file (cover, title page, original index), six narrative files and one publishing-information file (pp. 231–232). Navigation contains 56 working destinations: two matter entries, six parents and 48 children. Author/city/index are preserved text, not narrative headings. The printed index is preserved as text; the EPUB navigation is independently linked. Front/back matter do not yet carry dedicated `epub:type` semantics; internal front-matter page breaks are not reconstructed.

The versioned `check_anthology.py` oracle asserts literal expected headings/levels, counts, source pages, eight spine documents, actual nested XML/links, narrative distribution, text/order/image accounting and real EPUBCheck results. Its expectations do not call reconstruction or packaging helpers. The authored generic six-story fixture uses different titles, larger prefatory fonts, a collection title duplicated as one story, and 48 sections. Negative tests mutate parent/front-matter roles and introduce a Roman gap. A terminal credits fixture covers final publishing information.

## Executed validation

- Complete suite: 62 tests, no failures, errors or skips, with real EPUBCheck 5.3.0. The historical refinement test was also rerun after strengthening assertions for all non-CSS/non-nav member bytes and unchanged schema-1 model bytes.
- Original authored editorial acceptance rerun: 14/14 expected blocks, two images, five headings at expected levels, EPUBCheck pass; refinement changes CSS only and preserves model bytes. Previously approved cases remain covered in the complete suite. The earlier private 190-page source was not rerun in this revision.
- Full private anthology reconverted from the PDF by `python -m book_epub` in `skills/booksmith/`, with the legacy directory absent. Source ledger and image assets/provenance equal the previous bundle; all retained textual characters and their order are unchanged. Exact serialized block text/order and styled characters pass; both image occurrences and their PNG bytes pass source/package accounting.
- Narrative character distribution: 156622, 84221, 106010, 124239, 123826, 109198. No single XHTML holds the bulk of the collection.
- EPUBCheck 5.3.0: zero fatal/errors/warnings/usage. Official distribution SHA-256: `6c07e68584b2e2ce2f89fe06e1246dfead3eb36b46b340e7d93524f29dcff6c5`.
- EPUB SHA-256: `c15b84b2b52986720902eef1a56f25c96d16f540b061fc8434329d46ecab32dc`. Rebuilding all EPUB members from the retained model reproduces the same member bytes. Existing source-to-model/EPUB determinism regression also passes.
- Python 3.12.14, Java 21.0.13; pdfplumber 0.11.9, pypdf 6.21.4, pdfminer.six 20251230, Pillow 13.0.0, pypdfium2 5.14.0. Engine remains 0.2.0 in this unmerged PR; implementation SHA-256 `d722bd18022d0ffbb20db519b82e381d8b84834e3b08fe03b0722ffa045f73e2` distinguishes this revision from the installed build.
- Independent inspection of the source PDF and actual EPUB confirms six story starts, all 48 Roman subdivisions, corrected prefatory/final separation, link destinations and serialized text/order. It does not constitute a full reading or visual equivalence guarantee.

Result remains **Revisão recomendada**: uncertain hyphens, paragraphs, quotations/indents, small text and extractor differences persist. In particular, independent extraction disagrees on p. 231; no loss was proved, and no text was generated to resolve the difference. Image hashes/accounting preserve the prior visible crops but do not certify visual identity against a second renderer. Physical Kindle, Send to Kindle, landscape and exhaustive visual inspection were not tested. The three quality states and evidence requirements are unchanged.

## Legacy directory decision and compatibility

Repository-wide tracked/hidden-file search found no active script, automation, installation instruction or materialization depending on the legacy directory. Its five tracked files were only `.gitignore`, a redirect README, a module-path shim and two dependency redirects. All five are removed; only `skills/booksmith/` implements this capability.

Remaining old-path references are historical provenance in README/evidence and `git show 856e4a70…:skills/book-to-epub/book_epub/...` in the compatibility test. This reads the pinned historical Git object; it does not access or require a legacy directory in the working tree. The historical branch name also remains intentionally unchanged for PR continuity.

The real 0.1.0 engine generated a schema-1 bundle from its pinned commit; the canonical current engine refines it without changing model or non-CSS/non-nav members, with actual EPUBCheck. `python -m book_epub` works in the canonical directory, and Book to EPUB remains a discovery alias in README, specification and platform guidance. No second installation or path shim is needed. Earlier schema-2 bundles remain loadable; if new source-context checks prove an editorial contradiction, presentation refinement withholds the defective EPUB and requires source reconversion instead of silently migrating its model.

Reproduce from `skills/booksmith/`:

```bash
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
PYTHONPATH=. python acceptance/run_editorial.py /path/NEW_OUTPUT /path/epubcheck.jar
python acceptance/check_anthology.py /path/NEW_PRIVATE_BUNDLE /path/PREVIOUS_PRIVATE_BUNDLE
```

PR #9 stays draft, on `feat/book-to-epub-mvp`, without merge. Installed Skill remains at its previously materialized source `2ff1f030252af85aca16f5f8793994e069ca7ae3`; this revised canonical source awaits the user's review before any deployment update.
