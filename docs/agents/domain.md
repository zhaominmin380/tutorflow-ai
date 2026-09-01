# Domain Docs

How engineering skills should consume TutorFlow AI's domain documentation.

## Before exploring

Read the root `CONTEXT.md` and any ADR in `docs/adr/` that applies to the area of work. This repository is single-context; there is no context map or per-package glossary.

If a relevant document does not exist, proceed silently. The domain-modeling skill creates glossaries and ADRs only when terminology or a durable decision is resolved.

## Use the glossary vocabulary

Use canonical terms from `CONTEXT.md` in issues, plans, tests, and implementation discussions. Do not substitute a term the glossary explicitly avoids. A missing needed term is a reason to use the domain-modeling skill.

## Respect ADRs

If proposed work conflicts with an applicable ADR, surface that conflict explicitly rather than silently overriding the decision.
