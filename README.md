# Proyecto-prueba
Este es para probar hyperframes

## Jarvis: el jefe de los agentes

Abre este repositorio en Claude Code y escribe `/jarvis` (o háblale a "Jarvis").
Jarvis conversa contigo y llama a sus dos agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.

Ejemplo: *"Jarvis, búscame los 3 productos con mejores reseñas"* → te los muestra (con
`vitrina.html` para ver las fotos) → *"¿Hacemos contenido de alguno?"* → *"Sí, del 2"* →
llama al agente de contenido y te entrega el video y el caption.
