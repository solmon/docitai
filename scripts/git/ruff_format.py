#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess


RUFF_FORMAT_CMD = "ruff format --force-exclude 2>&1 | grep -v '`ISC001`. To avoid unexpected behavior'"
envcopy = os.environ.copy()
envcopy["CLICOLOR_FORCE"] = "1"
subprocess.run(RUFF_FORMAT_CMD, shell=True, check=True, env=envcopy)  # noqa: S602
