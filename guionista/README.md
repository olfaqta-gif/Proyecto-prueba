# Guionista de Isabella

Convierte un guion en lo que Isabella necesita para grabar con su celular.

```
python3 guionista/preparar.py guiones/<slug>
```

Crea `guionista/salida/<slug>/`:

- `hoja.html`: la hoja de grabación. Qué preparar (con casillas), toma por toma qué decir,
  qué mostrar, el plano y los segundos, otros ganchos para probar y el caption con botón
  de copiar. Se ve bien en el celular y se puede imprimir.
- `teleprompter.html`: el texto grande que se desliza solo. Tocar la pantalla pausa o
  sigue; tiene velocidad, tamaño de letra y modo espejo.
- `caption.txt`: el texto para publicar con sus hashtags.

Antes de crearlos revisa las reglas (sin precios, porcentajes de resultados, promesas
médicas ni de ingresos) y avisa si una toma suena apurada (más de 2,8 palabras por
segundo) o si el gancho dura más de 3 segundos.

## guion.json

Copia `guiones/grwm-vitamina-c/guion.json`.

| Campo | Qué es |
|---|---|
| `formato` | `grwm`, `prueba`, `tutorial`, `en-mi-bolsa`, `opinion`, `dia`, `respuesta`, `historias`, `en-vivo` |
| `titulo` | nombre del video; `*palabra*` sale resaltada |
| `red` | dónde se publica (ej. "Reels / TikTok", "Historias") |
| `duracion_objetivo` | segundos que debería durar (avisa si las tomas suman mucho más) |
| `audio` | `voz`, `voz-en-off`, `tendencia` (sonido de moda que elige al publicar), `musica-suave` |
| `por_que` | (opcional) una frase de por qué este video funciona |
| `producto` | (opcional) `{"carpeta": "agente-contenido/productos/<slug>"}`; sale su foto en la hoja |
| `preparar` | lista de lo que necesita a la mano antes de grabar |
| `tomas` | lista de tomas: `plano` (`cerca`, `medio`, `detalle`, `manos`, `pantalla`, `ambiente`), `segundos`, `dice`, y opcionales `muestra`, `texto_pantalla`, `consejo` |
| `ganchos_alternativos` | otras primeras frases para probar otros días |
| `caption` | `texto` y `hashtags` (sin #) |

En `dice`, lo personal que el guion no puede saber va como `[completa: qué contar]` y
sale en amarillo para que Isabella lo diga con sus palabras.

La personalidad de Isabella está en `marca/voz-isabella.md`.
