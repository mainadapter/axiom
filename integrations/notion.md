---
name: Axiom Notion Catalog Integration Contract
version: 1.1.0-draft
language: en
description: Optional human-friendly catalog for canonical Axiom artifacts without duplicating their behavioral source of truth.
---

# Notion Catalog Integration Contract

## Purpose and boundary

Notion may provide a human-friendly catalog for discovering and navigating canonical Axiom artifacts.

GitHub remains the authoritative source for Prompt, Skill, and Agent content. The Notion catalog is an index and interface, not a second behavioral definition that must be kept textually synchronized.

Catalog registration is independent from an artifact's own runtime persistence behavior. A Skill or Agent may have no Notion runtime integration at all and still belong in the Axiom catalog because the catalog describes the canonical artifact, not the outputs it produces.

This contract defines catalog semantics. Workspace IDs, database identifiers, property IDs, connector operations, and other private deployment details belong to the operational binding rather than the public canonical repository.

## Catalog roles

A catalog entry should identify an artifact without reproducing its full canonical instructions. Useful semantic fields include:

- **Artifact** — human-readable canonical name.
- **Type** — Prompt, Skill, or Agent.
- **Purpose** — short description of what the artifact is for.
- **Category** — optional discovery-oriented grouping when useful.
- **Path** — canonical repository path.
- **GitHub** — link to the canonical location or, while under review, the relevant draft pull request.

The exact Notion property names may follow the existing workspace conventions as long as these roles remain clear.

## Content ownership

Do not maintain a full independent copy of canonical prompts, skills, or agents in Notion by default.

During migration, legacy prompt text may remain temporarily in the catalog until it has been safely transferred to GitHub. Preserve that content rather than deleting it merely to achieve the target schema.

After migration, prefer a concise purpose/description and repository link over duplicated canonical instructions.

## Creation and update behavior

When Axiom creates or durably changes a canonical artifact and a catalog integration is available:

1. Create or update the GitHub branch and draft pull request first.
2. Ensure one Notion catalog entry represents the artifact unless the user explicitly opts out of catalog registration itself.
3. Keep its type, purpose, repository path, and link aligned with the canonical artifact.
4. While the artifact is under review, the catalog may link to the draft pull request or branch if that is more useful than linking to an outdated `main` path.
5. After merge, prefer the stable canonical `main` location.

A request not to persist runtime outputs in Notion does **not** imply opting out of catalog registration. For example, “do not save Daily Log results to Notion” means the Daily Log Skill should return its output in conversation without Notion persistence; the canonical Daily Log Skill should still appear in the Axiom catalog when that catalog is enabled.

Do not create duplicate catalog entries for provider deployments of the same canonical artifact. Platform packages are implementations of the artifact, not separate catalog artifacts unless the user explicitly wants to track deployments separately.

## Lookup behavior

The catalog should support quick discovery such as:

- finding an artifact by name or purpose;
- browsing Prompt, Skill, and Agent types;
- identifying the canonical GitHub path;
- opening the source definition for review or use.

If the catalog and GitHub disagree about behavior, GitHub canonical content wins. Correct stale catalog metadata rather than changing canonical behavior to match the index.

## Preservation and migration

- Do not delete legacy prompt text until its canonical GitHub replacement exists and the user has approved cleanup.
- Preserve useful categories and discovery metadata when evolving an existing prompt database into the broader artifact catalog.
- Avoid adding properties that merely duplicate Git metadata without improving discovery.
- Keep the catalog lightweight enough that maintaining it does not become a parallel documentation burden.
