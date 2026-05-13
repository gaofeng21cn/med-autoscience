# Standard Domain Agent Skeleton

Status: `repo-source physical anchors landed; workspace artifacts locator-only`
Owner: `MedAutoScience`
Purpose: record the human-facing location of the standard domain-agent skeleton anchors.
Machine boundary: machine truth lives in the product-entry manifest, the JSON anchors under `agent/`, `contracts/runtime/`, `runtime/artifact_locator/`, and MAS workspace/runtime receipt surfaces.

MAS now keeps physical repo-source anchors for the standard domain-agent skeleton while preserving the existing callable facades and generated docs. The anchors are intentionally small: they prove where new repo-source material should land, and they do not import workspace artifact bodies, memory bodies, publication decisions, or paper packages into the repository.

Current anchors:

- `agent/standard-domain-agent-anchor.json`
- `contracts/runtime/standard-domain-agent-anchor.json`
- `runtime/artifact_locator/workspace-runtime-artifact-root.locator.json`
- `docs/runtime/contracts/standard_domain_agent_skeleton.md`

Workspace and runtime evidence remains body-free. Missing live paper apply, owner receipt, or long-soak evidence must be reported as a typed blocker rather than as paper closure.
