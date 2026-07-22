# Review And Quality Gate Policy

This is the independent cross-Stage Meta Review. It starts a new StageRun whose
primary Attempt uses the shared `producer` role, inherits no upstream authoring
or analysis conversation, and consumes only exact stage artifact hashes, source
refs, Stage Review receipts, global rubric refs, and necessary lineage. Mechanical
guards can validate provenance or block stale records; they cannot emit the
medical quality verdict.

The Meta Reviewer does not repair upstream artifacts inline. It emits a
defect-owner matrix and routes to the earliest canonical Stage that can close the
root cause. The target Stage creates a new generation and passes fresh independent
Review before this Meta Review runs again.

The Meta Reviewer independently checks all applicable
`initial_draft_evidence_integrity_requirements` in
`contracts/manuscript_first_draft_quality_policy.json` against the immutable
candidate snapshot and lane-consumed member inventories. It does not reopen live
workspace files to complete missing evidence, and it assigns each defect to the
requirement's declared earliest owner.

Every review receipt names MedAutoScience, the lane-specific authority role and
verdict. Generation manifest v2 binds each professional receipt to the MAS-owned
lane scope and reviewed member inventory plus its artifact/claim/provenance
dependency graph. OPL Framework evaluates semantic currentness over each reviewed
node's declared transitive dependencies; MAS consumes that evaluation and keeps
the domain verdict. `review_scope_sha256` and member hashes are locator/stale
hints, not content authority. Reuse requires the current scope id/kind/dependency
closure, rubric, stable member identity/role, snapshot binding, and complete
origin provenance. `exact_byte_package` contains package content/wrapper members,
not checklist, status, evaluation, projection, or receipt metadata. Only exact
lane receipt refs named by the current MAS review-currentness receipt count.

Candidate-level review begins after candidate freeze. All affected lanes are
dispatched in one wave, independent lanes may run in parallel, and findings are
aggregated before one repair route is selected. This sequencing follows
`contracts/artifact_iteration_efficiency_policy.json`; it changes review cost,
not the independent-review or authority boundary.

Quality and ready claims fail closed when the independent record or current refs
are missing. Stage transition does not fail closed for an ordinary repair gap: a
consumable independent-review packet may close as
`completed_with_quality_debt`, with debt blocking ready claims. Hard authority,
safety, identity, currentness, credential, irreversible-action, and human gates
remain blockers.
