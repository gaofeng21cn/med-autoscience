# Owner Receipt And Route Control Skill Policy

MAS owner receipts record what stage work changed, which refs were read, which outputs were produced, and which owner should act next. Route control follows `owner_route` and controller decisions; generated OPL surfaces may dispatch allowlisted MAS tasks but cannot interpret medical quality or write domain truth.

Every mutating path must return one of these semantic outcomes: owner receipt with refs, typed blocker, no-op with currentness proof, route-back request, or human gate request. Ambiguous completion is invalid because it would let runtime progress replace medical authority.
