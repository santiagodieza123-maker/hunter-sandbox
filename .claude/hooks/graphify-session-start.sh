#!/bin/bash
# Deja graphify listo al iniciar sesión y refresca el grafo (solo AST, sin coste de API).
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
if ! command -v graphify >/dev/null 2>&1 && [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  if command -v uv >/dev/null 2>&1; then uv tool install -q graphifyy >/dev/null 2>&1
  else pip install -q --user graphifyy >/dev/null 2>&1; fi
fi
if command -v graphify >/dev/null 2>&1; then
  cd "${CLAUDE_PROJECT_DIR:-.}" && graphify update . --force >/dev/null 2>&1
else
  echo "graphify no está instalado: ejecuta 'uv tool install graphifyy'" >&2
fi
exit 0
