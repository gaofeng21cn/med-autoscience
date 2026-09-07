# MAS Authority Functions

Owner: `med-autoscience`
Purpose: `authority_declaration_directory`
State: `declaration_surface`
Machine boundary: This directory declares authority boundaries; bindings are owned by
`contracts/domain_handler_registry.json`, not by this README.

MAS retains medical owner judgment, receipts and forbidden-write validation.
Open-ended scientific and quality judgments are made by the declared Stage roles.
Registry handlers consume exact host inputs and return domain results or authorized
CAS requests; Framework performs the generic transport and lifecycle operation.

The current handler map and private attempt-local snapshot adapter are documented
once in [Agent Runtime Interface](../../docs/runtime/contracts/agent_runtime_interface.md).
The executable App contribution is a separate read-only producer, not a registry handler.

This directory is not a runner, scheduler, queue, session ledger, cache or artifact store.
Declaration presence does not prove runtime readiness, study progress or publication.
