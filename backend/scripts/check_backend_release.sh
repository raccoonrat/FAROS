#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"
python -m py_compile $(find app -name '*.py') $(find tests -name '*.py')
pytest -q
python - <<'PY2'
import sys
sys.path.insert(0, '.')
from app.main import app
print(app.title, app.version)
PY2
