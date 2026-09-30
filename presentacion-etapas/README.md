# Etapa 1 vs Etapa 2: ahorro de tiempo (HyperFrames)

Presentación estilo keynote con motion graphics, hecha con [HyperFrames](https://hyperframes.heygen.com).
**Los datos son simulados**, solo para probar el formato y las referencias visuales.

## Dos formas de usarla

| Modo | Comando | Qué obtienes |
| --- | --- | --- |
| **Keynote (recomendado)** | Abrir `keynote/presentacion.html` en el navegador | Un solo archivo, sin instalar nada. Clic o → avanza con animación, ← retrocede, **F** pantalla completa, **N** notas |
| Regenerar el keynote | `npm run keynote` | Vuelve a crear `keynote/presentacion.html` a partir de `index.html` (hazlo después de cada cambio) |
| Deck de HyperFrames | `npm run present` | Deck navegable con modo presentador (tecla **P**); los clics saltan a cuadros fijos |
| Video motion graphics | `npm run render` | MP4 de 61 s con todas las animaciones seguidas |
| Editar en Studio | `npm run dev` | Timeline visual de HyperFrames |

Requisitos: Node ≥ 22 y FFmpeg (solo para renderizar). GSAP y la fuente Inter vienen incluidos en `assets/`, así que funciona sin internet.

## Diapositivas (datos simulados)

1. **Portada**: ¿Cuánto tiempo nos ahorramos con cada etapa?
2. **Hoy**: 40 h/semana de trabajo manual (desglose en 4 tareas)
3. **Etapa 1**: −18 h/semana (45%), lista en 4 semanas
4. **Etapa 2**: −32 h/semana (80%), lista en 10 semanas
5. **Curva acumulada**: Etapa 2 alcanza a Etapa 1 en la semana 18
6. **Resultado a 12 meses**: 864 h vs 1,344 h → +480 h para Etapa 2
7. **Recomendación**: arrancar con Etapa 1 y escalar a Etapa 2

### Supuestos de la simulación

- Línea base actual: 40 h/semana.
- Etapa 1 ahorra 18 h/semana a partir de la semana 4.
- Etapa 2 ahorra 32 h/semana a partir de la semana 10.
- Ahorro acumulado = ahorro semanal × semanas desde que entra en operación (horizonte de 52 semanas).
- 1 mes-persona ≈ 160 h.

## Colores

Toda la paleta está en el bloque `PALETA DE MARCA` al inicio del `<style>` de `index.html`. La actual es provisional (azul marino, celeste y dorado); reemplaza esos hex por los oficiales, luego ejecuta `npm run keynote` y `npm run render`.

Para usar datos reales, cambia los números en `index.html` (textos, `countUp(...)`, anchos de las barras y los puntos del gráfico SVG de la diapositiva 5).
