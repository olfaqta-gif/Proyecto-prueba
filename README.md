# Proyecto-prueba
Este es para probar hyperframes

## Isa: la jefa de los agentes

**Panel de Isa:** para verla a ella y a sus agentes y conversar en una página web,
abre `panel/abrir-panel.bat` (Windows) o `panel/abrir-panel.command` (Mac). Ver `panel/README.md`.

Abre este repositorio en Claude Code y escribe `/isa` (o háblale a "Isa").
Isa conversa contigo y llama a sus cinco agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `estratega-contenido` (`.claude/agents/`): arma la estrategia y el calendario de publicaciones con `planificador/`.
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.
- `creador-educativo`, el Profe (`.claude/agents/`): hace videos que enseñan, con motion graphics
  (tips, mito vs realidad, rutina paso a paso, "¿sabías que?") y carruseles, con `agente-educativo/`.
- `guionista` (`.claude/agents/`): escribe los videos que Isabella graba ella misma (arréglate
  conmigo, lo probé, tutorial, historias, en vivo…) y le arma una hoja de grabación toma por
  toma, un teleprompter y el caption, con `guionista/`.

Todos leen `marca/voz-isabella.md`, la ficha con la personalidad de Isabella, para que el
contenido suene a ella.

Ejemplo para grabar: *"Isa, quiero grabar un arréglate conmigo con el sérum de vitamina C"* →
el guionista escribe el guion con su voz y te entrega la hoja y el teleprompter para leer mientras grabas.

Ejemplo educativo: *"Isa, hazme un video de tips para que el labial dure más"* → el Profe
escribe el guion, genera el video con su propia música y te entrega los formatos y el caption.

Ejemplo: *"Isa, búscame los 3 productos con mejores reseñas"* → te los muestra (con
`vitrina.html` para ver las fotos) → *"¿Hacemos contenido de alguno?"* → *"Sí, del 2"* →
llama al agente de contenido y te entrega el video y el caption.

Para planificar: *"Isa, ¿qué publico las próximas 2 semanas?"* → el scraper trae los
productos mejor calificados → el estratega arma el plan y un calendario para ver en el
navegador → cuando lo apruebas, el agente de contenido hace cada anuncio del plan, uno
por uno, preguntándote antes de cada uno.
