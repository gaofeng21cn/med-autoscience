---
name: external-scientific-skills
description: Thin MAS discovery helper for on-demand external scientific specialist skills.
---

# External Scientific Skills

Default first to the eight core `mas-scholar-skills` modules: `display`,
`tables`, `stats`, `lit`, `write`, `review`, `submit`, and `data`. Use this
helper only after the current MAS work unit names an uncovered specialist gap
that those core modules cannot cover.

## Trigger Boundary

Use OPL Connect external-skills only when one of these is true:

- the user explicitly names a tool, database, workflow, or runtime;
- a core ScholarSkills route-back names an uncovered specialist gap;
- stage policy judges the core eight modules insufficient for the current
  owner delta;
- network access, cloud compute, sensitive data, or external credentials require
  policy or approval.

## Invocation Shape

Run only a single-skill discovery sequence; stop after one selected specialist:

```bash
opl connect external-skills search --query <specialist-gap> --json
opl connect external-skills inspect --skill <skill-id> --json
opl connect external-skills sync --skill <skill-id> --scope workspace --target-workspace <workspace_root> --json
```

Use quest scope when the current MAS owner route names a runtime quest target.
Do not preload a domain, library, repository, or full external skill pack.

Examples of legitimate specialist gaps include `scanpy`, `pydeseq2`, pathway
enrichment, Nextflow, RDKit, PyHealth, and similarly narrow scientific tool or
database needs.

## Authority Boundary

External specialist output is refs-only: candidate refs, execution receipt
candidates, owner-gate requests, and route-back hints. It cannot write MAS study
truth, paper body, artifact authority, owner receipt, typed blocker, human gate,
publication eval, controller decision, submission package, or `current_package`.

Machine flags:

- `single_skill_only = true`
- `bulk_load_allowed = false`
- `writes_authority = false`

Do not bulk load external skill libraries. Do not make K-Dense, an external
README, or a synced skill directory a MAS source of truth.
