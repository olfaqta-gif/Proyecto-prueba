# Agente de contenido Farmasi

Convierte un producto en **anuncios de 15 segundos** con música y efectos propios, en
**3 estilos** y **4 formatos**, más el **caption** listo para pegar.

Nace del anuncio `anuncio-farmasi` (rama `claude/anuncio-farmasi`): misma técnica de render
cuadro por cuadro y el mismo sintetizador de sonido, pero como plantilla. Cambiar de
producto es cambiar una ficha, no el código.

```
ficha.json + foto  ──►  generar.py  ──►  caption.txt                    (texto + hashtags + aviso)
                                     └─►  <estilo>/anuncio-<formato>.html   (animación, se abre en el navegador)
                                          <estilo>/previa-<formato>.jpg     (cuadros clave para revisar)
                                          <estilo>/anuncio-<formato>.mp4    (con --video: 30 fps + audio)
```

## Uso rápido

```bash
cd agente-contenido
python3 generar.py productos/vitamin-c-glow-serum                      # previas + caption
python3 generar.py productos/vitamin-c-glow-serum --video              # + los MP4 (los 4 formatos)
python3 generar.py productos/vitamin-c-glow-serum --estilo todos       # los 3 estilos para comparar
python3 generar.py productos/vitamin-c-glow-serum --formatos 9x16,4x5  # solo esos formatos
```

Con Claude Code basta con pedir *"hazme un anuncio del <producto>"*: la skill
`.claude/skills/anuncio-producto` guía al agente por todo el flujo (investigar, escribir
la ficha, revisar la previa, renderizar y entregar).

## Lo que no cambia (el concepto)

En todos los estilos: la marca FARMASi, la foto real del producto, la paleta de colores,
el botón "Escríbeme “PALABRA”" al final y el aviso legal. Así todo se reconoce como tuyo
aunque cada video se vea distinto.

## Estilos

| Estilo | Sensación | Escenas | Música |
|---|---|---|---|
| `clasico` | Elegante, oscuro con brillos | Gancho (problema → respuesta) · producto en halo · beneficios con check · cierre | 100 bpm, electrónica con "drop" |
| `favorito` | "Te muestro mi favorito", tipo TikTok, fondo claro | Gancho palabra por palabra · foto en tarjeta con sticker de ★ · beneficios en recuadros de subtítulo · cierre | 118 bpm, pop alegre |
| `razones` | Directo y editorial | Número gigante "3 razones" · pantalla dividida con la foto · una razón por pantalla con barra tipo historia · cierre dividido | 84 bpm, lo-fi relajado |

Cada estilo vive en `plantilla/estilos/<estilo>/` (`plantilla.html` + `tiempos.json`) y
su música en `sonido.py`. Los tiempos los usan tanto la animación como el sonido, así que
si se mueve un tiempo, el efecto de sonido se mueve con él.

**Variar sin perder el concepto:** alterna estilos entre productos (o publica el mismo
producto en dos estilos distintos en días diferentes), cambia la paleta y escribe un gancho
nuevo para cada estilo con `estilos.<estilo>` en la ficha.

## Formatos

| Formato | Tamaño | Dónde se usa |
|---|---|---|
| `9x16` | 1080×1920 | Reels, TikTok, Stories, Shorts |
| `4x5` | 1080×1350 | Feed de Instagram y Facebook (el que más espacio ocupa en el feed) |
| `1x1` | 1080×1080 | Feed, anuncios, WhatsApp |
| `16x9` | 1920×1080 | YouTube, Facebook horizontal |

El diseño se reacomoda solo en cada formato (en horizontal el producto va a un lado y el
texto al otro). Por defecto salen los 4; `"formatos": ["9x16", "4x5"]` en la ficha o
`--formatos` en la línea de comando eligen menos.

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
| `estilo` | opcional: `clasico` (defecto), `favorito` o `razones` | — |
| `formatos` | opcional: lista, p. ej. `["9x16", "1x1"]` (defecto: los 4) | — |
| `estilos.<estilo>` | opcional: textos propios de un estilo; se ponen encima del resto de la ficha | — |

Ejemplo de `estilos` (ver `productos/nutriplus-serenity-earl-grey-tea/ficha.json`):

```json
"estilos": {
  "favorito": { "gancho": { "linea1": "El té que me tomo cada tarde", "linea2": "Y no lleva azúcar" } },
  "razones":  { "gancho": { "linea1": "razones para probar", "linea2": "este té" } }
}
```

En `razones` el número grande es la cantidad de beneficios (2 o 3) y cada beneficio es
una razón; conviene escribirlas un poco más completas que en la lista del clásico.

Los campos opcionales vacíos desaparecen del video. Si un texto es más largo que lo
recomendado, la letra se achica sola para que quepa, y el script avisa.

## Archivos

- `generar.py` — valida la ficha y produce todo lo de `salida/<slug>/` (carpeta ignorada por git).
- `plantilla/base.css` — paletas, fondo, animaciones, botón y aviso comunes a todos los estilos.
  Las medidas van en `u` (`12u`): en 9:16 equivale a 1 px y se escala en los otros formatos.
- `plantilla/base.js` — llena los textos de la ficha, aplica los tiempos y permite exportar cuadro por cuadro.
- `plantilla/estilos/<estilo>/` — diseño (`plantilla.html`) y línea de tiempo (`tiempos.json`) de cada estilo.
- `plantilla/fonts/fonts.css` — Montserrat y Playfair Display embebidas (el render no usa internet).
- `sonido.py` — una receta de música y efectos por estilo, sintetizados, sin samples ni licencias.
- `render.cjs` — captura los cuadros con Chromium (Playwright).
- `productos/` — una carpeta por producto. El té Serenity trae textos para los 3 estilos.

## Requisitos

`python3` con `numpy` y `scipy`, `node` con `playwright`, y `ffmpeg`.

## ¿Y HyperFrames?

Para piezas más largas o con otro formato (explicadores de 30–90 s, presentaciones,
videos que combinan clips grabados) siguen estando los proyectos HyperFrames de las ramas
`claude/heygen-hyperframes-skill-*` y `claude/loving-lamport-*`. Esta plantilla es la vía
rápida para el contenido diario de producto: no necesita instalar nada de HyperFrames ni
conexión a internet para renderizar.
