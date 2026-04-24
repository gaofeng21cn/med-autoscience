from __future__ import annotations

from .test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

from .test_runtime_watch_cases.chunk_01 import *  # noqa: F403,F401
from .test_runtime_watch_cases.chunk_02 import *  # noqa: F403,F401
from .test_runtime_watch_cases.chunk_03 import *  # noqa: F403,F401
from .test_runtime_watch_cases.chunk_04 import *  # noqa: F403,F401
from .test_runtime_watch_cases.chunk_05 import *  # noqa: F403,F401
