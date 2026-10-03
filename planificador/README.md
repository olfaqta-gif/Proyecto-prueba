# Planificador de contenido Farmasi

Aquí vive la **estrategia y el calendario** de publicaciones. Lo escribe el agente
`estratega-contenido` (`.claude/agents/`) y lo coordina Isa:

```
Isabella: "Isa, hazme el plan de contenido de las próximas 2 semanas para vender más"
  │
  ├─► scraper-farmasi       lee el catálogo completo de la tienda (sin precios)
  ├─► estratega-contenido   analiza todos los productos con analizar.py
  │                         y arma plan.json + calendario plan.html
  │     Isa te lo muestra y pregunta: "¿Empezamos con el primer anuncio?"
  ├─► creador-contenido     hace cada anuncio del plan y lo marca como "hecho"
  └─► tú publicas y le cuentas a Isa cómo te fue → se guarda en el plan
                            y el próximo análisis aprende de eso
```

El archivo del plan es el punto de unión: el estratega lo escribe, Isa lo lee para
saber qué sigue, el agente de contenido lo marca cuando termina un video y tus
resultados quedan guardados ahí para el siguiente plan.

## El análisis (`analizar.py`)

No elige solo por reseñas. Une los tonos de un mismo producto (cada tono es una página
pero comparten reseñas), separa lo que no se vende (muestras, guías, bolsas) y califica
cada producto de 0 a 100 con estas variables:

| Variable | Qué mide |
|---|---|
| confianza | calificación ajustada por cantidad de reseñas (4.9 ★ con 10 reseñas vale menos que con 1000) |
| popularidad | cuántas reseñas tiene: lo que más se vende en la tienda |
| temporada | si encaja con las fechas del periodo (Halloween, Black Friday, Navidad, San Valentín, Día de las Madres, verano…) |
| novedad | producto nuevo o edición limitada |
| potencial de contenido | cuántos ángulos ofrece: tonos para mostrar, ingredientes para explicar, modo de uso, reto de 7 días, regalo… |
| empuje de la tienda | la tienda lo tiene en promoción (no se escriben precios; es una señal para que pongas tu oferta) |
| disponibilidad | que haya stock y tonos disponibles |
| tus ventas | lo que más te compran tus clientas (`datos/ventas.csv`, opcional) |
| rendimiento | cómo te fue con esa categoría en tus publicaciones (resultados guardados) |

Cada **objetivo** pesa distinto esas variables: `ventas`, `alcance` (gente nueva),
`confianza`, `lanzamiento` (novedades) o `equilibrado`. Después aplica **variedad**: baja
lo que ya tiene anuncio o ya está en otro plan y no deja más de 2 productos por categoría.

```bash
python3 planificador/analizar.py mercado        # productos, reseñas, novedades y promos por categoría
python3 planificador/analizar.py aprendizaje    # qué te funcionó: por tipo, pilar, estilo, día, hora, categoría
python3 planificador/analizar.py oportunidades --objetivo ventas --inicio 2026-10-05 --dias 14
python3 planificador/analizar.py oportunidades --objetivo alcance --categoria labios --n 6
```

`oportunidades` muestra cada producto con su puntaje, el porqué y las ideas de contenido,
y lo guarda en `analisis/<inicio>-<objetivo>.json`.

**Tus ventas (opcional):** si creas `planificador/datos/ventas.csv` con las columnas
`fecha,codigo,cantidad` (una fila por venta), el análisis sube lo que tus clientas ya compran.

## Comandos

Solo usa Python 3 (librería estándar). Desde la raíz del repositorio:

```bash
# Qué anuncios ya existen, el último estilo usado y los planes guardados
python3 planificador/planificar.py estado

# Revisar un plan y crear su calendario (plan.html, se abre en el navegador)
python3 planificador/planificar.py revisar planificador/planes/2026-10-05-vender-mas.json

# El próximo anuncio pendiente, con lo que necesita el agente de contenido
python3 planificador/planificar.py siguiente planificador/planes/2026-10-05-vender-mas.json
python3 planificador/planificar.py siguiente planificador/planes/2026-10-05-vender-mas.json --tipo educativo   # el próximo video educativo

# Marcar una publicación: pendiente, hecho, publicado o saltado
python3 planificador/planificar.py marcar planificador/planes/2026-10-05-vender-mas.json 3 hecho

# Guardar cómo le fue (así el próximo plan aprende)
python3 planificador/planificar.py resultado planificador/planes/2026-10-05-vender-mas.json 1 --vistas 1500 --mensajes 9 --ventas 3
```

## Tendencias de la semana

El estratega busca cada semana de qué se está hablando en belleza (en noticias, blogs y revistas;
nunca entra a Instagram ni TikTok) y elige hasta 5 que Isabella pueda hacer con sus productos.
Cada plan lleva al menos una por semana.

```bash
python3 planificador/tendencias.py pendiente     # ¿ya están las de esta semana? y qué buscar
python3 planificador/tendencias.py guardar lote.json
python3 planificador/tendencias.py actuales      # las de esta semana
python3 planificador/tendencias.py usada 2 --plan planificador/planes/x.json --id p3
python3 planificador/tendencias.py historial
```

Quedan en `planificador/tendencias/<año>-S<semana>.json` con una página `.html` para Isabella.

## El plan (`planes/<fecha>-<nombre>.json`)

| Campo | Qué es |
|---|---|
| `nombre`, `inicio` | título del plan y primer día (AAAA-MM-DD) |
| `basado_en` | qué análisis se usó (archivo, objetivo, fecha del catálogo, resultados) |
| `objetivo`, `publico`, `frecuencia` | la estrategia en pocas palabras |
| `pilares` | temas de contenido: `id`, `nombre`, `porque`, `porcentaje` (meta) |
| `notas` | recomendaciones o preguntas para Isabella |
| `publicaciones` | el calendario (abajo) |

Cada publicación:

| Campo | Qué es |
|---|---|
| `id`, `fecha`, `hora`, `red` | cuándo y dónde |
| `pilar` | uno de los `id` de `pilares` |
| `tipo` | `anuncio` (video que hace el agente de contenido), `educativo` (video con motion graphics que hace el agente educativo: lleva `forma` = `tips`, `mito`, `pasos` o `dato`, y `"carrusel": true` si también se quiere en imágenes), `reel`, `historia`, `carrusel`, `post` o `en-vivo` (los haces tú) |
| `idea` | qué se publica, en una frase |
| `producto` | `codigo`, `slug` y `nombre` (los da el scraper) |
| `estilo`, `formatos` | solo anuncios: `clasico` / `favorito` / `razones` y `9x16`, `4x5`, `1x1`, `16x9` |
| `gancho`, `guion`, `caption`, `llamado` | el texto: gancho para el anuncio, guion para lo que grabas tú |
| `porque` | por qué este producto, en palabras simples (sale del análisis) |
| `estado` | `pendiente`, `hecho`, `publicado` o `saltado` |
| `resultados` | `vistas`, `mensajes`, `ventas`, `guardados`, `compartidos` (los guarda `resultado`) |

`revisar` detiene el plan si algún texto menciona precios, porcentajes de resultados,
promesas médicas o de ingresos, y avisa si dos anuncios seguidos usan el mismo estilo,
si un producto se repite en la misma semana o si la mezcla de pilares se aleja de la meta.
