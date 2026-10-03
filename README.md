# Proyecto-prueba
Este es para probar hyperframes

## Isa: la jefa de los agentes

**Panel de Isa:** para verla a ella y a sus agentes y conversar en una página web,
abre `panel/abrir-panel.bat` (Windows) o `panel/abrir-panel.command` (Mac). Ver `panel/README.md`.

Abre este repositorio en Claude Code y escribe `/isa` (o háblale a "Isa").
Isa conversa contigo y llama a sus ocho agentes:

- `scraper-farmasi` (`.claude/agents/`): busca productos en farmasius.com con `lector-farmasi/`.
- `estratega-contenido` (`.claude/agents/`): arma la estrategia y el calendario de publicaciones con `planificador/`, y cada semana busca
  las tendencias de belleza del momento para sumar al menos una al plan (`planificador/tendencias.py`).
- `creador-contenido` (`.claude/agents/`): hace el anuncio en video y el caption con `agente-contenido/`.
- `creador-educativo`, el Profe (`.claude/agents/`): hace videos que enseñan, con motion graphics
  (tips, mito vs realidad, rutina paso a paso, "¿sabías que?") y carruseles, con `agente-educativo/`.
- `guionista` (`.claude/agents/`): escribe los videos que Isabella graba ella misma (arréglate
  conmigo, lo probé, tutorial, historias, en vivo…) y le arma una hoja de grabación toma por
  toma, un teleprompter y el caption, con `guionista/`.
- `analista-redes`, la Analista (`.claude/agents/`): revisa cómo le va a Isabella en Instagram y
  TikTok a partir de las capturas de sus estadísticas, y entrega un informe visual con qué
  funcionó, qué no y consejos para cada agente, con `analista/`.
- `comunidad-ventas`, Comunidad (`.claude/agents/`): lee las capturas de tus comentarios y
  mensajes, te deja una respuesta lista para cada uno (copiar y abrir el chat con un toque),
  anota a las interesadas en tu libreta de clientas y te arma tus respuestas rápidas, con `comunidad/`.
- `asesora-rutinas`, la Asesora (`.claude/agents/`): cuando una clienta pregunta qué usar para su
  piel, le arma su rutina de mañana y noche con productos Farmasi en una tarjeta para mandarle por
  WhatsApp, con el mensaje escrito, y la anota en tu libreta, con `asesora/`.

**Libreta de clientas:** en el panel toca **«Clientas»**. Ves a quién escribirle hoy (a quién
se le acaba un producto, cumpleaños, pedidos por entregar), el tablero de cada clienta de
"preguntó" a "clienta fiel", sus pedidos y tus números. Ver `clientas/README.md`.

Todos leen `marca/voz-isabella.md`, la ficha con la personalidad de Isabella, para que el
contenido suene a ella.

Ejemplo para grabar: *"Isa, quiero grabar un arréglate conmigo con el sérum de vitamina C"* →
el guionista escribe el guion con su voz y te entrega la hoja y el teleprompter para leer mientras grabas.

Ejemplo de redes: deja las capturas de tus estadísticas en `analista/capturas/` y di
*"Isa, ¿cómo me va en redes?"* → la Analista las lee y te entrega el informe con lo que más
funcionó y qué hacer la próxima semana.

Ejemplo de mensajes: deja las capturas de tus comentarios y chats en `comunidad/capturas/` y di
*"Isa, ayúdame a responder"* → te entrega una hoja con cada respuesta lista para copiar y anota
a las interesadas en tu libreta.

Ejemplo de rutina: pégale a Isa el mensaje de una clienta (*"tengo la piel mixta y me salen
granitos, ¿qué me recomiendas?"*) y di *"Isa, ármale una rutina"* → la Asesora te entrega su
tarjeta con cada paso y foto, lo esencial para empezar y el mensaje listo para mandarle.

**Media kit:** *"Isa, hazme mi media kit"* → arma tu presentación para marcas (PDF de dos páginas)
con tus seguidores, vistas, interacción, quién te sigue y tus mejores publicaciones, sacados de las
capturas que leyó la Analista, más las colaboraciones que ofreces y tu contacto. Ver `mediakit/README.md`.

**Sumar socias:** *"Isa, ¿a quién le escribo del equipo?"* → te dice a quién le interesó vender
Farmasi y qué mensaje mandarle; tienes una presentación de 6 imágenes, mensajes para invitar sin
presionar y una guía de 30 días para cada socia nueva. Ver `equipo/README.md`.

**Kit de marca:** *"Isa, hazme una historia con lo que me dijo Carla"* → sale lista con tus colores y
letras. También las portadas de tus destacados, fondos para escribir encima y tu guía de marca. Ver `marca/README.md`.

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

## Para hacer videos (una sola vez)

Doble clic en `instalar-videos.command` (Mac) o `instalar-videos.bat` (Windows), o pídele a Isa
"instala lo que falta para hacer videos". Instala gratis lo que hace falta (la música, ffmpeg,
node y el navegador que toma los cuadros); node y ffmpeg quedan dentro de `herramientas/`.
