from __future__ import annotations

import importlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS
from tests.study_runtime_test_helpers import make_profile, write_study, write_text
