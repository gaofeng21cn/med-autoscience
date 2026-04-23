from __future__ import annotations
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import matplotlib.pyplot as plt
import pytest
from med_autoscience import display_registry
from med_autoscience.display_pack_resolver import get_template_short_id
