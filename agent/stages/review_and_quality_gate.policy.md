# Review And Quality Gate Policy

This stage requires independent reviewer or auditor invocation. The reviewer reads stage outputs, source refs, evidence refs, review refs, manuscript refs, and artifact refs from a separate task record. Mechanical guards can validate provenance or block stale records; they cannot emit the medical quality verdict.

Quality and ready claims fail closed when the independent record or current refs
are missing. Stage transition does not fail closed for an ordinary repair gap: a
consumable independent-review packet may close as
`completed_with_quality_debt`, with debt blocking ready claims. Hard authority,
safety, identity, currentness, credential, irreversible-action, and human gates
remain blockers.

Stage throughput requires a reviewable delta or an evidence-backed blocker. Currentness-only, record-only, or provider-completed-only closeout cannot satisfy the stage unless it names the consumed no-op evidence and forced next target surface. Human gate requests must carry the decision boundary, evidence refs, blocking reason, and resume target surface.
