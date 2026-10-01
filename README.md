# Proyecto-prueba
Este es para probar hyperframes

## Jarvis: el jefe de los agentes

Abre este repositorio en Claude Code y escribe `/jarvis` (o háblale a "Jarvis").
Jarvis conversa contigo y llama a sus tres agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `estratega-contenido` (`.claude/agents/`): arma la estrategia y el calendario de publicaciones con `planificador/`.
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.

Ejemplo: *"Jarvis, búscame los 3 productos con mejores reseñas"* → te los muestra (con
`vitrina.html` para ver las fotos) → *"¿Hacemos contenido de alguno?"* → *"Sí, del 2"* →
llama al agente de contenido y te entrega el video y el caption.

Para planificar: *"Jarvis, ¿qué publico las próximas 2 semanas?"* → el scraper trae los
productos mejor calificados → el estratega arma el plan y un calendario para ver en el
navegador → cuando lo apruebas, el agente de contenido hace cada anuncio del plan, uno
por uno, preguntándote antes de cada uno.
