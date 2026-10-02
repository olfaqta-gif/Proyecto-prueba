# Agente educativo Farmasi (el Profe)

Hace el contenido que **enseña o entretiene**, no el que anuncia: tips, mito vs realidad,
rutinas paso a paso y datos curiosos. Sale como **reel con motion graphics** (texto que
entra palabra por palabra, palabras resaltadas con marcador, íconos que se dibujan solos,
números que suben, transiciones de círculo, cortina y empuje) con **su propia música**,
en 4 formatos, y si se pide también como **carrusel** de imágenes.

```
guion.json  ──►  generar.py  ──►  caption.txt
                              └─►  video-<formato>.html / previa-<formato>.jpg / video-<formato>.mp4
                              └─►  carrusel/01.jpg, 02.jpg …        (con --carrusel)
```

Lo usa el agente `creador-educativo` (`.claude/agents/creador-educativo.md`), que Isa
llama cuando Isabella pide contenido educativo. Los anuncios de producto siguen siendo
del agente de contenido (`agente-contenido/`).

## Uso rápido

```bash
cd agente-educativo
python3 generar.py temas/labial-que-dure                    # previas + caption
python3 generar.py temas/labial-que-dure --video            # + los MP4 con música
python3 generar.py temas/labial-que-dure --carrusel         # + las imágenes del carrusel (4:5)
python3 generar.py temas/labial-que-dure --formatos 9x16    # solo ese formato
python3 generar.py temas/labial-que-dure --variacion 2      # otra canción, otras transiciones
```

## Las 4 formas (`tipo`)

| Forma | Cómo se ve | Ítems |
|---|---|---|
| `tips` | Número grande en el gancho; cada tip con medalla e ícono que se dibuja, "TIP 01" que golpea, barra de progreso tipo historia; fondos que alternan de color | 2 a 5 |
| `mito` | "MITO o REALIDAD" que chocan; tarjeta con el mito, sello rojo **FALSO**, la tarjeta gira y aparece la realidad sobre fondo verde con un ✓ | 1 a 3 |
| `pasos` | Barra de pasos fija arriba que se va llenando; cada paso entra empujando al anterior, con su número gigante de fondo | 2 a 5 |
| `dato` | Signo **?** que gira; cada dato con una cifra que sube (o una palabra clave) y su fuente | 1 a 3 |

## Música: cada video suena distinto

`musica.py` arma una canción nueva para cada guion: sortea **ambiente** (`suave` lo-fi,
`fresco` pop, `energia` house, `brillante` pop de medio tiempo), **tono**, **velocidad**,
**progresión de acordes** y **patrón** de arpegio y batería. La batería entra justo en el
primer ítem, y los efectos caen en cada animación, afinados en el tono de la canción:
whoosh en cada transición, pop por palabra, tics que se aceleran mientras sube un número,
golpe en el sello de "FALSO", campanitas al acertar y en el botón final.

El mismo guion siempre suena igual (para poder repetir el render); `--variacion N` o
`"musica": {"variacion": N}` da otra canción, y `"musica": {"ambiente": "suave"}` fija el ambiente.

Los anuncios de producto también cambian ahora: cada producto saca su tono, acordes y
velocidad (ver `agente-contenido/sonido.py`).

## El guion (`temas/<slug>/guion.json`)

| Campo | Para qué |
|---|---|
| `tipo` | `tips`, `mito`, `pasos` o `dato` |
| `paleta` | `coral`, `dorado`, `verde`, `lavanda` o `rosa` (si falta, se sortea) |
| `fondo` | `claro` u `oscuro` (si falta, se sortea) |
| `gancho.kicker` | etiqueta pequeña ("Tips de maquillaje") |
| `gancho.titulo` | el título; `*palabra*` sale resaltada con marcador (≤ 60 caracteres) |
| `gancho.subtitulo` | opcional, una línea debajo |
| `items` | la lista (ver abajo) |
| `cierre.frase1` / `frase2` | frase final ("Guárdalo" / "para tu próximo look") |
| `cierre.accion` | `guardar`, `compartir`, `seguir` o `escribir` (con `cierre.palabra`) |
| `cierre.usuario`, `cierre.aviso` | opcionales |
| `producto` | opcional: `{"carpeta": "agente-contenido/productos/<slug>", "texto": "Lo que yo uso"}` sale al final con su foto |
| `caption` | `texto`, `hashtags` (sin #), `aviso` opcional |
| `formatos` | opcional, p. ej. `["9x16", "4x5"]` (defecto: los 4) |
| `musica` | opcional: `variacion` (número) y `ambiente` |
| `etiqueta` | opcional: cambia "Tip" / "Paso" / "Dato" |

Ítems por forma:

- `tips` y `pasos`: `titulo` (≤ 60), `detalle` (≤ 90, opcional), `icono`.
- `mito`: `mito` (≤ 90), `realidad` (≤ 150), `sello` opcional (defecto "FALSO").
- `dato`: `numero` + `unidad` (el número sube si es entero) **o** `clave` (palabra grande),
  `titulo`, `detalle`, `fuente` (obligatoria si hay número), `icono` si no hay número ni clave.

Íconos: `gota`, `agua`, `sol`, `luna`, `dormir`, `hoja`, `corazon`, `estrella`, `reloj`,
`chispa`, `escudo`, `cara`, `labios`, `ojo`, `frasco`, `vaso`, `taza`, `cabello`, `pincel`,
`calendario`, `bombilla`, `lupa`, `flecha`, `guardar`, `compartir`, `mensaje`, `regalo`,
`mano`, `check`, `x`.

La duración sale sola según cuánto texto hay (unos 3 a 5 segundos por ítem): un tips de 4
dura unos 25 s, un mito de 2 unos 22 s, un dato de 2 unos 18 s.

`generar.py` revisa el guion: frena palabras prohibidas ("cura", "elimina", "garantiza",
"adelgaza", promesas de dinero…), pide fuente para las cifras y avisa si un texto es largo.

## Ejemplos

`temas/labial-que-dure` (tips), `temas/mitos-piel-grasa` (mito, con la Tea Tree Face Cream al
final), `temas/rutina-de-noche` (pasos, con la All Night Beauty Mask) y
`temas/sabias-que-sol-y-labios` (dato).

## Archivos

- `generar.py`: valida el guion, calcula la línea de tiempo y produce todo en `salida/<slug>/` (ignorada por git).
- `musica.py`: la canción y los efectos de cada video.
- `plantilla/comun.html`: gancho y cierre; `plantilla/tipos/<forma>.html`: la insignia del gancho y la pantalla de cada ítem.
- `plantilla/edu.css` y `plantilla/edu.js`: transiciones, texto cinético, íconos, contadores y decoración.
- Reutiliza de `agente-contenido/`: `base.css`, `base.js`, las fuentes, `render.cjs` y los instrumentos de `sonido.py`.

Requisitos: los mismos que el agente de contenido (`python3` con `numpy` y `scipy`, `node`
con `playwright`, y `ffmpeg`).
