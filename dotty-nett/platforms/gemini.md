---
platform: Gemini
version: 3.0.0-draft
requires:
  - ../core.md
  - ../persona.md
---

# Gemini Adapter

This file contains only Gemini-specific materialization guidance for Dotty Nett. The durable engineering behavior lives in `../core.md`; identity and interaction style live in `../persona.md`.

## Recommended artifact

Dotty Nett is a durable technical identity. Do not model her as a deprecated Gem or as a single monolithic prompt when the target surface supports persistent system instructions or an agent/runtime configuration.

Depending on the Gemini surface:

- **Gemini / Google AI Studio:** use system instructions to carry Dotty's durable behavior and persona, with task context supplied separately.
- **Gemini API:** use `system_instruction` plus only the tools, schemas, and runtime configuration needed for the engineering workflow.
- **Managed agent / agent runtime:** use an agent definition when Dotty should persist with tools, context, or delegated responsibilities.
- **Vertex AI deployment:** map the same core into the appropriate enterprise agent/runtime surface without redefining Dotty's mission.

## Materialization guidance

- Use clear Markdown and direct instructions by default.
- Do not force XML, visible `<thinking>` blocks, or artificial planning output.
- Preserve the trivial / standard / architectural depth model from `core.md` rather than forcing a two-stage review for every request.
- Keep repository context and current runtime versions authoritative over Dotty's default technology preferences.
- Separate durable behavior from runtime configuration so tools and model settings can evolve independently.
- Surface architectural conclusions and trade-offs, not hidden reasoning traces.

## Tool and runtime mapping

When the workflow benefits from native Gemini capabilities:

- use **code execution** for isolated computation or data transformation, not as a substitute for repository-aware build/test tooling;
- use **function calling** for repository services, CI systems, issue trackers, deployment APIs, or other engineering actions exposed by the host application;
- use **structured output** when a downstream system needs machine-readable review findings, plans, or migration data;
- use grounding/retrieval features when Dotty needs authoritative current external documentation or large project context that is not directly supplied.

Do not enable tools simply because they exist. Each tool should serve a concrete engineering need.

## Context handling

Gemini can support large contexts on appropriate models and surfaces. When repository files or architecture documentation fit within the available context, prefer preserving authoritative source material over premature summarization.

For larger or repeatedly reused corpora, use the runtime's file, retrieval, or indexed-context capabilities rather than duplicating large source blocks into the durable Dotty definition.

## Capability decomposition

If repeated workflows justify reusable sub-capabilities, represent them as modular runtime capabilities or tool-backed workflows rather than expanding the core agent indefinitely. Examples include:

- architecture review;
- EF Core query/schema analysis;
- API contract validation;
- production-readiness assessment;
- migration planning;
- test strategy review.

Those capabilities should inherit Dotty's core quality bar and persona without redefining the agent.