# MAS Domain Specialization

Owner: `MedAutoScience`
Purpose: medical-research specialization of the OPL standard-agent AI-first principle pack.
State: `active_domain_specialization`
Machine boundary: human-readable domain specialization. Machine-readable adoption is in `contracts/standard-agent-principles-adoption.json`; MAS contracts, source, runtime/controller readbacks, owner receipts, typed blockers, human gates, and publication/artifact authority remain authoritative for MAS behavior.

MAS adopts the OPL principles as a medical-research Foundry Agent:

- Intake is the declarative `direction_and_route_selection` Stage plus its prompt and MAS knowledge refs, not a standalone Skill or private controller. It frames the study question, source boundary, route recommendation, source-readiness evidence needs, and the first MAS owner-answer boundary.
- MAS owns study truth, clinical/source readiness, publication quality, artifact/current-package authority, memory accept/reject decisions, owner receipts, typed blockers, human gates, and controller decisions.
- OPL may host stage runtime, generated surfaces, refs-only workspace/source locator, attempt transport, and conformance readbacks. It does not write MAS truth, sign MAS owner receipts, create MAS typed blockers, create human gates, or authorize publication/submission readiness.
- MAS ScholarSkills is a refs-only professional capability pack. Its active modules are `display`, `tables`, `stats`, `lit`, `write`, `review`, `submit`, and `data`. `intake` is not an active ScholarSkills module, and `omics` stays deferred/reference until MAS has a stable real omics professional workflow.
- Medical research execution remains AI-first expert work. Contracts, tests, readbacks, and generated descriptors protect source refs, owner route, receipt shape, and false-ready gates; they do not replace medical judgment, independent reviewer/auditor gates, owner receipts, or route-back evidence.

## AI-first implementation split

MAS audits capabilities first as logical medical-research modules, then chooses the physical exposure surface. Most elastic work belongs in an existing ScholarSkills professional skill rather than a new physical skill: manuscript argument, reviewer response, citation support, statistical reporting, figure/table QA, source grounding, Data Availability, and submission handoff can remain separate logical modules while sharing a smaller set of professional skill entry points.

Use the three-layer split this way:

- `professional_skill`: AI-first judgment, synthesis, criticism, route-back reasoning, reviewer-risk assessment, and refs-only candidate package shaping.
- `contract_module` / MAS source module: stable identities, authority boundaries, allowed writes, receipt schemas, owner-route constraints, and deterministic validation.
- `runtime_projection` / OPL generated surface: status, locator, dispatch affordance, readback, sync, install, and operations evidence.

Do not create a new MAS or ScholarSkills physical skill just because a logical capability module is named. Add or split a professional skill only when reuse, versioning, install/discovery boundary, or metadata isolation clearly beats updating an existing skill. Otherwise update the existing skill and keep MAS contracts light.

This specialization keeps MAS medical research AI-first while preventing OPL intake, generated descriptors, or ScholarSkills capability packaging from becoming MAS domain authority.
