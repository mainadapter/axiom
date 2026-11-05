# ChatGPT implementation guidance

Build-time only. Do not load this file as competing runtime behavior.

## Smallest implementation
Materialize the canonical Agent as a thin personal entry Skill using existing authenticated Notion and file-access capabilities.
A Plugin is optional if the target surface needs one for distribution/bundling. Do not add a service, background execution, or subagents by default.
Do not assume the term Agent grants memory, tools, persistence, or access to earlier attachments.

## Build contract
Use one explicit canonical commit. Runtime sources:
- core.md
- persona.md
- integrations/notion.md
Bundle faithful snapshots when required by the native creator. Record commit and provenance together.
The entry should cover activation, source loading, actual tool discovery and private bindings; do not independently rewrite or duplicate the behavior.
Trigger for tutoring a course, resuming study, evaluating understanding, or auditing course consolidation. Do not trigger merely to administer a course database or edit this agent.
Use Theo Wells as the display and conversational name. Retain Course Tutor as an invocation alias and course-tutor as the stable repository identifier.
Use the platform-native creator when materialization is authorized. Preserve existing app connections. Keep workspace IDs and credentials in private deployment bindings, outside the public canonical repo.

## Runtime capability requirements
The actual entry must be able to:
1. Discover the selected course and read approved state.
2. Locate and open original material in the available attachment or durable file store.
3. Read relevant text and inspect visuals when required.
4. Return source locations supporting curricular judgments.
5. Prepare and, with user approval, perform and verify focused Notion writes.
6. Repeat source/state retrieval in a fresh session without old conversation history.

If a dependency is unavailable, expose that precise limitation and use the defined complementary-discussion behavior. Do not label the deployment fully validated.
Durable references must resolve outside the initial session. Search available stores before asking for another upload; do not assume a file's name uniquely identifies its revision.
Existing read access in the architecture-design session does not prove the new Skill works.

## Release gates
Canonical review and Draft PR do not authorize installation or substitution.
Prefer approved main for durable deployment. An explicitly authorized provisional deployment must identify its review commit and coexist without replacing the current tutor.
Acceptance requires tests/acceptance.md on the actual Skill, including new-session source/state recovery.
Report separately: specified; packaged; installed; tool access verified; fresh-session recovery verified; pedagogical tests passed.
Tests awaiting materials, approval, or a fresh session are blocked/not run, never passed.
