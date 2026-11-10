# Booksmith

Reconstruct conventional textual books from PDF into faithful reflowable EPUB 3, preserve relevant typography and raster images, and refine presentation incrementally. **Book to EPUB** is the historical name and discovery alias.

Runtime authority: [skill-spec.md](skill-spec.md), [quality.md](quality.md), `book_epub/` and pinned dependencies. [platforms/chatgpt.md](platforms/chatgpt.md) is build guidance. This repository change does not replace the installed ChatGPT preview.

## Run

Python 3.11+; from `skills/booksmith/`:

```bash
python -m pip install -r requirements.txt
python -m book_epub convert /path/book.pdf /path/book-v1 --title 'Book title' --language pt-BR --profile kindle --epubcheck-jar /path/epubcheck.jar
python -m book_epub refine /path/book-v1 /path/book-v2 --paragraph-gap 1.0 --epubcheck-jar /path/epubcheck.jar
python -m book_epub refine /path/book-v2 /path/book-v3 --labels /path/labels.json --epubcheck-jar /path/epubcheck.jar
```

`labels.json` maps existing navigation block IDs to nonempty display labels, e.g. `{"b1":"Introdução"}`. Chapter and subordinate-heading IDs are in model.json. This changes navigation labels only, not the author's headings. `--indent` and `--paragraph-gap` accept finite em values 0–3. No arbitrary CSS or textual patches are accepted. The generic and Kindle profiles share a conservative responsive template; Kindle is a target, not evidence of Amazon/device testing. No automatic network upload occurs.

Exit codes: 0 approved, 1 review recommended, 2 intervention necessary or invalid invocation. Read report.md/report.json. Review can produce an EPUB. Blocking source or serialized-package findings withhold the EPUB and retain diagnostics; a rejected package's hash is recorded.

Each new revision directory contains `book.epub` when viable, `model.json`, `report.json`, `report.md`, `manifest.json`. The schema-2 model embeds image payloads and full source provenance; keep the entire bundle privately. Retain the original PDF separately. Reports/models contain book text and images: never publish user conversion bundles with this code.

## Reconstruction and limits

Page-local geometry and document-wide body typography support paragraph inference. A small-font epigraph cannot redefine a recurring body size actually present on the same page. Heading candidates require isolation and positive structure; dense prose and dialogue provide counter-evidence. Source-only facts in `book_epub/evidence.py` combine repeated label families (Portuguese/English, digits, written cardinal/ordinal one through ten, Roman numerals), recurring isolated title styles, and original contents echoes. Explicit structure takes precedence over local font-size rank; ambiguous standalone typography requires review. Document-wide repeated title/roman cycles corroborate parent headings independently of larger cover typography. An ordered source-contents echo on preceding sparse pages confirms front matter, kept in its own XHTML with a single navigation entry. Terminal publishing information receives a separate XHTML only when smaller-font terminal pages combine rights and catalogue identifiers. Level-one headings start chapters; level-two headings appear in nested navigation. Ordinary paragraph indents and dash-led dialogue turns receive distinct treatment. Font-name-backed bold/italic spans and textual section separators survive in XHTML. Ambiguities are reported; exact text agreement does not prove editorial structure.

Raster occurrences become PNG crops of their **visible PDF appearance** at 144 DPI, with original/visible coordinates, source object, transform, dimensions, source-relative percentage display width and hash. The long side is capped to one content width for conservative portrait presentation; landscape and physical-reader layouts remain unverified. This intentionally preserves clipping, masks and orientation rather than pretending the raw embedded image is always equivalent to what the page shows. Source encoding/resolution and accessibility semantics are not guaranteed. The first unambiguous image-only cover receives cover-image metadata. Capture failures, image/text overlaps, overlapping raster compositions and possible internal scans remain blockers; lateral relationships require review. No OCR, advanced tables, formulas, arbitrary vector reconstruction or complex layout support is claimed.

Independent extraction checks text and word spacing. Separate accounting checks source lines, image occurrences, styles and serialized EPUB content. EPUBCheck must execute successfully for approval. Missing EPUBCheck requires review; it is not a fabricated pass or a proven package failure. Java plus the official EPUBCheck release and its lib directory must be installed separately; conversion does not download tools.

Markdown diagnostics group occurrences with counts, actions and three representative page/block references. JSON retains the complete ledger. A dedicated editorial section highlights source-context contradictions (blocking), suspicious heading density, uncertain titles, source-contents divergences, unexplained Roman sequences or uncertain front matter (review), independently of link integrity. The auditor re-reads the source-line ledger and ignores stored heading evidence and stored editorial predictions. Source parsing is shared, so common-mode parser defects remain possible; authored oracles and deliberate model mutations complement, rather than replace, source inspection. Prior schema-2 bundles with a proven editorial contradiction must be reconverted from source rather than repaired through presentation-only refinement. Uncertain hyphens remain unchanged; no translation, correction, modernization or generative rewriting occurs.

## Refinement and compatibility

Refine changes CSS/navigation only, preserving the model and every other EPUB member byte for byte, including images, chapters and OPF. Earlier source findings persist. Every revision has fresh checks, hashes and a parent link.

Historical schema-1/engine-0.1.0 bundles are supported for presentation refinement without model migration or source re-extraction. Their existing limitations remain. Other unknown schemas fail explicitly. The command `python -m book_epub` runs from the canonical directory alone. The legacy directory was removed after a repository-wide reference audit; no live scripts, workflows or deployment instructions depended on it. Only historical Git paths remain for provenance and the pinned 0.1.0 compatibility test. The alias Book to EPUB is retained in this specification and platform packaging.

Git preserves the move from `skills/book-to-epub/`; MVP provenance is [PR #9](https://github.com/mainadapter/axiom/pull/9), commit `856e4a70e2312568161876cb3737ba4622432cb7`.

## Reproduce validation

```bash
python -m pip install -r requirements-dev.txt
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
PYTHONPATH=. python acceptance/run_editorial.py /path/NEW_OUTPUT /path/epubcheck.jar
```

Use `requirements-lock.txt` to reproduce all tested transitive versions. Real-conformance tests are explicitly skipped without EPUBCHECK_JAR; such a run must not be described as complete validation. The historical compatibility test reads the pinned MVP commit from the Git checkout and fails if unavailable; use a full repository checkout for the suite.

Stable IDs, ordered JSON, fixed ZIP timestamps and pinned dependencies make identical EPUB/model bytes reproducible for identical source bytes/options. Runtime reports record implementation and library versions. External checker paths/timings can vary. Hashes protect against accidental bundle changes, not malicious replacement of all files.

Tests use independently authored expected text and structural assertions, complemented by deliberate text/image/style/navigation corruption. [Editorial acceptance](acceptance/booksmith-evidence.md) records executed results and limits. [Historical MVP evidence](acceptance/evidence.md) belongs to version 0.1.0 and must not be read as results of the current engine. The private anthology oracle can be rerun with `python acceptance/check_anthology.py /path/NEW_BUNDLE /path/OLD_BUNDLE`; it checks literal expected headings/levels, source pages, eight XHTMLs, nested navigation, text/image accounting and the real EPUBCheck report. It never derives its expected structure from the implementation. Public-text sampling remains available in `acceptance/run_public_texts.py`.

Primary technical references: [pdfplumber](https://github.com/jsvine/pdfplumber), [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), [EPUB 3.3](https://www.w3.org/TR/epub-33/), [EPUBCheck](https://www.w3.org/publishing/epubcheck/docs/getting-started/).

See `acceptance/novel-evidence.md` for the third private-source regression, generalization boundaries and commands. No per-book names, source pages or IDs occur in runtime classification. Source-specific acceptance oracles stay outside the motor. The installed materialization is unchanged.
