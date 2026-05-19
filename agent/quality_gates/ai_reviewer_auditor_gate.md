# AI Reviewer Auditor Gate

AI-first quality gates require a reviewer or auditor agent invocation that is separate from the executor invocation. The reviewer/auditor reads source refs, evidence refs, manuscript refs, review refs, runtime event refs, and quality pack refs, then emits an AI reviewer record, audit receipt, route-back reason, or typed blocker.

The gate can authorize medical quality only through MAS-owned reviewer/auditor records with current provenance. Script success, test pass, generated interface readiness, provider completion, and self-review in the executor context are insufficient and must fail closed.
