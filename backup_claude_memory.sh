#!/usr/bin/env bash
#
# backup_claude_memory.sh — Respaldo de la memoria y configuración de Claude CLI.
#
# Empaqueta en un solo .tar.gz (con fecha) todo lo valioso y NO versionado:
#   - ~/.claude/projects/*/memory/   (todas las memorias y sus MEMORY.md)
#   - ~/.claude/settings.json, keybindings.json, statusline-command.sh
#   - los CLAUDE.md de ~/Dev (referencia; ya están en git, pero se incluyen)
#
# Uso:
#   ./backup_claude_memory.sh                 # guarda en ~/Documents/ClaudeBackups (iCloud)
#   ./backup_claude_memory.sh /Volumes/MiDisco/ClaudeBackups   # a un disco externo
#
set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
DEV_DIR="$HOME/Dev"
# Destino por defecto: carpeta Documents del usuario (sincronizada con iCloud).
DEST="${1:-$HOME/Documents/ClaudeBackups}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
ARCHIVE="$DEST/claude-memory-backup_$STAMP.tar.gz"

mkdir -p "$DEST"

# Área de staging temporal para armar una estructura limpia dentro del tar.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
ROOT="$STAGE/claude-backup_$STAMP"
mkdir -p "$ROOT/claude-config" "$ROOT/dev-CLAUDE.md"

# 1) Todas las carpetas memory/ (lo más importante), conservando el nombre del proyecto.
echo "→ Copiando memorias..."
found_mem=0
while IFS= read -r -d '' mem; do
  proj="$(basename "$(dirname "$mem")")"
  mkdir -p "$ROOT/memory/$proj"
  cp -a "$mem/." "$ROOT/memory/$proj/"
  echo "   • $proj"
  found_mem=1
done < <(find "$CLAUDE_DIR/projects" -type d -name memory -print0 2>/dev/null)
[ "$found_mem" -eq 0 ] && echo "   (no se encontraron carpetas memory/)"

# 2) Config de Claude (lo que exista).
echo "→ Copiando configuración..."
for f in settings.json settings.local.json keybindings.json statusline-command.sh; do
  if [ -f "$CLAUDE_DIR/$f" ]; then
    cp -a "$CLAUDE_DIR/$f" "$ROOT/claude-config/"
    echo "   • $f"
  fi
done

# 2b) LaunchAgent del backup automático (para poder recrearlo tras formatear).
LAUNCHD_SRC="$HOME/Library/LaunchAgents/com.darkesthj.claude-memory-backup.plist"
if [ -f "$LAUNCHD_SRC" ]; then
  mkdir -p "$ROOT/launchd"
  cp -a "$LAUNCHD_SRC" "$ROOT/launchd/"
  echo "→ Copiando LaunchAgent (backup semanal)..."
  echo "   • com.darkesthj.claude-memory-backup.plist"
fi

# 3) CLAUDE.md del árbol ~/Dev (referencia).
echo "→ Copiando CLAUDE.md de ~/Dev..."
while IFS= read -r -d '' cmd; do
  rel="${cmd#"$DEV_DIR"/}"
  mkdir -p "$ROOT/dev-CLAUDE.md/$(dirname "$rel")"
  cp -a "$cmd" "$ROOT/dev-CLAUDE.md/$rel"
  echo "   • $rel"
done < <(find "$DEV_DIR" -maxdepth 3 -name CLAUDE.md -print0 2>/dev/null)

# 4) Script de restauración autocontenido (viaja DENTRO del backup).
cat > "$ROOT/restore.sh" <<'RESTORE'
#!/usr/bin/env bash
# restore.sh — Restaura la memoria y config de Claude desde este backup.
# Ejecútalo desde la carpeta descomprimida:  ./restore.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Restaurando memoria de Claude a $CLAUDE_DIR ..."
if [ -d "$HERE/memory" ]; then
  for proj in "$HERE"/memory/*/; do
    [ -d "$proj" ] || continue
    name="$(basename "$proj")"
    target="$CLAUDE_DIR/projects/$name/memory"
    mkdir -p "$target"
    cp -a "$proj." "$target/"
    echo "  ✓ memory → projects/$name/memory"
  done
fi

if [ -d "$HERE/claude-config" ]; then
  mkdir -p "$CLAUDE_DIR"
  for f in "$HERE"/claude-config/*; do
    [ -e "$f" ] || continue
    cp -a "$f" "$CLAUDE_DIR/"
    echo "  ✓ config → $(basename "$f")"
  done
fi

if [ -d "$HERE/launchd" ]; then
  mkdir -p "$HOME/Library/LaunchAgents"
  for p in "$HERE"/launchd/*.plist; do
    [ -e "$p" ] || continue
    cp -a "$p" "$HOME/Library/LaunchAgents/"
    launchctl unload "$HOME/Library/LaunchAgents/$(basename "$p")" 2>/dev/null || true
    launchctl load -w "$HOME/Library/LaunchAgents/$(basename "$p")" 2>/dev/null || true
    echo "  ✓ backup semanal reactivado ($(basename "$p"))"
  done
fi

echo ""
echo "✅ Listo. Los CLAUDE.md de ~/Dev se restauran solos al clonar tus repos de git."
echo "   Abre Claude Code en ~/Dev/workspace y tu memoria estará de vuelta."
RESTORE
chmod +x "$ROOT/restore.sh"

# 5) Manifiesto legible con fecha e inventario.
{
  echo "Backup de memoria Claude CLI"
  echo "Fecha: $(date)"
  echo "Equipo: $(hostname)"
  echo ""
  echo "Contenido:"
  find "$ROOT" -type f | sed "s|$ROOT/|  |" | sort
} > "$ROOT/MANIFEST.txt"

# 5) Empaquetar.
echo "→ Comprimiendo..."
tar -czf "$ARCHIVE" -C "$STAGE" "claude-backup_$STAMP"

# 7) Retención: conservar solo los 12 backups más recientes en el destino.
KEEP=12
ls -t "$DEST"/claude-memory-backup_*.tar.gz 2>/dev/null | tail -n +$((KEEP+1)) | while IFS= read -r old; do
  rm -f "$old" && echo "→ Borrado backup antiguo: $(basename "$old")"
done

echo ""
echo "✅ Backup creado:"
echo "   $ARCHIVE"
echo "   Tamaño: $(du -h "$ARCHIVE" | cut -f1)"
echo ""
echo "Para restaurar: tar -xzf <archivo>.tar.gz  y copia las carpetas memory/<proyecto>"
echo "de vuelta a ~/.claude/projects/<proyecto>/memory/"
