#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_PATH="$ROOT_DIR/.venv/bin/activate"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Asegura que Python ve raíz y carpeta superior (opción B que elegiste)
export PYTHONPATH="$ROOT_DIR:$(dirname "$ROOT_DIR"):${PYTHONPATH:-}"

# Activa venv
if [[ ! -f "$ENV_PATH" ]]; then
  echo "No existe el entorno en $ENV_PATH"; exit 1
fi
source "$ENV_PATH"

echo "[Docker] down/up --build -d"
docker compose down -v || true
docker compose up --build -d

echo "[LM Studio] en background -> $LOG_DIR/lmstudio.log"
../squashfs-root/./lm-studio > "$LOG_DIR/lmstudio.log" 2>&1 & echo $! > "$LOG_DIR/lmstudio.pid"

echo "[Consumer] en background -> $LOG_DIR/consumer.log"
# Nota: ejecuta desde ROOT_DIR para que los imports funcionen
( cd "$ROOT_DIR" && python consumer/whatsapp_consumer.py ) > "$LOG_DIR/consumer.log" 2>&1 & echo $! > "$LOG_DIR/consumer.pid"

# Evita doble instancia del bot (mismo auth)
if [[ -f "$LOG_DIR/node-bot.pid" ]] && ps -p "$(cat "$LOG_DIR/node-bot.pid")" >/dev/null 2>&1; then
  echo "[Node bot] ya estaba ejecutándose (PID $(cat "$LOG_DIR/node-bot.pid"))."
  echo "Saliendo sin lanzar otra instancia para evitar 'replaced (440)'."
  exit 0
fi

echo
echo "Logs en tiempo real (Ctrl+C para volver a la consola):"
echo "  tail -f $LOG_DIR/lmstudio.log $LOG_DIR/consumer.log"
echo

# === AQUÍ VA EN PRIMER PLANO ===
echo "[Node bot] en PRIMER PLANO. Verás el QR aquí. Ctrl+C para parar el bot."
cd "$ROOT_DIR"
# No redirigimos ni ponemos '&' para que quede en foreground
node whatsapp-bot/index.js
