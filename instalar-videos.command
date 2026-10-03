#!/bin/bash
cd "$(dirname "$0")"
python3 herramientas/instalar_videos.py
echo
read -n 1 -s -r -p "Presiona cualquier tecla para cerrar esta ventana."
