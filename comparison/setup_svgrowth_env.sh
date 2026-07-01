#!/usr/bin/env bash
# One-time setup of the dedicated svGrowth virtual environment.
#
# svGrowth depends on numba, which currently requires NumPy < 2.4 and
# Python < 3.14 -- incompatible with the gr package's environment. So svGrowth
# gets its own venv (.venv-svgrowth), and comparison/run_svgrowth.py drives it as
# a subprocess.
#
# Usage:  bash comparison/setup_svgrowth_env.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO/.venv-svgrowth"

echo "Creating svGrowth venv at $VENV (Python 3.12)..."
uv venv --python 3.12 "$VENV"

echo "Installing svGrowth's dependencies..."
uv pip install --python "$VENV/bin/python" "numpy<2.4" scipy pandas pyyaml numba

echo
echo "Done. Verify with:"
echo "  SVGROWTH_DIR=/path/to/svGrowth uv run python comparison/run_svgrowth.py"
echo
echo "Set SVGROWTH_DIR to your svGrowth checkout (default: /Users/pfaller/repos/svGrowth)."
