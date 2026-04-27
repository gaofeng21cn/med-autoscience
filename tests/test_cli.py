from __future__ import annotations

from .test_cli_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

from .test_cli_cases.public_entry_commands import *  # noqa: F403,F401
from .test_cli_cases.runtime_and_quality_commands import *  # noqa: F403,F401
from .test_cli_cases.ai_reviewer_publication_eval_command import *  # noqa: F403,F401
from .test_cli_cases.sidecar_and_submission_commands import *  # noqa: F403,F401
from .test_cli_cases.bootstrap_and_bundle_commands import *  # noqa: F403,F401
