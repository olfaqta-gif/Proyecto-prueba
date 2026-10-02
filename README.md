# Proyecto-prueba
Este es para probar hyperframes

## Isa: la jefa de los agentes

**Panel de Isa:** para verla a ella y a sus agentes y conversar en una página web,
abre `panel/abrir-panel.bat` (Windows) o `panel/abrir-panel.command` (Mac). Ver `panel/README.md`.

Abre este repositorio en Claude Code y escribe `/isa` (o háblale a "Isa").
Isa conversa contigo y llama a sus seis agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `estratega-contenido` (`.claude/agents/`): arma la estrategia y el calendario de publicaciones con `planificador/`.
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.
- `creador-educativo`, el Profe (`.claude/agents/`): hace videos que enseñan, con motion graphics
  (tips, mito vs realidad, rutina paso a paso, "¿sabías que?") y carruseles, con `agente-educativo/`.
- `guionista` (`.claude/agents/`): escribe los videos que Isabella graba ella misma (arréglate
  conmigo, lo probé, tutorial, historias, en vivo…) y le arma una hoja de grabación toma por
  toma, un teleprompter y el caption, con `guionista/`.
- `analista-redes`, la Analista (`.claude/agents/`): revisa cómo le va a Isabella en Instagram y
  TikTok a partir de las capturas de sus estadísticas, y entrega un informe visual con qué
  funcionó, qué no y consejos para cada agente, con `analista/`.

Todos leen `marca/voz-isabella.md`, la ficha con la personalidad de Isabella, para que el
contenido suene a ella.

Ejemplo para grabar: *"Isa, quiero grabar un arréglate conmigo con el sérum de vitamina C"* →
el guionista escribe el guion con su voz y te entrega la hoja y el teleprompter para leer mientras grabas.

Ejemplo de redes: deja las capturas de tus estadísticas en `analista/capturas/` y di
*"Isa, ¿cómo me va en redes?"* → la Analista las lee y te entrega el informe con lo que más
funcionó y qué hacer la próxima semana.

Ejemplo educativo: *"Isa, hazme un video de tips para que el labial dure más"* → el Profe
escribe el guion, genera el video con su propia música y te entrega los formatos y el caption.

Ejemplo: *"Isa, búscame los 3 productos con mejores reseñas"* → te los muestra (con
`vitrina.html` para ver las fotos) → *"¿Hacemos contenido de alguno?"* → *"Sí, del 2"* →
llama al agente de contenido y te entrega el video y el caption.

Para planificar: *"Isa, ¿qué publico las próximas 2 semanas?"* → el scraper trae los
productos mejor calificados → el estratega arma el plan y un calendario para ver en el
navegador → cuando lo apruebas, el agente de contenido hace cada anuncio del plan, uno
por uno, preguntándote antes de cada uno.

Reunión de equipo: *"Isa, reúne al equipo"* (o el botón **Reunir al equipo** del panel) →
todos los robots se acercan a la mesa de Isa → Isa revisa el trabajo de cada agente con
`reunion/revisar.py`, le pone nota por criterio, revisa los acuerdos de la vez pasada y deja
nuevos → te entrega un informe visual (`reunion/actas/<fecha>.html`) con la nota del equipo,
una tarjeta por agente, lo que produjo cada uno, cómo va mejorando y los acuerdos. Los
agentes leen sus acuerdos antes de cada trabajo, así cada reunión el equipo sale mejor.
