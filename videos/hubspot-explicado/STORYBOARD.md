---
format: 1920x1080
duration: 60s
message: "HubSpot es un CRM central al que se conectan herramientas de marketing, ventas y servicio, y todas comparten los mismos datos del cliente"
arc: concept-explainer with process
audience: personas que oyen hablar de HubSpot y quieren entender cómo encajan sus piezas
music: calm minimal corporate tech underscore
mode: collaborative
language: es
---

## Decisions

- **Message:** HubSpot es un CRM central al que se conectan herramientas de marketing, ventas y servicio, y todas comparten los mismos datos del cliente.
- **Audience and arc:** quien ha oído hablar de HubSpot pero no sabe cómo encajan sus piezas. Arco: dolor (datos dispersos) → el centro (CRM) → las piezas se conectan una a una → la IA las recorre → el sistema completo.
- **Format:** 1920×1080, ~60 s, voz en off en español, música suave de fondo + clics al encajar cada pieza. Captions: por decidir en el build (keep-out inferior ~17% reservado).
- **The spine:** UN diagrama que se arma pieza a pieza. El nodo "CRM" nace en el frame 02 en el centro y NO se mueve de ahí en todo el video; cada Hub llega como un nodo que se engancha a él con una línea. Un punto naranja ("el cliente") recorre las conexiones Marketing → Sales → Service.
- **Brand:** `frame.md` (preset Broadside remezclado): fondo azul marino #213343, texto #F5F8FA, naranja #FF7A59 como único acento; Barlow (display en minúsculas) + IBM Plex Mono (etiquetas). Sin logo oficial de HubSpot: el nombre va en texto.
- **Bans:** nada de interfaces falsas de HubSpot (no hay capturas reales); nada de logotipos de terceros; ninguna cifra inventada; no "slideshow" (cada frame es el mismo diagrama creciendo, no una tarjeta nueva); no "salvapantallas" (cada movimiento nombra una pieza que dice la voz).
- **Held frame:** el final del frame 08 — el sistema completo quieto mientras aterriza la frase.
- **Truthfulness:** el contenido resume la oferta pública de HubSpot (CRM, Hubs, Breeze) sin cifras ni precios; hubspot.com no se pudo consultar desde el entorno.

## Frame 1 — Todo disperso

- scene: Fragmentos flotando por el lienzo marino — "correo", "hoja de cálculo", "chat", "notas", "facturas" — desconectados, cada uno con un puntito de cliente distinto.
- voiceover: "Tus clientes están en todas partes: un correo aquí, una hoja de cálculo allá, un chat que nadie ve."
- duration: 6s
- transition_in: cut
- status: outline
- src: compositions/frames/01-todo-disperso.html
- type: hook
- persuasion: Pain validation + Concretization (datos dispersos → fragmentos visibles)
- beat: recognition + tension
- blueprint: overwhelm-surround

narrativeRole: Abre la brecha: el espectador reconoce el caos de tener la información del cliente repartida.
keyMessage: Sin un centro, cada equipo ve solo un trozo del cliente.

## Frame 2 — El centro: el CRM

- scene: Los fragmentos del frame 1 son absorbidos hacia el centro y se funden en un único nodo "crm"; dentro aparecen cuatro etiquetas: contactos · empresas · negocios · tickets.
- voiceover: "HubSpot empieza por el centro: un CRM. Contactos, empresas, negocios y tickets, en una sola ficha por cliente."
- duration: 8s
- transition_in: zoom-through
- status: outline
- src: compositions/frames/02-el-centro-crm.html
- type: product_intro
- persuasion: Frame-then-fill (el centro primero, luego su contenido) + Progressive disclosure
- beat: clarity + orientation
- blueprint: constellation-hub

narrativeRole: Nombra la idea protagonista — el CRM como fuente única de verdad — y ancla el nodo que no se moverá en todo el video.
keyMessage: Todo en HubSpot gira alrededor de una sola base de datos de clientes.

## Frame 3 — Marketing Hub

- scene: Mismo diagrama; la cámara se acerca a la izquierda. Un nodo "marketing" se engancha al CRM con una línea; alrededor aparecen tres etiquetas: emails · anuncios · formularios. El punto naranja "visitante" entra y se convierte en "lead" al tocar el CRM.
- voiceover: "Se conecta Marketing Hub: emails, anuncios y formularios atraen visitantes… y los convierten en leads."
- duration: 7s
- transition_in: crossfade
- status: outline
- src: compositions/frames/03-marketing-hub.html
- type: feature_showcase
- persuasion: Progressive disclosure + Causal chain (visitante → lead)
- beat: comprehension
- blueprint: spatial-pan-stations

narrativeRole: Primera pieza del mecanismo: cómo entran los clientes al sistema.
keyMessage: Marketing Hub atrae gente y la registra en el CRM como lead.

## Frame 4 — Sales Hub

- scene: Mismo diagrama; la cámara pasa a la derecha. Un nodo "ventas" se engancha al CRM; etiquetas: pipeline · reuniones · cotizaciones. El punto naranja viaja de marketing a ventas y avanza por tres columnas de pipeline hasta "cliente".
- voiceover: "Sales Hub recoge ese lead: pipeline, reuniones, cotizaciones… hasta cerrar la venta."
- duration: 7s
- transition_in: crossfade
- status: outline
- src: compositions/frames/04-sales-hub.html
- type: feature_showcase
- persuasion: Signposting (primero… luego…) + Demonstration (el punto recorre el pipeline)
- beat: momentum
- blueprint: spatial-pan-stations

narrativeRole: Segunda pieza: el mismo cliente pasa de marketing a ventas sin reescribir datos.
keyMessage: Ventas trabaja sobre la misma ficha que creó marketing.

## Frame 5 — Service Hub

- scene: Mismo diagrama; la cámara baja. Un nodo "servicio" se engancha al CRM; etiquetas: tickets · chat · base de conocimiento. El punto naranja ("cliente") abre un ticket y las líneas hacia marketing y ventas parpadean: todos ven el caso.
- voiceover: "Y Service Hub cuida al cliente después: tickets, chat, ayuda. Y todo el equipo ve el mismo historial."
- duration: 8s
- transition_in: crossfade
- status: outline
- src: compositions/frames/05-service-hub.html
- type: benefit_highlight
- persuasion: Callback (las líneas del frame 3 y 4 se reactivan) + Demonstration
- beat: "aha"
- blueprint: camera-journey

narrativeRole: Cierra el ciclo del cliente y entrega el "por qué importa": un historial compartido por todos.
keyMessage: Marketing, ventas y servicio ven lo mismo porque comparten el CRM.

## Frame 6 — Y además

- scene: Mismo diagrama, plano un poco más abierto; tres nodos más pequeños se enganchan de golpe al anillo exterior: "content" (web y blog) · "operations" (datos) · "commerce" (cobros).
- voiceover: "Y si lo necesitas, más piezas: Content para tu web, Operations para tus datos, Commerce para cobrar."
- duration: 7s
- transition_in: crossfade
- status: outline
- src: compositions/frames/06-y-ademas.html
- type: feature_showcase
- persuasion: Rule of three + Numbered enumeration
- beat: foresight
- blueprint: grid-card-assemble

narrativeRole: Muestra que el sistema es modular: se añaden piezas sin cambiar el centro.
keyMessage: Cada Hub extra se engancha al mismo CRM.

## Frame 7 — Breeze, la IA

- scene: Mismo diagrama completo; un pulso naranja nace en el CRM y recorre cada línea hasta todos los nodos; aparece la etiqueta "breeze · ia". Tres verbos junto al pulso: escribe · resume · responde.
- voiceover: "Por encima trabaja Breeze, la IA de HubSpot: usa esos datos para escribir, resumir y responder por ti."
- duration: 7s
- transition_in: crossfade
- status: outline
- src: compositions/frames/07-breeze-ia.html
- type: benefit_highlight
- persuasion: Causal chain (datos compartidos → IA útil) + Rule of three
- beat: fascination
- blueprint: constellation-hub

narrativeRole: Muestra la capa que aprovecha que todo esté conectado.
keyMessage: Como todos los datos están juntos, la IA puede trabajar con todos ellos.

## Frame 8 — Así funciona HubSpot

- scene: Alejamiento lento: el diagrama entero queda pequeño y quieto en el centro; debajo, la frase final en tipografía grande: "un centro. muchas piezas. un mismo cliente."
- voiceover: "Un centro, muchas piezas, un mismo cliente. Así funciona HubSpot."
- duration: 8s
- transition_in: zoom-through
- status: outline
- src: compositions/frames/08-asi-funciona.html
- type: branding
- persuasion: Distillation + Callback (el caos del frame 1 ahora ordenado)
- beat: "now I get it"
- blueprint: zoom-out-workspace-reveal

narrativeRole: Aterriza la tesis en una línea memorable sobre el sistema completo, quieto.
keyMessage: HubSpot = un CRM central + piezas conectadas que comparten al cliente.
