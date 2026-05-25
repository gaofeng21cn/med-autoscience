# Standard Domain Agent Skeleton

Status: `repo-source physical anchors landed; workspace artifacts locator-only`
Owner: `MedAutoScience`
Purpose: record the human-facing location of the standard domain-agent skeleton anchors.
Machine boundary: machine truth lives in the product-entry manifest, the JSON anchors under `agent/`, `contracts/runtime/`, `runtime/artifact_locator/`, and MAS workspace/runtime receipt surfaces.
State: `active_runtime_support`

MAS now keeps physical repo-source anchors for the standard domain-agent skeleton while existing callable/product/status/workbench surfaces remain migration inputs and direct-path bridges. The anchors are intentionally small: they prove where new repo-source material should land, and they do not import workspace artifact bodies, memory bodies, source bodies, publication decisions, or paper packages into the repository. Generated CLI/MCP/Skill/product-entry/status/workbench shells remain OPL-owned target surfaces; MAS exposes descriptor, locator, receipt, typed blocker and authority-function refs for those shells to consume.

Current anchors:

- `agent/standard-domain-agent-anchor.json`
- `contracts/runtime/standard-domain-agent-anchor.json`
- `runtime/artifact_locator/workspace-runtime-artifact-root.locator.json`
- `docs/runtime/contracts/standard_domain_agent_skeleton.md`

Workspace and runtime evidence remains body-free. Missing live paper apply, owner receipt, or long-soak evidence must be reported as a typed blocker rather than as paper closure.

Default new repo-source placement follows the product-entry skeleton surface:

- stage definitions: `agent/stages`
- prompts: `agent/prompts`
- skills and execution policy: `agent/skills`
- domain knowledge refs: `agent/knowledge`
- AI-first quality gates: `agent/quality_gates`
- projection / lifecycle adapter contracts: `contracts/runtime/projection_builders` and `contracts/runtime/lifecycle_adapters`

`runtime/artifact_locator/workspace-runtime-artifact-root.locator.json` is a locator anchor only. It can name workspace artifact roots, owner-route receipts, stage review indexes, publication-eval refs and controller-decision refs; it cannot move artifact bodies into repo source, authorize source readiness, mark publication quality, update `current_package`, or replace MAS owner receipt / typed blocker evidence.

Source readiness and artifact mutation remain MAS authority gates. The standard skeleton can carry source-readiness policy refs and artifact authority refs for OPL generated surfaces, but it cannot close those gates from file presence, provider completion, package freshness, test pass or generated-interface readiness. Missing independent reviewer/auditor record, artifact rebuild proof, owner receipt, no-forbidden-write proof or live workspace receipt must stay a typed blocker.
