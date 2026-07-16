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

Every review receipt names MedAutoScience, the lane-specific authority role and
verdict. Generation manifest v2 binds each professional receipt to the MAS-owned
lane scope and complete reviewed member inventory. The currentness receipt may
reuse an unchanged lane only when scope policy, professional rubric, and scope
identity are identical and complete origin provenance is retained; changed lanes
route back for fresh independent review. V1 remains whole-generation exact,
while `exact_byte_package` always covers the complete root inventory including
locators. Only exact lane receipt refs named by the current MAS
review-currentness receipt count.

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
