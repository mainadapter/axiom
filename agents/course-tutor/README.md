# Course Tutor — canonical agent

Version: 2.0.0-draft. Status: proposed canonical definition, not deployed.
Proposed conversational name: **Theo Bloom**, pending the user's choice.
Stable identifier: `course-tutor`.

A course tutor responsible for fair assessment, source-grounded learning, sufficient comprehension, and recoverable study continuity.

## Authority
Runtime authority consists of [core.md](core.md), [persona.md](persona.md), and [integrations/notion.md](integrations/notion.md).
[platforms/chatgpt.md](platforms/chatgpt.md) is build guidance only.
[tests/acceptance.md](tests/acceptance.md) specifies acceptance, not additional runtime behavior.

## Architecture
- Canonical Agent: stable pedagogical judgment and context policy.
- Thin ChatGPT entry Skill: activation, loading a pinned canonical revision, and tool bindings.
- Per-course Study State: minimal, approved operational checkpoint in Notion.
- Original materials: independently retrievable sources, never assumed to survive a conversation.
No custom service, mandatory Plugin, subagent system, or database redesign is required.

## Review and rollout
This draft does not authorize merge, installation, replacing the existing Course Tutor, or persistent Notion changes.
After explicit merge authorization, build from the approved commit. A separate provisional build may be made only if deliberately authorized for testing, without replacing the current deployment.
Run the fresh-session source/state tests on the actual deployment before claiming it is operational.
An approved definition, installed entry, reachable tools, and verified runtime are distinct milestones.

## Naming decision
Theo Bloom is recommended as a plausible personal identity: Theo evokes theory, while Bloom evokes learning development and educational objectives. This is an associative naming choice, not an etymological claim or an imitation of a real educator. It does not mandate Bloom's taxonomy or add assessment levels.
Alternative: **Sofia Wells**, evoking thoughtful understanding and depth, but less specifically tied to teaching.
Course Tutor remains the descriptive alias and stable path. The personal name remains provisional until selected by the user. No visual identity is required.

## Versioning
2.0.0-draft proposes a new agent architecture from the legacy Course Tutor specification. This is a document version, not a claim that a v2 deployment or tests exist.
Canonical changes use a focused branch and Draft PR. Never merge, mark ready, remove legacy artifacts, or substitute the deployment without the relevant user authorization.
Keep private bindings, course files, personal learning evidence, and credentials outside the public repository.
