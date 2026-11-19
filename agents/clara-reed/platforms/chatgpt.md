---
platform: ChatGPT / OpenAI
version: 1.0.0
status: materialized as personal Skill; representative conversation behavior validated; broader Notion and continuity validation remains deployment-specific
last_reviewed: 2026-10-14
canonical_sources:
  - ../core.md
  - ../persona.md
  - ../integrations/notion.md
architectural_reference:
  - ../../../core.md
  - ../../../platforms/chatgpt.md
  - ../../../docs/architecture.md
verify_against:
  - https://learn.chatgpt.com/docs/skills-and-plugins
  - https://learn.chatgpt.com/docs/build-skills
  - https://learn.chatgpt.com/docs/build-plugins
---

# Clara Reed — ChatGPT Adapter

## Scope and authority

This adapter defines ChatGPT-specific materialization, activation, source loading, tool binding, deployment limitations, creation handoff, and validation.

The canonical definition remains:

- [Core](../core.md): behavior, context policy, continuity, quality, and acceptance scenarios.
- [Persona](../persona.md): identity and interaction style.
- [Notion integration contract](../integrations/notion.md): persistence semantics and authorization.

This adapter does not restate or replace those sources. If a platform limitation prevents compliance, disclose the limitation and delimit the implementation rather than silently changing the canonical definition.

Axiom on `main` supplies architectural guidance, not additional Clara Reed behavior. Record the inspected Axiom revision when materializing a release.

## Recommended initial materialization

Materialize Clara Reed as a personal ChatGPT entry Skill with access to the existing Notion app connection. If the native creation mechanism benefits from wrapping that Skill and connection in a Plugin, that packaging is acceptable, but it is not part of Clara Reed's canonical identity.

Clara Reed remains an agent in the canonical architecture. Plugin and Skill are platform packaging mechanisms.

The entry Skill owns only:

- Discovery metadata and activation boundaries.
- Instructions for loading the canonical sources.
- Operational access to available tools.
- Platform-specific execution and deployment handoff.

Do not split the core's conceptual capabilities into separate Skills or agents unless a demonstrated platform requirement makes that necessary.

Use the existing Notion connection before considering custom integration infrastructure. Do not create an MCP server or API service when available tools satisfy the contract.

A ChatGPT Project may optionally organize conversations and reading materials. It must not become another maintained definition of the agent. A custom GPT, Workspace Agent, or API application is not the default target for this implementation.

## Activation

Support explicit selection of Clara Reed through the native skill or plugin picker.

Discovery metadata should identify reading discussion, reflection, resumption, and consolidation as relevant contexts, with scope derived from the core. It must not activate merely because a book is mentioned in an unrelated task.

Requests to inspect, edit, or implement Clara Reed itself are configuration work, not requests to begin a reading conversation.

At activation, load the required sources before providing a substantive Clara Reed response. Continue applying them while the conversation remains within that scope.

Do not assume installation guarantees activation in every conversation. Validate both explicit selection and intended implicit matching on each supported surface.

## Canonical source loading

Load the complete core and persona at the start of an activated session. Load the complete Notion integration contract before retrieving or persisting library content.

Do not rely on filenames, metadata, excerpts, or an instruction to “follow the linked documents” as evidence that their contents have been loaded.

Make all three sources directly addressable from the entry Skill. Preserve their relative-link relationships or provide an explicit resource mapping.

For an autocontained installation, package unmodified snapshots from one identified canonical revision. These are deployment resources, not independently maintained definitions:

- Record source paths and the source revision or content hashes.
- Update behavior only in the canonical sources.
- Regenerate deployment resources after approved source changes.
- Never edit packaged snapshots as a separate behavioral branch.

Do not promise automatic synchronization with GitHub unless it has been implemented and verified. Referencing `main` alone does not establish which version an installed package contains.

If required sources cannot be loaded, identify the missing material. Do not substitute a legacy Skill, reconstruct the definition from memory, or claim full activation.

After context loss, recover the required sources and applicable persisted state before relying on them.

## Notion operational binding

The [integration contract](../integrations/notion.md) remains authoritative. This implementation supplies the tool-level binding required to execute it.

During setup, verify:

- The connected Notion workspace and accessible library location.
- Database or data-source identifiers and the method for resolving work records.
- Existing property meanings and the target book's sections and child pages. Resolve the *O Pequeno Príncipe* reference through the connected library and follow the layout in the integration contract.
- Available search, fetch, pagination, creation, update, and verification operations.
- Any restrictions affecting complete retrieval or reliable writes.

Keep workspace identifiers, schema mappings, and connection details in deployment configuration or retrievable setup context. Do not add them to the canonical sources. Authentication and credentials remain with the platform's connection mechanism.

Bind tool operations to the contract's requirements for current-content reads, preservation, duplicate prevention, conflict handling, result verification, and uncertain outcomes. Refresh any saved Notion binding that describes an older layout. Keep the layout rules in the integration contract and the location and connector details in the binding.

Use targeted updates when supported. If the available tool can only replace broader content, determine whether that operation can preserve the contract before using it.

The approved persistence preference is inherited from the contract. Do not introduce routine conversational approval for each consolidation. Platform-enforced confirmations and access restrictions still apply; disclose any resulting limitation without rewriting the preference.

If Notion is unavailable or only partially accessible, apply the fallback defined by the canonical sources. Installation alone does not establish successful integration.

## Platform limitations

Validate capabilities in the actual account and target surface. Availability in Chat, Work, or another deployment must not be inferred from availability elsewhere.

Account permissions, app authorization, tool access, and plugin installation are separate prerequisites. Packaging does not grant access to Notion content or additional write capabilities.

Treat ChatGPT history, memory, and Project context as supplementary context. They do not replace the retrievable continuity mechanism specified in the core.

Skill selection and instruction following are model-mediated. Validate behavior through representative conversations rather than treating successful installation as proof of fidelity.

This deployment does not imply background execution, scheduled synchronization, or autonomous work between conversations.

Revalidate this adapter when native creation mechanisms, source loading, permissions, or Notion tool behavior materially change.

## Handoff to native creation

Prefer the current native Skill Creator for the entry Skill and use the existing Notion app connection rather than recreating the integration.

Provide the creator with:

- The three canonical sources as authoritative inputs.
- This adapter as the build-time implementation boundary.
- The selected source revision and resource mapping.
- The intended ChatGPT surfaces.
- Verified Notion capabilities and unresolved setup requirements.
- References to the core's acceptance scenarios and the validation plan below.

Instruct the creator to generate the minimum required packaging. It must not summarize the canonical definition into a competing prompt, invent persona traits, or add a new reflection workflow.

Let the native creator own current metadata, manifests, installation procedures, and package-format details. Keep those volatile mechanisms out of the canonical sources.

An existing Reading Companion or Clara Reed installation is migration evidence, not an additional behavioral authority. Inspect it before replacement, identify any operational configuration worth retaining, and avoid leaving competing versions active.

Review the generated resource loading and integration binding before relying on the installation. Report separately whether the package was created, installed, connected, and validated.

## Validation plan

### Source and packaging fidelity

- Confirm every canonical resource matches the selected revision.
- Check that all links or resource mappings resolve after installation.
- Verify the entry Skill loads the required sources in full.
- Confirm generated instructions contain adaptation only, without a second definition of behavior or persona.

### Activation and conversation behavior

- Test explicit activation in a fresh conversation.
- Test relevant implicit activation and unrelated non-trigger requests.
- Execute behavioral acceptance scenarios from the core as needed without replacing their expected outcomes with adapter-specific criteria.
- Include a multi-turn conversation to check continued adherence after initial activation.
- Include a weak or poorly supported interpretation to verify constructive intellectual resistance rather than automatic agreement.

### Notion integration

Use a designated test record for write validation.

Verify record resolution, schema mapping, complete retrieval across pagination, targeted updates, preservation, result verification, and duplicate prevention. Check that the Reading Map, divider, Takeaways, and child-page entries render in the intended order, including the documented fallback if columns or callouts are unavailable.

Exercise unavailable access, ambiguous destinations, uncertain write outcomes, and intervening edits. Assess results against the integration contract.

### Continuity and deployment

Resume in a fresh conversation using persisted material. Verify that continuity does not depend on the original chat remaining available.

Test every surface claimed as supported. Record source revision, validation date, observed results, and limitations. Documentation review alone does not establish runtime validation.

A deployment is ready only when the applicable acceptance scenarios pass and any remaining platform limitations are explicit. Resolve implementation failures in the adapter or packaging before proposing changes to the canonical definition.
