"""Evidence-based AI maturity assessment (framework structure adapted from UNESCO under CC BY-SA 3.0 IGO)."""

import os
from pathlib import Path

# Data folders live next to src/ in a checkout. A non-editable install (the container image) points
# AIMATURITY_HOME at the folder that holds framework/, rubric/ and samples/.
ROOT = Path(os.environ.get("AIMATURITY_HOME") or Path(__file__).resolve().parents[2])
FRAMEWORK = ROOT / "framework"
RUBRIC = ROOT / "rubric"
SAMPLES = ROOT / "samples"
SCHEMAS = ROOT / "schemas"
EVALS = ROOT / "evals"
