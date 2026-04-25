## Medical stage packet discipline

Use this block whenever the current stage needs to become durable enough for resume, takeover, review, or route-back.

The goal is to learn from DeepScientist stage operational packets while keeping `MAS` as the medical research owner.

### Stage-start packet

Before substantial work, recover or create a compact stage-start packet with:

- `study_id`, `active_route`, `active_run_id`, and `quest_id` when available
- current `study_charter` boundary
- current objective contract or route question
- active evidence / review ledger refs
- current baseline, comparator, or accepted prior line
- current blocker, human gate, or route-back reason if any
- planned durable outputs for this stage

### Stage-end packet

Before leaving the stage, write or refresh a stage-end packet with:

- route outcome: `continue`, `route_back`, `bounded_analysis`, `write_repair`, `finalize`, `human_gate`, or `stop`
- evidence refs that directly support the route outcome
- reviewer-first concerns that remain open or were closed
- failed paths and why they should not be retried blindly
- winning path and exact resume point
- next route and why it is the narrowest honest continuation

### Tool discipline

- Use artifact / reports as the canonical stage truth surface.
- Use evidence and review ledgers for claim, rigor, novelty, clinical relevance, and reviewer-concern closure.
- Use memory only when a reusable lesson should change future default behavior.
- Use execution logs as first-hand evidence, not as paper or publication authority.
- Do not use prose-only summaries as a substitute for route truth, ledger closure, or publication gate state.

### Medical route mapping

- `idea`: produce an idea objective contract and candidate board before selecting a route; record why each serious candidate remains viable or is rejected.
- `analysis-campaign`: define a bounded campaign before running analysis; bind every batch to a claim, concern, or bounded route-back reason.
- `write`: treat each repair as an evidence-bound repair; bind section edits to evidence refs, reviewer-first concerns, caveats, and claim downgrades.
- `finalize`: verify submission truth before package readiness, including declarations, caveats, artifact freshness, submission gates, and unresolved human gates.
- `decision`: record the route outcome from durable truth: continue, route-back, bounded analysis, write repair, finalize, human gate, or stop.
