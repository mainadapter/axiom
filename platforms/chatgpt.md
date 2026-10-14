---
platform: ChatGPT / OpenAI
version: 2.3.1-draft
requires: ../core.md
last_reviewed: 2026-10-14
verify_against:
  - https://help.openai.com/en/articles/20001066-skills-in-chatgpt
  - https://help.openai.com/en/articles/20001256-plugins-in-chatgpt
  - https://help.openai.com/en/articles/10169521-projects-in-chatgpt
  - https://help.openai.com/en/articles/20001143/
  - https://developers.openai.com/learn/agents
  - https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide
---

# ChatGPT / OpenAI Adapter

ChatGPT- and OpenAI-specific artifact selection, packaging, and handoff guidance only. Mission, workflow, quality hierarchy, persona semantics, and durable integration contracts come from canonical sources; do not restate them here.

## Choosing the OpenAI artifact

Map the user's need to the narrowest surface that owns the behavior:

| Need | OpenAI artifact / surface |
| --- | --- |
| One-off, bounded request | Direct prompt in ChatGPT |
| Lightweight preferences that should apply broadly across chats | Custom Instructions |
| Persistent context, files, and instructions for one body of work | ChatGPT Project |
| Reusable, on-demand workflow or capability | Skill |
| Reusable workflow that also needs connected services, external data, or actions | Plugin containing Skills and/or Apps |
| Repeatable end-to-end team workflow with tools, schedules, or API triggers | ChatGPT Workspace Agent, when available |
| Repository-specific coding guidance | `AGENTS.md` / Codex instructions, optionally combined with Skills or Plugins |
| Agent embedded in a product or service | Responses API and/or Agents SDK; use the current managed agent API when its runtime model fits |

Do not default every reusable behavior to a Skill. A Skill is appropriate for reusable task-scoped guidance. Use a Plugin when the workflow also needs app connections or packaged external capabilities. Use a Workspace Agent when the desired result is a durable autonomous workflow with its own tools, configuration, schedule, or trigger channels.

Custom GPTs are a legacy target during the current transition. Do not choose a new GPT as Axiom's durable default when a Skill, Plugin, Project, or Workspace Agent better represents the use case.

If the user's ChatGPT/OpenAI surface, plan, or workspace permissions materially change the artifact choice, ask or state the assumption before handoff.

## Axiom self-materialization

When materializing Axiom itself in ChatGPT, treat the repository root as the canonical definition.

Runtime authority includes:

- [`../core.md`](../core.md) for Axiom's workflow and artifact decisions;
- [`../persona.md`](../persona.md) for persona-design policy;
- [`../integrations/github.md`](../integrations/github.md) when Axiom can create or evolve canonical repository artifacts;
- [`../integrations/notion.md`](../integrations/notion.md) when the optional artifact catalog is connected.

This file remains build-time guidance and must not be copied into a second competing definition of Axiom.

The preferred personal ChatGPT materialization is a thin entry Skill with the connected GitHub and Notion apps available when authorized. The Skill should load the canonical Axiom sources, recognize natural artifact-design intent, ask only high-impact questions, and then use the integrations when the user wants durable publication.

When GitHub access is available, durable canonical creation or modification should follow the GitHub contract: focused branch, draft pull request, user review, and no merge without explicit authorization. When Notion is available, maintain lightweight catalog metadata without copying the full canonical behavior there.

Catalog use is distinct from an artifact's own runtime integrations. If a user says that a generated Skill should not save its outputs to Notion, continue to register the canonical Skill in the Axiom catalog when the catalog is enabled unless the user explicitly opts out of catalog registration itself.

Axiom should not require the user to ask for `agent-spec`, `skill-spec`, repository paths, adapters, or handoff syntax explicitly. Requests such as “I need something that turns rough notes into a structured daily log” should be enough for Axiom to begin discovery and classification.

## Skill handoff

Axiom specifies the reusable capability; ChatGPT's `skill-creator` should generate, update, test, or troubleshoot the final Skill when available.

For reusable artifacts managed canonically by Axiom, create the canonical branch and draft pull request before producing the definitive ChatGPT Skill. If the user deliberately wants a pre-merge runtime test, materialize from the review branch only as a provisional deployment and report that status explicitly. After approval and merge, rebuild or update the deployment from the approved canonical revision when needed.

Before handoff, provide enough information that the creator does not need to rediscover the intent:

- **purpose** — the repeatable outcome the Skill exists to produce;
- **when useful** — requests and contexts in which the Skill should be selected automatically;
- **non-trigger contexts** — nearby requests that should remain ordinary chat when ambiguity is likely;
- **inputs** — user text, files, project context, or connected information the workflow expects;
- **workflow** — stable steps, decisions, checks, and fallback behavior;
- **resources** — examples, references, templates, or supporting files;
- **scripts/code** — deterministic or repetitive operations better packaged as reusable code;
- **tools/apps** — capabilities or connected services required by the workflow;
- **outputs** — expected deliverables and important format contracts;
- **persona** — concise interaction guidance when useful;
- **test prompts** — 2–3 representative requests when validation would improve confidence;
- **assumptions/open questions** — only unresolved issues that could materially change implementation.

Let `skill-creator` own current Skill packaging details. Do not duplicate volatile file-layout, metadata, installation, or troubleshooting rules in Axiom unless a target surface explicitly requires them.

## Canonical agent materialization

When an agent already has canonical repository files, ChatGPT materialization is a build step rather than a new behavioral design exercise.

Separate the inputs into two roles:

- **Runtime authority** — canonical sources such as `core.md`, `persona.md`, and any applicable `integrations/*.md` contracts. These define the behavior the deployed agent must preserve.
- **Build guidance** — the agent's `platforms/chatgpt.md` adapter. It guides artifact selection, source loading, app binding, validation, and packaging, but is not a second behavioral source.

The native creator should generate the smallest package that can execute those sources. For a Skill-based materialization, keep `SKILL.md` thin: discovery/activation boundaries, source loading, tool access, and platform operation belong there; the canonical behavior should not be copied into it.

Package canonical files as unmodified or fidelity-preserving deployment resources when the platform needs local copies. Generated manifests, metadata, bindings, native icons, and installation files are deployment artifacts and do not become canonical merely because the platform created them.

Prefer existing connected apps and native capabilities before creating custom integration infrastructure. Keep workspace IDs, credentials, private bindings, and similar deployment details out of the public canonical definition.

### Reusable materialization prompt

Use this as a handoff template when the canonical agent files are supplied to ChatGPT's native creator:

> Materialize **<agent name>** for ChatGPT using the supplied repository files as its canonical definition.
>
> Treat `core.md`, `persona.md`, and any applicable `integrations/*.md` files as authoritative runtime sources. Treat `platforms/chatgpt.md` as build-time guidance: use it to choose and configure the ChatGPT materialization, but do not treat it as a second behavioral definition.
>
> Create the smallest suitable native package described by the adapter. If the result uses an entry Skill, keep `SKILL.md` focused on discovery, activation, canonical-source loading, tool/app access, and operational handoff. Do not duplicate canonical behavior or persona into `SKILL.md`.
>
> Preserve the canonical files as deployment resources with high fidelity. Reuse existing connected apps or platform capabilities when they satisfy the integration contracts before creating custom infrastructure.
>
> Generate any required manifests, metadata, bindings, native icons, or deployment configuration as platform-owned artifacts. Keep deployment-specific identifiers, credentials, private bindings, and other environment details out of the canonical repository sources.
>
> Validate source loading, representative activation, the canonical acceptance scenarios relevant to this deployment, and any connected-system behavior the adapter requires. Report separately what was created, installed, connected, and actually runtime-validated.

Axiom may specialize this template for the current agent by naming the exact canonical files, integrations, existing app connections, target surfaces, and validation scenarios. It should not add platform packaging rules that belong to the native creator.

The user-facing instruction may be much shorter. If the canonical definition is already in context, a request such as **“Materialize this agent for ChatGPT.”** is sufficient; Axiom should generate the detailed handoff internally from the canonical sources and this adapter.

## Plugin handoff

Use a Plugin when reusable instructions need to travel together with external capabilities.

A Plugin specification should identify:

- which behavior belongs in Skills;
- which external systems require Apps or MCP-backed capabilities;
- read vs. write actions;
- authentication or workspace prerequisites the user must complete;
- approval boundaries for consequential actions;
- surfaces where the plugin must work (Chat, Work, Codex, desktop, web, or mobile) when that matters.

Prefer the native Plugin Creator when available rather than teaching Axiom the full plugin package format.

## Projects and Custom Instructions

Use **Custom Instructions** for lightweight, broadly applicable user preferences rather than task-specific workflows.

Use a **Project** when instructions, files, chats, and connected sources should remain scoped to one ongoing body of work. Project instructions should contain only the behavior that needs to remain active throughout that project; reusable task workflows should stay in Skills so they can be invoked when relevant.

## Workspace Agents

Use a **Workspace Agent** when the user needs a persistent, shareable agent that can own a repeatable end-to-end workflow rather than merely provide reusable instructions.

A Workspace Agent specification may include:

- mission and description;
- instructions and persona;
- model/reasoning requirements only when they materially affect the workflow;
- Skills;
- Apps and tool permissions;
- memory requirements;
- action approval boundaries;
- starter prompts;
- schedules or API trigger channels;
- deployment context such as ChatGPT or Slack.

Keep Skills modular: attach reusable capabilities to the agent rather than expanding one monolithic system instruction.

## Codex

For repository-specific coding behavior, prefer `AGENTS.md` for instructions that should be continuously available within repository scope. Use Skills for task-specific reusable workflows and Plugins when those workflows need external apps or packaged integrations.

Do not add prompt scaffolding for intermediate plans, reasoning traces, or progress messages unless current Codex guidance explicitly calls for it. Native model and harness behavior evolves quickly.

## API and developer runtimes

When the artifact belongs in an application rather than ChatGPT itself, hand off an agent/runtime specification rather than a ChatGPT Skill specification.

Prefer current OpenAI agent primitives such as the Responses API, Agents SDK, supported managed agent APIs, tools, MCP, and structured output mechanisms according to runtime needs. Keep model choice, tool configuration, schemas, state, and deployment concerns in the implementation layer rather than the portable Axiom core.

## Instruction guidance

- Prefer clear headings, explicit steps for multi-stage workflows, and concrete positive instructions.
- Add examples when they disambiguate behavior or classification boundaries.
- Do not require XML or decorative prompt scaffolding by default.
- Do not request visible chain-of-thought. Ask for conclusions, checks, assumptions, concise rationale, or artifacts instead.
- Keep persona subordinate to task quality and the hierarchy in `../persona.md`.

## Verification rule

OpenAI product surfaces are changing rapidly. At each `last_reviewed` pass, verify Skill availability, Plugin semantics, Workspace Agent capabilities, Codex instruction behavior, API agent primitives, and any migration/deprecation notices against current OpenAI documentation before changing the durable Axiom core.
