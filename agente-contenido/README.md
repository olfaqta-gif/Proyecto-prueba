# Agente de contenido Farmasi

Convierte un producto en un **anuncio vertical de 15 segundos** (1080×1920, para Reels,
TikTok y Stories) con música y efectos propios, más el **caption** listo para pegar.

Nace del anuncio `anuncio-farmasi` (rama `claude/anuncio-farmasi`): mismo estilo visual,
misma técnica de render cuadro por cuadro y el mismo sintetizador de sonido, pero ahora
como plantilla. Cambiar de producto es cambiar una ficha, no el código.

```
ficha.json + foto  ──►  generar.py  ──►  anuncio.html   (animación, se abre en el navegador)
                                     ├─►  caption.txt    (texto + hashtags + aviso)
                                     ├─►  previa.jpg     (5 cuadros para revisar)
                                     └─►  anuncio.mp4    (con --video: 30 fps + audio)
```

## Uso rápido

```bash
cd agente-contenido
python3 generar.py productos/vitamin-c-glow-serum            # previa + caption
python3 generar.py productos/vitamin-c-glow-serum --video    # + MP4 final
```

Con Claude Code basta con pedir *"hazme un anuncio del <producto>"*: la skill
`.claude/skills/anuncio-producto` guía al agente por todo el flujo (investigar, escribir
la ficha, revisar la previa, renderizar y entregar).

## El anuncio, escena por escena

| Tiempo | Escena | Qué muestra |
|---|---|---|
| 0 – 2.7 s | Gancho | Problema o deseo de la clienta + respuesta en cursiva |
| 2.7 – 6.3 s | Producto | Foto en halo blanco, categoría, nombre, calificación |
| 6.4 – 10.2 s | Beneficios | 2 o 3 beneficios con check sobre fondo de color |
| 10.3 – 15 s | Cierre | FARMASi, producto, frase final, botón "Escríbeme “PALABRA”", aviso legal |

Los tiempos están en `plantilla/tiempos.json`. Lo usan tanto la animación como el
sonido, así que si se mueve un tiempo, el efecto de sonido se mueve con él.

## La ficha (`productos/<slug>/ficha.json`)

| Campo | Para qué | Largo recomendado |
|---|---|---|
| `paleta` | `coral`, `dorado`, `verde`, `lavanda` o `rosa` | — |
| `imagen` | archivo de la foto en la misma carpeta (jpg, png, webp) | — |
| `gancho.kicker` | etiqueta pequeña arriba ("Piel grasa o mixta") | 32 |
| `gancho.linea1` | el problema o deseo | 40 |
| `gancho.linea2` | la respuesta (cursiva) | 28 |
| `producto.categoria` | "Sérum facial" | 24 |
| `producto.nombre` | nombre comercial | 34 |
| `producto.nombre_corto` | línea de marca en la escena de beneficios | 30 |
| `producto.dato` | opcional: `{"destacado": "★★★★★", "texto": "4.97 · 980 reseñas"}` | — |
| `beneficios.titulo` | "Lo que vas a notar" | 40 |
| `beneficios.lista` | 2 o 3 beneficios | 34 c/u |
| `cierre.frase1` / `frase2` | frase final en dos partes | 24 c/u |
| `cierre.precio` | opcional: precio u oferta | 40 |
| `cierre.boton_pre` + `palabra` | "Escríbeme" + palabra clave | 12 |
| `cierre.usuario` | opcional: @usuario | — |
| `cierre.aviso` | aviso legal en letra pequeña | — |
| `caption.texto` | caption completo (usa `\n` para saltos) | — |
| `caption.hashtags` | lista sin `#`, máx. 30 | — |
| `caption.aviso` | opcional: aviso al final del caption | — |
| `voz` | opcional: `{"archivo": "voz.mp3", "inicio": 0.3, "guion": "…"}` | — |

Los campos opcionales vacíos desaparecen del video. Si un texto es más largo que lo
recomendado, la letra se achica sola para que quepa, y el script avisa.

## Archivos

- `generar.py` — valida la ficha y produce todo lo de `salida/<slug>/` (carpeta ignorada por git).
- `plantilla/anuncio.template.html` — diseño y animaciones; las paletas están al inicio del CSS.
- `plantilla/tiempos.json` — línea de tiempo compartida por video y sonido.
- `plantilla/fonts/fonts.css` — Montserrat y Playfair Display embebidas (el render no usa internet).
- `sonido.py` — música (100 bpm) y efectos sintetizados, sin samples ni licencias.
- `render.cjs` — captura los cuadros con Chromium (Playwright).
- `productos/` — una carpeta por producto. Hay dos ejemplos.

## Requisitos

`python3` con `numpy` y `scipy`, `node` con `playwright`, y `ffmpeg`.

## ¿Y HyperFrames?

Para piezas más largas o con otro formato (explicadores de 30–90 s, presentaciones,
videos que combinan clips grabados) siguen estando los proyectos HyperFrames de las ramas
`claude/heygen-hyperframes-skill-*` y `claude/loving-lamport-*`. Esta plantilla es la vía
rápida para el contenido diario de producto: no necesita instalar nada de HyperFrames ni
conexión a internet para renderizar.
