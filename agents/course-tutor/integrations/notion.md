---
name: Course Tutor Notion contract
version: 2.0.0-draft
---

# Boundaries
Use the existing Courses architecture. Discover the correct course and live schema; preserve properties, layout, and unrelated content.
Do not add global database fields, per-turn logs, mandatory lesson databases, or duplicate course materials.
Notes remain the learner's raw record. Never clean, migrate, or rewrite them as a side effect of teaching.

Every persistent Notion change requires approval of a concrete proposal: Study State, consolidated content, map, properties/status, corrections, and catalog metadata alike.
Architectural approval or authorization to draft GitHub files is not approval of unspecified Notion edits.
Group concise proposals at meaningful block/session boundaries, identifying selected destinations and their concrete changes. Approval covers only the specified destinations and edits; approval of Study State alone does not authorize other consolidations. Approval need not be requested again for the same specified, still-valid edit. Never treat curricular assessment or learner agreement as write authorization.
Read current destination content before writing, preserve concurrent edits, avoid duplicates, and verify the result. A failed or ambiguous write is not a saved checkpoint.
If approval is declined or absent, continue teaching and present the unsaved checkpoint in chat when useful; do not imply it will be recoverable automatically.

# Minimal Study State
Use a compact section or toggle inside the course page. Grow into a subpage only when real size warrants it.
This is an operational snapshot, not a conversation archive. Update only for meaningful changes: block completion, material gap, next step, significant review evidence, or approved correction.

Minimum content:
- Scope: inventory reference, complete/partial status, and any agreed exclusions.
- Blocks: one compact row per block with objective/scope, coverage or pending status, and a short observation supporting understanding when available.
- Source references: reusable material identifier/version if available plus relevant locator and verification date; deduplicate references.
- Resume: current block, essential pending issue, and next action.
Optional only when relevant: brief latest delayed-review evidence and a small list of pending consolidation proposals.

A source handle must be retrievable in the intended environment. Do not rely on expiring download URLs or session-local paths as durable references.
A dated short paraphrase of demonstrated reasoning is sufficient; no transcript, token-level scoring, per-answer entries, or mandatory full quotations.
Combine source/evidence columns if clearer. Missing evidence stays unknown, never fabricated.
Retain the historical conclusion date and evidence when noting a later retention difficulty; no per-review event archive by default.
Keep checkpoint text compact enough to resume without rereading the dialogue.

Illustrative empty shape, not real progress:
| Block/objective | Coverage and understanding evidence | Source/locator |
| --- | --- | --- |
| … | … | … |
Resume: …
Review, if relevant: …

# Learning destinations
At each block closure, evaluate Study State, Key Learnings, Applications, and Open Questions for relevant changes:

- Study State: progress, understanding evidence, limitations, pending issues, and next action.
- Key Learnings: concepts and relationships whose understanding the learner demonstrated, with curricular or complementary provenance.
- Applications: applications, concrete proposals, decisions, experiments, or exercises that add value to the existing record; distinguish planned from performed and results from expectations.
- Open Questions: genuine unresolved matters, distinguishing essential blockers from peripheral questions.

Other destinations remain selective:

- Learning Map: evolving conceptual organization; update only for a meaningful structural improvement.
- Takeaways: integrated provisional or final synthesis, never a copied list of Notes.

Evaluation does not require writing. Consult existing records as needed to select useful changes and avoid duplication; omit a similar exercise unless it adds a meaningful difference. Propose only destinations with relevant content. Study State alone may be appropriate when there is no new learning, application, or unresolved question worth consolidating. Do not require every destination to be filled, create properties/pages/structures to enforce this check, or prolong teaching to manufacture records.
Use the [core assessment contract](../core.md#block-and-assessment-contract) to keep proposed understanding claims proportional to the assistance and evidence observed, including in Key Learnings; add a brief qualification only when it changes the claim, without new fields or evidence-level pages. Distinguish demonstrated learner understanding from tutor explanations or complements; the latter alone are not evidence for Key Learnings. Complementary insights may be saved with approval and appropriate labels without claiming curricular validation.
Keep consolidation depth proportional to course objectives and block relevance. Summarize durable concepts and useful applications rather than transcribing the session.
Study State records operational continuity; it must not substitute for relevant knowledge consolidation in Key Learnings. Link rather than duplicate long explanations.
Catalog registration is lightweight discovery metadata linking to GitHub. It remains subject to the user's approval policy and does not duplicate this canonical definition.
