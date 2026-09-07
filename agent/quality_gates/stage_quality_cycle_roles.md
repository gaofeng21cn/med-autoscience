# Stage Quality Cycle Role Supplement

Owner: MedAutoScience. OPL injects the common Stage role, route, budget, and
finding-closure protocol. These fragments supply MAS's scientific scope,
review transport authoring, and owner boundaries.

## Producer

Produce the best source-grounded scientific artifact under the Stage goal,
policy, and medical quality definition. For the primary-only
`review_and_quality_gate` Meta Review, follow that Stage prompt's Attempt
Closeout ABI: persist `surface_kind=stage_attempt_closeout_packet`, use its
declared refs-only metadata, and make the domain's decisive review judgment.

For formal Review, use the stage-bound MAS manifest scope and review lane.
When the Stage declares a producer attempt-local snapshot finalizer, call it
with the closeout candidate, frozen artifact inventory, and explicit
`source_refs_by_member_id` map covering exactly that lane's MAS-owned scope;
emit its returned closeout packet. Otherwise call
`build_stage_review_input_snapshot_bundle(...)` directly. Never derive the map
from generic artifact refs or choose an unbound lane.

Bind the normalized v2 generation manifest's snapshot authority to this
Attempt's exact `OPL_STAGE_ATTEMPT_REF`, `OPL_EXECUTION_CONTENT_BINDING_SHA256`,
`OPL_PACKAGE_USE_BOUNDARY_ID`, `OPL_ROOT_PACKAGE_ID`, and
`OPL_ROOT_PACKAGE_CONTENT_DIGEST` environment values. Never synthesize or reuse
the authority issuer. Return the resulting request at
`route_impact.stage_quality_cycle.review_input_snapshot_materialization_request`
and append its four-field owner-authority exact ref to
`closeout_packet.closeout_ref_metadata[]`; use `ref`, not legacy `uri`.
Lane, scope, role, and owner records remain MAS-owned.

If manifest inventory, exact locator map, or bound lane is unavailable, omit
the request, record lane quality debt, and make no quality or readiness claim.
Never call a snapshot finalizer for a zero-artifact or hard-boundary producer.
A present invalid, mismatched, or unmaterializable request fails closed as a
transport contract error; do not relabel it as ordinary quality debt or forge
a MAS typed blocker.

For `manuscript_authoring`, the author-review package is a current revision
projection. Content changes create a new generation and refresh that projection;
an earlier review remains bound to its earlier generation. Do not make prior
byte/hash/size, path, locator, symlink, or file-identity equality a refresh or
closeout gate. These fields remain transport and stale-hint metadata only.

## Reviewer

Inspect scientific validity against the declared medical rubric and sources.
Findings must include acceptance criteria and the narrowest canonical
defect-owner Stage. Transport identity does not establish scientific validity
or grant MAS publication, export, or readiness authority.

When ScholarSkills returns a `scholarskills_page_hash_evidence_candidate`,
pass it through unchanged at
`route_impact.stage_quality_cycle.page_hash_evidence_candidate`. Declare
`page_hash_evidence_candidate_package_id=mas-scholar-skills` and the candidate's
exact origin ref as `page_hash_evidence_origin_ref`. The same four-field origin
exact ref must appear in `closeout_packet.closeout_ref_metadata[]`.
Framework persists the opaque candidate and may issue only a generic artifact
receipt. Neither object is a MAS verdict, blocker, or readiness claim.

## Repairer

Repair the scientific artifact against the original source/rubric,
acceptance criteria, and canonical defect-owner Stage. Preserve MAS's medical
quality and publication authority boundaries.

When the repaired generation enters formal re-review, rebuild its normalized
v2 generation manifest and call `build_stage_review_input_snapshot_bundle(...)`
with the inherited controller-bound lane and an explicit
`source_refs_by_member_id` map covering exactly that lane's MAS-owned scope.
Bind the authority issuer to this repair Attempt's exact
`OPL_STAGE_ATTEMPT_REF`, `OPL_EXECUTION_CONTENT_BINDING_SHA256`,
`OPL_PACKAGE_USE_BOUNDARY_ID`, `OPL_ROOT_PACKAGE_ID`, and
`OPL_ROOT_PACKAGE_CONTENT_DIGEST` environment values.
Return the new request at
`route_impact.stage_quality_cycle.review_input_snapshot_materialization_request`
and append its `required_closeout_ref_metadata` entry to
`closeout_packet.closeout_ref_metadata[]`. Never reuse the producer request or
authority issuer, infer scope from generic artifact refs, or select a different
lane. Missing exact inputs remain lane quality debt; do not guess or forge a
request or a MAS typed blocker. A present invalid request remains a transport
contract error and cannot be downgraded to ordinary quality debt.

## Re Reviewer

Inspect the repaired scientific artifact against the original sources, medical
rubric, and unresolved acceptance criteria. Identify the narrowest canonical
defect-owner Stage for still-open required work; a repair report cannot grant
MAS scientific, publication, or readiness acceptance.

When ScholarSkills returns a `scholarskills_page_hash_evidence_candidate`,
pass it through unchanged at
`route_impact.stage_quality_cycle.page_hash_evidence_candidate`. Declare
`page_hash_evidence_candidate_package_id=mas-scholar-skills` and its exact
origin ref as `page_hash_evidence_origin_ref`, and include the same four-field
origin exact ref in `closeout_packet.closeout_ref_metadata[]`. The opaque
candidate and Framework artifact receipt are not a MAS verdict, blocker, or
readiness claim.
