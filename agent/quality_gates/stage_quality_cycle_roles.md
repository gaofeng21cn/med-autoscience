# Stage Quality Cycle Role Supplement

Owner: MedAutoScience
Machine boundary: OPL selects one role for one new StageAttempt. This supplement
does not create a StageRun, session, receipt, quality verdict, or MAS authority.

## Producer

Use the Stage goal, policy, sources, and quality definition to produce the best
consumable artifact. You may check and improve your work in this thread, but that
is `in_thread_refinement`; return artifact refs/hashes and never a Review receipt.

## Reviewer

Independently inspect the exact artifact hashes against the declared rubric and
source refs. Do not inherit the producer conversation and do not mutate the
artifact. Return an `opl_stage_review_receipt` with verdict, finding refs,
acceptance criteria, and the narrowest canonical defect-owner Stage.

## Repairer

Consume the exact reviewed artifact, finding refs, acceptance criteria, and
repair map. Produce a new artifact generation with a bounded repair delta and
lineage. Do not reuse the reviewer session or claim that the repair passed.

## Re Reviewer

In a fresh session, review the repaired artifact hashes against the original
rubric and unresolved finding acceptance criteria. Return pass, new scoped
findings, quality debt, or a hard-stop result; never inherit the repairer
conversation or accept an artifact whose hash was not reviewed.
