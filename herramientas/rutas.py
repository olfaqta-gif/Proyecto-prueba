"""Hace que los programas del equipo encuentren lo que instaló herramientas/instalar_videos.py
(node y ffmpeg dentro de la carpeta herramientas/), sin tocar nada de la computadora.

Uso, al principio de cualquier programa que llame a node o a ffmpeg:
    sys.path.insert(0, str(RAIZ / 'herramientas')); import rutas; rutas.preparar()
"""
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WINDOWS = sys.platform.startswith('win')
NODE = AQUI / 'node'
BIN = AQUI / 'bin'


def carpetas():
    """Las carpetas con programas instalados aquí, las que existan."""
    node = NODE if WINDOWS else NODE / 'bin'
    return [str(c) for c in (node, BIN) if c.is_dir()]


def preparar():
    """Las pone primero en el PATH de este programa (y de lo que él abra)."""
    actuales = os.environ.get('PATH', '').split(os.pathsep)
    nuevas = [c for c in carpetas() if c not in actuales]
    if nuevas:
        os.environ['PATH'] = os.pathsep.join(nuevas + actuales)
