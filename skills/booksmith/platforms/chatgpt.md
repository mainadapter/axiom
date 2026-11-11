# Booksmith — ChatGPT materialization — build guidance only

Create the smallest personal entry Skill after canonical review. Do not install it merely because a draft implementation exists. An explicitly requested preview must identify its unmerged source SHA as provisional.

Use the current native skill creator. Runtime authority: `skill-spec.md`, `quality.md`, and `book_epub/` from one pinned revision, plus pinned dependencies. Bundle faithful copies and an origin manifest. Keep the entry focused on invocation, source loading and executing the local module. Do not duplicate policies or create a second behavioral definition. README.md provides CLI operation; this adapter is not runtime authority.

Reuse the host's file access and Python execution. Verify pdfplumber/pypdf, Pillow, pypdfium2 rendering and local Java/EPUBCheck availability. Missing EPUBCheck must downgrade conformance evidence, never trigger a fabricated pass. No conversion-time GitHub, Notion, email or Amazon connection is needed. Deliver output using the host's private artifact mechanism; preserve the entire revision bundle for continuation. Uploads to ChatGPT do not imply permission to send books to third parties.

Validate trigger/non-trigger examples in the spec, a real simple PDF conversion, a problematic source, and a spacing/navigation refinement preserving content bytes. Report separately canonical state, created package, installed state and runtime-tested behavior. Test native packaging and dependency availability at materialization time; unit tests of the core are not a native deployment test.

Materialize the canonical Booksmith directory only, retaining Book to EPUB as a discovery alias and python -m book_epub as the executable entry. Do not create duplicate installed capabilities. New schema-2 bundles carry embedded image assets; include complete models in private delivery. Validate cover/internal image handling, nested navigation, typography and a historical schema-1 refinement. Updating this adapter does not authorize replacing the current deployment.
