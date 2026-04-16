#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/setup_venv_py310.sh /ruta/a/python3.10
#
# Example:
#   ./scripts/setup_venv_py310.sh /opt/alt/python310/bin/python3.10

if [[ $# -lt 1 ]]; then
  echo "Error: debes indicar la ruta absoluta al binario python3.10"
  echo "Uso: $0 /ruta/a/python3.10"
  exit 1
fi

PYTHON310_BIN="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv310"

if [[ ! -x "$PYTHON310_BIN" ]]; then
  echo "Error: no se puede ejecutar $PYTHON310_BIN"
  exit 1
fi

echo "Creando venv en $VENV_DIR con $PYTHON310_BIN"
"$PYTHON310_BIN" -m venv "$VENV_DIR"

echo "Instalando dependencias"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements.txt"

echo "OK. Venv listo:"
echo "  $VENV_DIR"
echo "Python usado:"
"$VENV_DIR/bin/python" --version
