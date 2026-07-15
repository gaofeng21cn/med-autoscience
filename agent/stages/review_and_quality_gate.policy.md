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

Quality and ready claims fail closed when the independent record or current refs
are missing. Stage transition does not fail closed for an ordinary repair gap: a
consumable independent-review packet may close as
`completed_with_quality_debt`, with debt blocking ready claims. Hard authority,
safety, identity, currentness, credential, irreversible-action, and human gates
remain blockers.
