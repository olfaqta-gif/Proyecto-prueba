#!/usr/bin/env python3
"""Prepara los productos de la página de Isabella con datos frescos de farmasius.com.

Lee sitio/productos.json (qué productos van y su texto en español), trae de la tienda
el nombre oficial, las reseñas, los tonos y hasta 3 fotos de cada uno, y escribe
sitio/productos.js, que es lo que usa la página.

Uso:
  python3 sitio/preparar.py            # todos
  python3 sitio/preparar.py --sin-fotos

Solo usa la librería estándar de Python (y el lector de lector-farmasi/).
"""
import argparse
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'lector-farmasi'))
import leer  # noqa: E402

FOTOS = AQUI / 'img' / 'productos'
MAX_FOTOS = 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--sin-fotos', action='store_true', help='no vuelve a bajar las fotos')
    a = ap.parse_args()

    lista = json.loads((AQUI / 'productos.json').read_text(encoding='utf-8'))['productos']
    mapa = leer.mapa_productos()
    FOTOS.mkdir(parents=True, exist_ok=True)
    salida = []
    for item in lista:
        d = leer.leer_producto(leer.resolver(item['codigo'], mapa))
        fotos = []
        quitar = set(item.get('quitar_fotos', []))
        buenas = [(i, u) for i, u in enumerate(d['imagenes_url'], 1) if i not in quitar][:MAX_FOTOS]
        for i, url in buenas:
            base = FOTOS / f"{item['id']}-{i}"
            ya = next(iter(FOTOS.glob(base.name + '.*')), None)
            f = ya if (ya and a.sin_fotos) else leer.bajar_foto(url, base, ancho=828)
            if f:
                fotos.append(f'img/productos/{f.name}')
            time.sleep(leer.PAUSA)
        tonos = [t['nombre'] for t in d['tonos'] if t.get('disponible') is not False]
        r = d['resenas']
        salida.append({
            **{k: v for k, v in item.items() if k not in ('codigo', 'quitar_fotos')},
            'codigo': d['codigo'], 'marca': (d['marca'] or 'Farmasi').replace('Farmasi MUP', 'Farmasi'), 'oficial': d['nombre'],
            'fuente': d['fuente'], 'nota': r['promedio'], 'resenas': r['cantidad'],
            'tonos': tonos, 'contenido': d['contenido'], 'fotos': fotos,
            'vegano': any('vegan' in x.lower() for x in d['atributos']),
        })
        print(f"{item['nombre']}: {r['promedio']}★ · {r['cantidad']} reseñas · {len(fotos)} fotos"
              + (f' · {len(tonos)} tonos' if tonos else ''))
        time.sleep(leer.PAUSA)

    js = ('// Lo genera sitio/preparar.py con datos de farmasius.com. No editar a mano:\n'
          '// el texto en español se cambia en sitio/productos.json.\n'
          f'window.PRODUCTOS = {json.dumps(salida, ensure_ascii=False, indent=1)};\n'
          f"window.PRODUCTOS_LEIDO = '{salida and leer.datetime.date.today().isoformat()}';\n")
    (AQUI / 'productos.js').write_text(js, encoding='utf-8')
    print(f'\nListo: {len(salida)} productos en sitio/productos.js')


if __name__ == '__main__':
    main()
