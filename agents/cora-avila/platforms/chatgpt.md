# ChatGPT build guidance
This is build-time guidance, not an additional runtime authority.

Materialize Cora Ávila as the smallest suitable personal entry Skill using existing Notion access, web research and image capabilities when available. No separate Plugin is required merely to group already connected tools.

Runtime authority consists of ../core.md, ../persona.md and ../integrations/notion.md. Bundle faithful snapshots from one recorded source commit. Keep SKILL.md thin: discovery, loading these sources, tool discovery and operational bindings only. Do not duplicate behavior into the entry.

Suggested skill name: cora-avila.
Display name: Cora Ávila.
Trigger: interior-design consultation for the user's Room project, including furniture, composition, organization, setup cables and continuity of project decisions; explicit requests for Cora Ávila. Exclude merely discussing, inspecting or editing the agent itself.

Keep the user's Room URL and optional resolved subpage identifiers in private deployment bindings. Fetch live project context when relevant rather than embedding a frozen room inventory. Record canonical repository, commit, source paths and deployment status in the deployment manifest.

Prefer approved merged main for durable installation. A review-branch build requires the user's deliberate choice of a provisional version; label it provisional and do not treat installation as canonical approval. Never merge automatically. Report source creation, installation and runtime validation separately.

Validate loading and triggering, and exercise tests/acceptance.md with read-only consultation cases before claiming runtime behavior is tested. Do not modify Room during tests.
