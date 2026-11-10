# Book to EPUB → Booksmith

The capability is now [Booksmith](../booksmith/README.md). Its authoritative specification, quality contract, Python implementation, tests and platform guidance live in `skills/booksmith/`.

The historical command `python -m book_epub` remains available from this directory through a thin compatibility entry point. Install requirements from either directory. Keep both sibling directories when using this compatibility path; for standalone packaging use Booksmith directly.

This is the same capability, not a second artifact or deployment. Source history remains available through Git and [MVP PR #9](https://github.com/mainadapter/axiom/pull/9), pinned at `856e4a70e2312568161876cb3737ba4622432cb7`. Existing 0.1.0 conversion bundles can be refined without rewriting their models; new conversions use schema 2. The installed ChatGPT preview is not replaced by this repository change.
