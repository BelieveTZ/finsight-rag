# Domain Docs

How the engineering skills should consume this repository’s domain documentation when exploring the codebase.

## Before exploring, read these

- `CONTEXT.md` at the repository root.
- `CONTEXT-MAP.md` if it exists.
- Relevant ADRs under `docs/adr/`.

If these files do not exist, proceed silently. Do not create empty domain documentation in advance. The domain-modeling workflow should create it only when real terminology or architectural decisions have been established.

## File structure

This repository uses a single-context layout:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
└── src/
```

`CONTEXT.md` is the project glossary and domain-language reference. Important, difficult-to-reverse architectural decisions belong in `docs/adr/`.

## Use the glossary’s vocabulary

When an issue, design proposal, test, hypothesis, or implementation names a domain concept, use the terminology defined in `CONTEXT.md`.

If a necessary concept is missing, reconsider whether the new term is needed or record it for the domain-modeling workflow.

## Flag ADR conflicts

If proposed work contradicts an existing ADR, surface the conflict explicitly instead of silently overriding the recorded decision.
