#!/usr/bin/env python3
"""Trae de farmasius.com la foto, el nombre oficial y las reseñas de cada producto de la asesora.

Lee asesora/catalogo.json (qué productos puede recomendar y su texto en español) y escribe
asesora/tienda.json y las fotos en asesora/img/. Se corre una vez, y otra vez cuando se
agregue un producto al catálogo o se quiera refrescar las reseñas.

Uso:
  python3 asesora/preparar.py              # todos (unos 40 segundos)
  python3 asesora/preparar.py --sin-fotos  # solo nombres y reseñas

Solo usa la librería estándar de Python (y el lector de lector-farmasi/).
"""
import argparse
import datetime
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'lector-farmasi'))
import leer  # noqa: E402

FOTOS = AQUI / 'img'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--sin-fotos', action='store_true', help='no vuelve a bajar las fotos')
    a = ap.parse_args()

    catalogo = json.loads((AQUI / 'catalogo.json').read_text(encoding='utf-8'))['productos']
    mapa = leer.mapa_productos()
    FOTOS.mkdir(exist_ok=True)
    tienda, fallos = {}, []
    for item in catalogo:
        try:
            d = leer.leer_producto(leer.resolver(item['codigo'], mapa))
        except Exception as e:  # noqa: BLE001  (un producto que falla no frena a los demás)
            fallos.append(f"{item['nombre']}: {e}")
            continue
        foto = next(iter(FOTOS.glob(item['id'] + '.*')), None)
        if not (foto and a.sin_fotos) and d['imagenes_url']:
            foto = leer.bajar_foto(d['imagenes_url'][0], FOTOS / item['id'], ancho=384) or foto
            time.sleep(leer.PAUSA)
        r = d['resenas']
        tienda[item['id']] = {'codigo': d['codigo'], 'oficial': d['nombre'], 'fuente': d['fuente'],
                              'nota': r['promedio'], 'resenas': r['cantidad'], 'contenido': d['contenido'],
                              'foto': f'img/{foto.name}' if foto else ''}
        print(f"{item['nombre']}: {r['promedio']}★ · {r['cantidad']} reseñas" + ('' if foto else ' · sin foto'))
        time.sleep(leer.PAUSA)
    salida = {'leido': datetime.date.today().isoformat(), 'productos': tienda}
    (AQUI / 'tienda.json').write_text(json.dumps(salida, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'\nListo: {len(tienda)} productos en asesora/tienda.json')
    for f in fallos:
        print('No se pudo leer:', f)


if __name__ == '__main__':
    main()
