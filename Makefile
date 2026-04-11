.PHONY: test test-fast test-meta test-display test-full

test: test-fast

test-fast:
	uv run pytest -q -m "not meta and not display_heavy"

test-meta:
	uv run pytest -q -m meta

test-display:
	uv run pytest -q -m display_heavy

test-full:
	uv run pytest -q
