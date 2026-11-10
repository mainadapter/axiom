# Book to EPUB — MVP

Canonical standalone Skill specification and portable Python core. Native ChatGPT installation is deliberately deferred until review. See [skill-spec.md](skill-spec.md) for behavior, [quality.md](quality.md) for the explicit quality contract and [platforms/chatgpt.md](platforms/chatgpt.md) for materialization.

## Run

Python 3.11+ (tested on 3.12); from this directory:

```bash
python -m pip install -r requirements.txt
python -m book_epub convert /path/book.pdf /path/book-v1 --title 'Book title' --language pt-BR --profile kindle --epubcheck-jar /path/epubcheck.jar
python -m book_epub refine /path/book-v1 /path/book-v2 --paragraph-gap 1.0 --epubcheck-jar /path/epubcheck.jar
python -m book_epub refine /path/book-v2 /path/book-v3 --labels /path/labels.json --epubcheck-jar /path/epubcheck.jar
```

`labels.json` maps chapter starting block IDs (from model.json) to nonempty display labels, e.g. `{"b1":"Introdução"}`. It changes only the TOC label, not the author's heading. Destination repair regenerates the TOC from the original model. `--indent` and `--paragraph-gap` accept finite em values 0–3; no arbitrary CSS is accepted in the MVP. Both profiles currently share conservative CSS; `kindle` expresses the intended delivery target, not verified Amazon acceptance. The CLI does not send anything externally.

Exit codes: 0 approved, 1 review recommended, 2 intervention needed or invalid invocation. Always read report.md/report.json; a nonzero quality exit may still produce a usable EPUB. Blocking extraction produces reports and provenance without an EPUB. Exceptions before source access/output creation appear as CLI errors.

New output directories contain `book.epub` when viable, `model.json`, `report.json`, `report.md`, `manifest.json`. Preserve all files for refinement; do not hand-edit them. Hashes detect accidental changes, not malicious replacement of an entire bundle. Original PDFs are not copied; retain them privately for source review. Reports/model contain book text. Never publish them with the code.

Reproducibility: stable IDs, ordered JSON, fixed ZIP timestamps and a deterministic package modification epoch produce identical EPUB/model bytes for the same source bytes, metadata, options and dependency versions. The package epoch is a reproducible-build convention, not the source publication date. Runtime reports record Python/library versions and EPUBCheck's structured evidence; temporary paths/timings inside external reports can differ. No private absolute source path is embedded.

## Tests

```bash
python -m pip install -r requirements-dev.txt
EPUBCHECK_JAR=/path/epubcheck.jar python -m unittest discover -s tests -v
```

For the complete tested dependency set, use `requirements-lock.txt`. It records transitive versions as well as test dependencies.

Obtain EPUBCheck from its official release distribution, keeping the JAR and lib directory together. Java is required. Tools are not auto-downloaded by conversion. With no JAR, the explicit real-approval integration test is skipped; do not report full conformance validation from that run. Unit tests still exercise missing-validator behavior.

Fixtures are generated from original authored text at test time. They cover simple chapters, cross-page paragraphs, ambiguous/evidenced hyphens, repeated margins, notes, scans, images, columns, blank/malformed PDFs, corrupted package content/references, output reproducibility and incremental invariants. No copyrighted book is committed. Additional real-world samples and physical Kindle testing remain a release-review activity; synthetic coverage alone is not a general fidelity guarantee.

## Design choices and next increments

pdfplumber supplies geometry; pypdf offers an independent text path. Standard XML/ZIP is sufficient for the small fixed EPUB layout; a broader EPUB library adds little to this template. EPUBCheck checks external conformance. Calibre can assist future differential conversion/preview but is not a required dependency.

Rendering is separate from extraction and validation. Refinement copies existing chapter bytes and changes CSS/nav only. It cannot erase extraction findings or change paragraphs. Source-backed paragraph editing, emphasis/quotes, linked notes, images, complex layouts and local OCR are later focused increments with their own regression fixtures.

Primary references: [pdfplumber](https://github.com/jsvine/pdfplumber), [pypdf extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), [EPUB 3.3](https://www.w3.org/TR/epub-33/), [EPUBCheck](https://www.w3.org/publishing/epubcheck/docs/getting-started/).

Acceptance evidence and reproducible public-text sampling: [acceptance/evidence.md](acceptance/evidence.md). These real literary excerpts are re-typeset under controlled layout; they do not establish general performance on independently published PDFs.
