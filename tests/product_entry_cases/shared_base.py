from __future__ import annotations

import importlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS
from tests.study_runtime_test_helpers import (
    make_profile,
    read_runtime_state,
    runtime_state_path,
    write_runtime_state,
    write_study,
    write_text,
)
