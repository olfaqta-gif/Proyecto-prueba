# Proyecto-prueba
Este es para probar hyperframes

## Isa: la jefa de los agentes

**Panel de Isa:** para verla a ella y a sus agentes y conversar en una página web,
abre `panel/abrir-panel.bat` (Windows) o `panel/abrir-panel.command` (Mac). Ver `panel/README.md`.

Abre este repositorio en Claude Code y escribe `/isa` (o háblale a "Isa").
Isa conversa contigo y llama a sus cuatro agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `estratega-contenido` (`.claude/agents/`): arma la estrategia y el calendario de publicaciones con `planificador/`.
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.
- `creador-educativo`, el Profe (`.claude/agents/`): hace videos que enseñan, con motion graphics
  (tips, mito vs realidad, rutina paso a paso, "¿sabías que?") y carruseles, con `agente-educativo/`.

Ejemplo educativo: *"Isa, hazme un video de tips para que el labial dure más"* → el Profe
escribe el guion, genera el video con su propia música y te entrega los formatos y el caption.

Ejemplo: *"Isa, búscame los 3 productos con mejores reseñas"* → te los muestra (con
`vitrina.html` para ver las fotos) → *"¿Hacemos contenido de alguno?"* → *"Sí, del 2"* →
llama al agente de contenido y te entrega el video y el caption.

Para planificar: *"Isa, ¿qué publico las próximas 2 semanas?"* → el scraper trae los
productos mejor calificados → el estratega arma el plan y un calendario para ver en el
navegador → cuando lo apruebas, el agente de contenido hace cada anuncio del plan, uno
por uno, preguntándote antes de cada uno.
