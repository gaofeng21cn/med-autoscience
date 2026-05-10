# Policies

Status: `active policy index`
Owner: `MedAutoScience`

Policies are stable internal rules. They define boundaries that maintainers and
agents must follow; one-off checklists, closeout notes, and program boards
belong in `docs/program/`, `docs/references/`, or `docs/history/`.

| directory | purpose |
| --- | --- |
| [quality](./quality/) | Publication gate, AI-first quality, reviewer calibration, evidence review, and manuscript quality rules. |
| [study-workflow](./study-workflow/) | Stage-led research autonomy, study route, data asset, research route, archetype, submission revision, and workspace workflow rules. |
| [runtime-governance](./runtime-governance/) | Runtime operating model, external runtime dependency gate, MAS/MDS owner boundary, and runtime stabilization rules. |
| [repo-ops](./repo-ops/) | Mainline integration, merge/cutover gates, and repository preflight rules. |

## Rule

Policies may be referenced by code, tests, or manifests only through stable
semantic IDs or explicit policy paths. They must not become active backlog or
runtime truth.
