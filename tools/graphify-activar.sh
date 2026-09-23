#!/usr/bin/env bash
# graphify-activar: deja graphify listo para Claude Code en el proyecto de la carpeta actual.
# Uso: entra a la carpeta del proyecto y ejecuta `graphify-activar`. Se puede repetir sin riesgo.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

command -v graphify >/dev/null 2>&1 || { echo "Falta graphify: ejecuta 'uv tool install graphifyy'" >&2; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Falta uv: https://docs.astral.sh/uv/" >&2; exit 1; }

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
if [ "$root" = "$HOME" ] || [ "$root" = "/" ]; then
  echo "Estás en tu carpeta personal. Entra primero a la carpeta del proyecto." >&2
  exit 1
fi
cd "$root"
echo "Activando graphify en: $root"

# 1. Skill /graphify, CLAUDE.md y hooks PreToolUse en modo estricto.
# --platform claude fuerza la variante Bash también en Windows (Claude Code usa Git Bash);
# si no, Windows instala la variante PowerShell y choca con la de WSL y la nube.
graphify install --project --strict --platform claude >/dev/null

# 2. Hook de inicio: instala graphify en la nube si falta y refresca el grafo.
mkdir -p .claude/hooks
cat > .claude/hooks/graphify-session-start.sh <<'EOF'
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
EOF
chmod +x .claude/hooks/graphify-session-start.sh
# Todo .claude/ en LF: bash no entiende los .sh con CRLF, y en Windows graphify
# escribe CRLF, lo que haría aparecer como modificados archivos idénticos.
printf '* text=auto eol=lf\n' > .claude/.gitattributes

# 3. Hooks SessionStart y PostToolUse (grafo al día tras cada edición de Claude).
uv run --no-project --quiet python - <<'EOF'
import json, pathlib
p = pathlib.Path(".claude/settings.json")
d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
hooks = d.setdefault("hooks", {})
def put(event, entry):
    kept = [e for e in hooks.get(event, []) if "graphify" not in json.dumps(e)]
    hooks[event] = kept + [entry]
put("SessionStart", {"hooks": [{"type": "command",
    "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/graphify-session-start.sh\"", "timeout": 300}]})
put("PostToolUse", {"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{"type": "command",
    "command": "cd \"$CLAUDE_PROJECT_DIR\" && graphify update . --force >/dev/null 2>&1; exit 0", "timeout": 60}]})
p.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
EOF

# 4. El grafo no se versiona: cada entorno genera el suyo.
touch .gitignore
grep -qxF 'graphify-out/' .gitignore || printf '\n# graphify: cada entorno genera su propio grafo\ngraphify-out/\n' >> .gitignore
# Copias de seguridad que graphify deja al modificar .claude/settings.json.
grep -qxF '*.graphify-bak' .gitignore || printf '*.graphify-bak\n' >> .gitignore
[ -f .graphifyignore ] || printf '# Archivos de la herramienta, no del proyecto\n.claude/\nCLAUDE.md\ngraphify-out/\n' > .graphifyignore

# 5. Hooks de git: rehacen el grafo en cada commit y cambio de rama.
if git rev-parse --git-dir >/dev/null 2>&1; then
  had_attrs=0; [ -f .gitattributes ] && had_attrs=1
  graphify hook install >/dev/null
  # El merge driver de graph.json sobra porque graphify-out/ no se versiona.
  if [ -f .gitattributes ]; then
    grep -vxF 'graphify-out/graph.json merge=graphify' .gitattributes > .gitattributes.tmp || true
    if [ "$had_attrs" = 0 ] && [ ! -s .gitattributes.tmp ]; then rm -f .gitattributes .gitattributes.tmp
    else mv .gitattributes.tmp .gitattributes; fi
  fi
fi

# 6. Primer grafo.
graphify update . --force 2>&1 | grep -i 'rebuilt' || true
# Que git no marque como modificados archivos que solo difieren en saltos de línea.
git update-index -q --refresh >/dev/null 2>&1 || true

echo
echo "Listo. Para que también funcione en el celular, sube la configuración:"
echo "  git add .claude CLAUDE.md .gitignore .graphifyignore"
echo "  git commit -m \"chore: activar graphify\""
echo "  git push"
