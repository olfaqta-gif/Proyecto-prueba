#!/usr/bin/env python3
"""Deja lista la computadora para hacer los videos (anuncios y educativos) y las imágenes.

Instala, solo para este equipo y gratis:
  - numpy y scipy (la música de los videos)
  - ffmpeg (arma el video con su música)
  - node y playwright con Chromium (toma los cuadros del video y las imágenes)

node y ffmpeg quedan dentro de la carpeta herramientas/, así que no cambia nada más de la
computadora ni pide la contraseña. Si ya están instalados, los usa.

Uso (desde la carpeta del equipo):
  python3 herramientas/instalar_videos.py            # instala lo que falte
  python3 herramientas/instalar_videos.py --revisar  # solo dice qué hay y qué falta
Solo librería estándar.
"""
import argparse
import hashlib
import json
import platform
import shutil
import ssl
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import rutas  # noqa: E402

WINDOWS = rutas.WINDOWS
NODE_LINEA = 'latest-v22.x'
NODE_SITIO = f'https://nodejs.org/dist/{NODE_LINEA}/'
PAQUETES_PY = ['numpy', 'scipy']


def decir(texto=''):
    print(texto, flush=True)


def correr(comando, **kw):
    return subprocess.run(comando, capture_output=True, text=True, **kw)


# ---------- revisar ----------
def hay_modulo(nombre):
    return correr([sys.executable, '-c', f'import {nombre}']).returncode == 0


def version_node():
    node = shutil.which('node')
    if not node:
        return None
    r = correr([node, '--version'])
    try:
        return int(r.stdout.strip().lstrip('v').split('.')[0])
    except ValueError:
        return None


def hay_playwright():
    return (RAIZ / 'node_modules' / 'playwright' / 'package.json').exists()


def hay_chromium():
    node = shutil.which('node')
    if not node or not hay_playwright():
        return False
    js = "const {chromium}=require('playwright');console.log(require('fs').existsSync(chromium.executablePath()))"
    return correr([node, '-e', js], cwd=RAIZ).stdout.strip() == 'true'


def revisar():
    rutas.preparar()
    v = version_node()
    return {
        'música (numpy y scipy)': all(hay_modulo(p) for p in PAQUETES_PY),
        'armar videos (ffmpeg)': bool(shutil.which('ffmpeg')),
        'node': bool(v and v >= 18),
        'playwright': hay_playwright(),
        'Chromium': hay_chromium(),
    }


def mostrar(estado):
    for nombre, ok in estado.items():
        decir(f'  {"✅" if ok else "⬜"} {nombre}')


# ---------- bajar archivos ----------
def bajar(url, destino):
    """Baja con Python; si la computadora no acepta el certificado, prueba con curl."""
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(destino, 'wb') as f:
            shutil.copyfileobj(r, f)
        return
    except (ssl.SSLError, urllib.error.URLError) as e:
        curl = shutil.which('curl')
        if not curl:
            raise RuntimeError(f'No pude bajar {url} ({e}). Revisa el internet y vuelve a intentar.')
    r = correr([curl, '-fsSL', '-o', str(destino), url])
    if r.returncode:
        raise RuntimeError(f'No pude bajar {url}. Revisa el internet y vuelve a intentar.')


def texto(url):
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / 'x'
        bajar(url, f)
        return f.read_text(encoding='utf-8')


# ---------- instalar ----------
def pip(*paquetes):
    base = [sys.executable, '-m', 'pip', 'install', '--user', '--disable-pip-version-check', *paquetes]
    r = correr(base)
    if r.returncode and 'externally-managed' in (r.stderr + r.stdout):
        r = correr(base + ['--break-system-packages'])
    if r.returncode and 'No module named pip' in r.stderr:
        correr([sys.executable, '-m', 'ensurepip', '--user'])
        r = correr(base)
    if r.returncode:
        raise RuntimeError('No se pudieron instalar ' + ', '.join(paquetes) + ':\n' + (r.stderr or r.stdout)[-800:])


def instalar_python():
    faltan = [p for p in PAQUETES_PY if not hay_modulo(p)]
    if not faltan:
        return
    decir('🎵 Instalando lo de la música (' + ', '.join(faltan) + ')… puede tardar unos minutos.')
    pip(*faltan)


def instalar_ffmpeg():
    if shutil.which('ffmpeg'):
        return
    decir('🎬 Instalando ffmpeg, el que arma los videos…')
    pip('imageio-ffmpeg')
    r = correr([sys.executable, '-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'])
    origen = Path(r.stdout.strip())
    if r.returncode or not origen.is_file():
        raise RuntimeError('No encontré ffmpeg después de instalarlo.')
    rutas.BIN.mkdir(parents=True, exist_ok=True)
    destino = rutas.BIN / ('ffmpeg.exe' if WINDOWS else 'ffmpeg')
    shutil.copy2(origen, destino)
    destino.chmod(destino.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    rutas.preparar()


def archivo_node():
    maquina = platform.machine().lower()
    arm = maquina in ('arm64', 'aarch64')
    if sys.platform == 'darwin':
        return f'darwin-{"arm64" if arm else "x64"}.tar.gz'
    if WINDOWS:
        return f'win-{"arm64" if arm else "x64"}.zip'
    return f'linux-{"arm64" if arm else "x64"}.tar.xz'


def instalar_node():
    v = version_node()
    if v and v >= 18:
        return
    decir('🧩 Bajando node (gratis, de nodejs.org)…')
    final = archivo_node()
    sumas = texto(NODE_SITIO + 'SHASUMS256.txt')
    linea = next((l.split() for l in sumas.splitlines() if l.endswith(final)), None)
    if not linea:
        raise RuntimeError('No encontré node para esta computadora en nodejs.org.')
    suma, nombre = linea
    with tempfile.TemporaryDirectory() as tmp:
        paquete = Path(tmp) / nombre
        bajar(NODE_SITIO + nombre, paquete)
        if hashlib.sha256(paquete.read_bytes()).hexdigest() != suma:
            raise RuntimeError('El archivo de node llegó dañado. Vuelve a intentar.')
        decir('   Descomprimiendo…')
        abierto = Path(tmp) / 'abierto'
        if nombre.endswith('.zip'):
            with zipfile.ZipFile(paquete) as z:
                z.extractall(abierto)
        else:
            with tarfile.open(paquete) as t:
                if hasattr(tarfile, 'tar_filter'):
                    t.extractall(abierto, filter='tar')
                else:
                    t.extractall(abierto)
        carpeta = next(abierto.iterdir())
        shutil.rmtree(rutas.NODE, ignore_errors=True)
        shutil.move(str(carpeta), str(rutas.NODE))
    rutas.preparar()


def npm():
    """npm, el de la computadora o el que vino con node en herramientas/."""
    for cli in (rutas.NODE / 'lib' / 'node_modules' / 'npm' / 'bin' / 'npm-cli.js',
                rutas.NODE / 'node_modules' / 'npm' / 'bin' / 'npm-cli.js'):
        if cli.exists():
            return [shutil.which('node'), str(cli)]
    encontrado = shutil.which('npm')
    if not encontrado:
        raise RuntimeError('No encontré npm junto a node.')
    return [encontrado]


def instalar_playwright():
    node = shutil.which('node')
    if not hay_playwright():
        decir('📸 Instalando playwright, el que toma los cuadros de los videos…')
        r = correr(npm() + ['install', '--no-audit', '--no-fund'], cwd=RAIZ)
        if r.returncode:
            raise RuntimeError('No se pudo instalar playwright:\n' + (r.stderr or r.stdout)[-800:])
    if not hay_chromium():
        decir('🌐 Bajando Chromium (el navegador que usa playwright)… es lo más pesado, ten paciencia.')
        r = correr([node, str(RAIZ / 'node_modules' / 'playwright' / 'cli.js'), 'install', 'chromium'], cwd=RAIZ)
        if r.returncode:
            raise RuntimeError('No se pudo bajar Chromium:\n' + (r.stderr or r.stdout)[-800:])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--revisar', action='store_true', help='solo decir qué hay y qué falta')
    a = p.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')  # ventanas que no muestran emojis

    estado = revisar()
    if a.revisar:
        decir('Para hacer videos:')
        mostrar(estado)
        decir('Todo listo para hacer videos.' if all(estado.values())
              else 'Falta algo. Para instalarlo: python3 herramientas/instalar_videos.py')
        return 0 if all(estado.values()) else 1
    if all(estado.values()):
        decir('✅ Ya está todo listo para hacer videos. No hace falta instalar nada.')
        return 0

    decir('Voy a dejar tu computadora lista para hacer videos. Todo es gratis.')
    decir('No cierres esta ventana hasta que diga "Listo".\n')
    try:
        instalar_python()
        instalar_ffmpeg()
        instalar_node()
        instalar_playwright()
    except RuntimeError as e:
        decir(f'\n❌ {e}\n\nNo pasa nada: vuelve a abrir el instalador y sigue donde quedó. '
              'Si vuelve a fallar, mándale este mensaje a tu asistente.')
        return 1

    estado = revisar()
    decir('')
    mostrar(estado)
    if all(estado.values()):
        decir('\n🎉 Listo. Ya puedes pedirle videos a tu asistente.')
        return 0
    decir('\nFalta algo de la lista. Vuelve a abrir el instalador; si sigue igual, cuéntale a tu asistente.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
