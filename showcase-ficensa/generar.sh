#!/usr/bin/env bash
# Genera un video completo (audio + cuadros + MP4).
#   ./generar.sh [16x9|9x16] [completa|corta] [hilos]
set -euo pipefail
cd "$(dirname "$0")"
FORMATO=${1:-16x9}; VERSION=${2:-completa}; HILOS=${3:-6}
export FORMATO VERSION NODE_PATH=${NODE_PATH:-/opt/node22/lib/node_modules}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
mkdir -p salida
node render.cjs eventos "$TMP/eventos.json"
python3 musica.py "$TMP/eventos.json" "$TMP/audio.wav"
node render.cjs video "$TMP/f" "$HILOS" > /dev/null
SAL="salida/showcase-apertura-cuenta-${VERSION}-${FORMATO}.mp4"
ffmpeg -v error -y -framerate 30 -i "$TMP/f/f_%05d.jpg" -i "$TMP/audio.wav" -c:v libx264 -pix_fmt yuv420p -crf 19 \
  -preset medium -c:a aac -b:a 192k -shortest -movflags +faststart "$SAL"
echo "$SAL"
