# AI Reviewer Auditor Gate

AI-first quality gates require a reviewer or auditor agent invocation that is separate from the executor invocation. The reviewer/auditor reads source refs, evidence refs, manuscript refs, review refs, runtime event refs, and quality pack refs, then emits an AI reviewer record, audit receipt, route-back reason, or typed blocker.

The reviewer/auditor record must be grounded in AI-native medical judgment, not just structured checklist completion. Rubrics and quality packs define the minimum traceable floor and route-back vocabulary; they do not cap the reviewer from naming additional clinical, statistical, contribution, reader-risk, or journal-fit concerns.

The gate can authorize medical quality only through MAS-owned reviewer/auditor records with current provenance. Script success, test pass, generated interface readiness, provider completion, and self-review in the executor context are insufficient and must fail closed.
