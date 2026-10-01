# Lector de productos Farmasi (farmasius.com)

Lee la ficha oficial de cualquier producto de la tienda de Farmasi US y la guarda como
`datos.json` + `producto.jpg` (foto 1080×1080 sobre fondo blanco). Es la materia prima
del agente de contenido (`agente-contenido/`): los datos son verdaderos y con fuente, y el
agente solo escribe el copy en español.

Solo usa Python 3 (librería estándar). No necesita navegador: cada página de producto
trae sus datos completos en el HTML.

## Uso

```bash
cd lector-farmasi

# Buscar productos por nombre (usa el mapa del sitio, ~630 productos)
python3 leer.py buscar "tea tree"

# Leer uno o varios: por código (pid), URL o palabras únicas del nombre
python3 leer.py producto 1000290 1002167
python3 leer.py producto "vitamin c glow serum"

# Guardar directo en la carpeta de productos del agente de contenido
python3 leer.py producto 1000290 --destino ../agente-contenido/productos

# Los 3 con mejores reseñas (crea salida/vitrina.html con fotos)
python3 leer.py mejores 3
python3 leer.py mejores 5 --filtro "dr c tuna"

# Todo el catálogo (o una parte) en un solo catalogo.json
python3 leer.py catalogo --filtro "dr c tuna" --destino salida
python3 leer.py catalogo            # los ~630, tarda unos minutos
```

## Qué trae `datos.json`

| Campo | Ejemplo |
|---|---|
| `nombre`, `marca`, `codigo`, `fuente` | "Dr. C. Tuna Tea Tree Face Cream", "Dr. C. Tuna", "1000290", URL |
| `descripcion`, `resultados_declarados` | texto oficial (en inglés) |
| `ingredientes_clave` | activos y para qué sirven |
| `ingredientes_inci` | lista completa de ingredientes |
| `modo_de_uso`, `precauciones`, `atributos`, `contenido` | vegano, sin parabenos, 30 ml… |
| `resenas` | `promedio` (4.95) y `cantidad` (496) |
| `tonos` | para maquillaje: cada tono con su código y si hay stock |
| `para_ficha` | con la misma forma de `ficha.json`: `imagen` y `producto` (`nombre`, `nombre_corto`, `dato` con ★ y reseñas) |

Los precios no se leen a propósito (se manejan aparte). `leido` guarda la fecha de lectura.
Las reseñas individuales (textos) no vienen en la página; solo el promedio y la cantidad.

## Notas

- Las fotos se bajan por el optimizador de imágenes de `www.farmasius.com`, porque el
  servidor de contenido (`content.farmasius.com`) puede estar bloqueado desde la nube.
- Pausa de 0.6 s entre páginas para no cargar la tienda.
- Redes sociales (Instagram/TikTok) quedan fuera: sus términos prohíben el scraping.
