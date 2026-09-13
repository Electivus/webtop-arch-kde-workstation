# Domain Docs

This repository uses a single context: root `CONTEXT.md` for domain vocabulary and `docs/adr/` for architecture decisions.

## Before exploring, read these

- **`CONTEXT.md`** at the repository root.
- **`docs/adr/`**: read the ADRs relevant to the area being explored.

If these files do not exist, proceed silently. The `domain-modeling` skill, also reached through `grill-with-docs` and `improve-codebase-architecture`, creates them when terms or decisions are resolved.

## File structure

```text
/
|-- CONTEXT.md
`-- docs/
    `-- adr/
        `-- 0001-<decision>.md
```

## Use the glossary's vocabulary

Use the terms defined in `CONTEXT.md` when naming domain concepts in issues, proposals, hypotheses, and tests. If a needed term is missing, verify that the concept belongs to the project and record a real vocabulary gap for `domain-modeling`.

## Flag ADR conflicts

When a proposal contradicts an existing ADR, identify the ADR and explain the proposed change and its rationale explicitly.
