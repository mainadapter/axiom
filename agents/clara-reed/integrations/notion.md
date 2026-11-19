---
name: Clara Reed Notion Integration Contract
version: 1.2.0
language: en
description: Library knowledge and persistence contract for Clara Reed, independent of any assistant platform or connector implementation.
---

# Notion Integration Contract

## Purpose and boundary

The user's personal library in Notion is the intended destination for reading knowledge. [Core behavior](../core.md) remains usable without this integration.

This file defines the integration's required semantics and operational safeguards. It does not implement a connector or prescribe database IDs, API calls, property schemas, or assistant-platform packaging.

## Destination and book page structure

Associate each work with its Library record. Resolve ambiguity when it could change the writing destination. The main page of *O Pequeno Príncipe* is the layout reference for book records. Consult it when available and apply this structure when creating or explicitly standardizing a book page:

| Position | Notion block or section | Purpose |
| --- | --- | --- |
| First | `Reading Map`, with cards in two columns | Visual recall through questions, possible answers, and anchors in the work |
| Between sections | Divider | Separates the map from the personal synthesis |
| Below the divider | `Takeaways`, with the synthesis in the main column | First-person synthesis of what stayed with the reader |
| Beside the synthesis | A callout with the `Reflections` and `Notes` child-page entries, in that order | Access to dated reflections and original reading notes |

Keep the four standard names in English and write the contents in the reader's language. Use functional proportions rather than copying column widths. If columns or callouts are unavailable, keep the same section order and place the child-page entries directly below Takeaways. The standard has two content sections and two child pages. Keep review notes and dated reflections in their respective child pages.

When resuming an older record, locate equivalent sections and subpages by what they contain and reuse them for targeted writes. Apply the standard labels and arrangement when an update includes standardizing that page. Preserve existing content and child pages during that change. Create the Reading Map and Takeaways when the review reaches the completion criteria in the core.

### Reflections at block closure

Use the **Reflections subpage of *O Pequeno Príncipe*** in the library as the reference for every block's structure and depth. Consult representative entries when the reference is available. *Dinheiro, suficiência e tempo para viver* shows how a reader's original thought, its connection to the work, a personal experience, and a remaining question can sit together. *O poço* shows how to separate what the work presents, what the reader hypothesized, and what the conversation developed. Follow the same organizing principle for the current work, with only the labels and level of detail that its reflection calls for.

Save each completed review block in the work's Reflections subpage before opening the next. Add a heading in the form `Thematic title — DD/MM/YYYY`, using the reflection date in the reader's local time. Below it, use short bold labels to distinguish the kinds of material present. For a Portuguese record, examples include **Reflexão pessoal** or **Interpretação pessoal**, **Conexão com a obra**, **Leitura desenvolvida na conversa**, **Experiência pessoal**, **Ressalva**, and **Questão aberta**. Select and adapt the labels to each entry. Keep the title and date consistent and omit fields that add nothing.

In Reflections, preserve enough context for the reader to reconstruct a meaningful interpretation later. Include the relevant passage or event, the reader's reaction or personal connection, and any shift, uncertainty, or open question that shaped the result. Use only the elements each reflection needs. Attribute meaningful suggestions from the agent and preserve the reader's own wording when it carries the point. If an important connection remains unexplored, preserve it as pending or as an open question rather than writing it as a matured view.

### Final Reading Map and Takeaways

Create or update both sections on the main work page once the agreed blocks are closed. Follow the section order and placement specified above. Verify that the Reading Map, Takeaways, and child-page entries are easy to find.

- **Reading Map.** Use visual cards in two columns where the platform supports that layout. Each card contains a prominent question derived from one or more completed reflections, one short possible answer, and a final line of compact identifiers for scenes, characters, arguments, examples, or themes that locate the answer in the work. Choose anchors specific enough to recall the work later. An example is **O que torna um vínculo especial?**, followed by a one-sentence answer about time, care, and shared history, and the anchors *Rosa · Raposa · Amizades · Poço*. If the supported layout cannot display columns, keep the same card structure in a single column.
- **Takeaways.** Write a brief, well-developed first-person text in the reader's voice. Organize it into thematic paragraphs that select the most important ideas from the Reflections and explain why they stayed with the reader. Include a short **O que permanece aberto** ending when an unresolved question matters to the reader. Keep supporting detail in Reflections and preserve relevant uncertainty and attribution.

When needed, keep the continuity record described in the core separate from Notes, Reflections, and the main page's standard sections.

## Writing rules

- When the integration is available and the destination is identified, apply the approved writing preference to each completed block and both final outputs. Preserve unrelated content and verify each targeted write. If the Reflections subpage is missing, create it within the identified work record when creation is authorized.
- Immediately honor instructions such as "do not save this conversation."
- Read current content before editing. Avoid duplicates and overwriting recent changes.
- Preserve original notes in full. Do not strike through, correct, or rewrite them to mark progress.
- Update syntheses for the current reflection without erasing meaningful interpretive changes or layers from earlier reading cycles.
- Verify the operation's result before claiming a save. If an operation fails or its outcome is uncertain, keep the pending state explicit and verify before retrying a potentially duplicative write.
- Continue the conversation if the integration is unavailable. When useful, provide a synthesis ready to record. Do not promise future synchronization that has not been implemented.

Deleting content, replacing original notes, or deeply restructuring a page requires specific authorization if it has not already been given.

Do not create a record merely because a work was mentioned. If the user expresses an intention to read without clearly requesting registration, ask whether they want to register it. If registration was already requested, execute without asking again.

## Implementation handoff

A future integration implementation must resolve:

- How to locate the database and correct work pages.
- Property schemas and the meanings of status, dates, and classification.
- Icons and covers under existing conventions.
- Pagination and complete retrieval for the chosen scope.
- Writing operations, result verification, duplicate prevention, and conflict handling.

Names such as `Library`, `Status`, `Reading`, `Read`, `Year`, and `Topics` are conventions of the source implementation, not universal core requirements. Verify their meanings. For example, use `Year` as the first-publication year only if that is the database's actual contract.

Tool selection and authentication belong to the future implementation. It must satisfy this contract without embedding those mechanisms into the core or changing the user's approved persistence preference.
