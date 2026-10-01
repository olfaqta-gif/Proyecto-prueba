# Planificador de contenido Farmasi

Aquí vive la **estrategia y el calendario** de publicaciones. Lo escribe el agente
`estratega-contenido` (`.claude/agents/`) y lo coordina Jarvis:

```
Julio: "Jarvis, hazme el plan de contenido de las próximas 2 semanas"
  │
  ├─► scraper-farmasi       trae los productos con mejores reseñas (sin precios)
  ├─► estratega-contenido   arma plan.json + calendario plan.html
  │     Jarvis te lo muestra y pregunta: "¿Empezamos con el primer anuncio?"
  └─► creador-contenido     hace cada anuncio del plan y lo marca como "hecho"
```

El archivo del plan es el punto de unión: el estratega lo escribe, Jarvis lo lee para
saber qué sigue, y el agente de contenido lo marca cuando termina un video.

## Comandos

Solo usa Python 3 (librería estándar). Desde la raíz del repositorio:

```bash
# Qué anuncios ya existen, el último estilo usado y los planes guardados
python3 planificador/planificar.py estado

# Revisar un plan y crear su calendario (plan.html, se abre en el navegador)
python3 planificador/planificar.py revisar planificador/planes/ejemplo-plan.json

# El próximo anuncio pendiente, con lo que necesita el agente de contenido
python3 planificador/planificar.py siguiente planificador/planes/ejemplo-plan.json

# Marcar una publicación: pendiente, hecho, publicado o saltado
python3 planificador/planificar.py marcar planificador/planes/ejemplo-plan.json 3 hecho
```

## El plan (`planes/<fecha>-<nombre>.json`)

| Campo | Qué es |
|---|---|
| `nombre`, `inicio` | título del plan y primer día (AAAA-MM-DD) |
| `objetivo`, `publico`, `frecuencia` | la estrategia en pocas palabras |
| `pilares` | temas de contenido: `id`, `nombre`, `porque`, `porcentaje` (meta) |
| `notas` | recomendaciones o preguntas para Julio |
| `publicaciones` | el calendario (abajo) |

Cada publicación:

| Campo | Qué es |
|---|---|
| `id`, `fecha`, `hora`, `red` | cuándo y dónde |
| `pilar` | uno de los `id` de `pilares` |
| `tipo` | `anuncio` (video que hace el agente de contenido), `reel`, `historia`, `carrusel`, `post` o `en-vivo` (los haces tú) |
| `idea` | qué se publica, en una frase |
| `producto` | `codigo`, `slug` y `nombre` (los da el scraper) |
| `estilo`, `formatos` | solo anuncios: `clasico` / `favorito` / `razones` y `9x16`, `4x5`, `1x1`, `16x9` |
| `gancho`, `guion`, `caption`, `llamado` | el texto: gancho para el anuncio, guion para lo que grabas tú |
| `estado` | `pendiente`, `hecho`, `publicado` o `saltado` |

`revisar` detiene el plan si algún texto menciona precios, porcentajes de resultados,
promesas médicas o de ingresos, y avisa si dos anuncios seguidos usan el mismo estilo,
si un producto se repite en la misma semana o si la mezcla de pilares se aleja de la meta.
