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

## Video direction

- **Palette (frame.md, one register — dark):** ground `ink-black` #213343 (full-bleed clip layer, plus a faint 1px `border-dark` hairline grid at ~25% for depth); nodes `ink-black-alt` #1B2A38 with 1px `border-dark` edges; text `cream`; secondary labels `cream-muted`; the ONLY accent is `fire-orange` #FF7A59 (the CRM core, the active hub's name + border, the live wire, the customer dot, one accent clause per statement). Ink-on-orange (#213343) inside the CRM core.
- **Type by role:** display/h1/h2 Barlow 800–900 lowercase negative-tracked; hub names h3 Barlow 800 lowercase; tags + kickers IBM Plex Mono uppercase 0.14em. Fonts are local files in `assets/fonts/` (`@font-face`, no network).
- **The shared stage (load-bearing):** every frame draws the SAME diagram world at the SAME coordinates as the confirmed sketch (`storyboard.html`, `.hyperframes/build_storyboard.py` NODES): crm (50%,42%) · marketing (17%,42%) · sales (83%,42%) · service (50%,74%) · content (24%,11%) · operations (50%,9%) · commerce (76%,11%). Nodes already introduced in earlier frames are present at t=0 (settled); only the NEW piece of each frame animates in. Camera = one `.world` wrapper transform (`viewport-change`); the crm node itself never moves inside the world.
- **Motion grammar:** `power3.out` long-tail settles, no overshoot/bounce. Wires connect via **SVG self-draw** (`svg-path-draw`) from the crm outward; nodes arrive with a short fade + 12px rise (`spring-pop-entrance`, smooth register, no overshoot); tags reveal via **per-word staggered reveal** (`dynamic-content-sequencing`) on each spoken cue; the customer dot travels along wires on a `power2.inOut` path. Camera moves happen at frame start (first 0.2–1.2s) and then LOCK — no back-half pan or push. Holds are still; at most subtle jitter (`sine-wave-loop`, low amplitude) on the customer dot.
- **Reveal model:** at t=0 only what the VO says at t=0; each tag/node/verb enters on its word cue. Timings below are estimates at ~2.3 words/s until real TTS timings replace them (sync-durations).
- **Rhythm / held frames:** 02 ends on a 1.5s held read of the crm core (the thesis); 05 holds the three lit wires ~1.5s ("aha"); 08's last ~2s are fully still. Frames 03/04/06/07 keep moving to their cue and hold only briefly.
- **SFX:** `click-soft` on each node that snaps onto a wire; `whoosh` on the 02 absorption and 08 pull-back; `chime` on 05's shared-history light-up; `sparkle` under 07's pulse. All ~0.35 volume, under the voice.
- **Negative list:** no HubSpot logo or UI mock; no third-party logos; no invented numbers; no gradients, glows-as-decoration, bokeh or purple AI clichés; no shadows or rounded cards (0 radius except the crm circle + customer dot); **no slideshow** (dumping a frame's pieces at t=0) and **no screensaver** (elements floating independently / drifting camera in the back half); no CSS transitions/keyframes, no `repeat:-1`, no Math.random.
- **Captions:** bottom 17% keep-out respected by every frame (content caps at y≈83%).

## Locked

Sketch sheet v1 confirmed by the user ("Adelante"): layout, positions, copy and camera framings of frames 01–08 are locked; the build dresses these layouts and never redraws them.

## Frame 1 — Todo disperso

- scene: Fragmentos flotando por el lienzo marino — "correo", "hoja de cálculo", "chat", "notas", "facturas" — desconectados, cada uno con un puntito de cliente distinto.
- voiceover: "Tus clientes están en todas partes: un correo aquí, una hoja de cálculo allá, un chat que nadie ve."
- duration: 6s
- transition_in: cut
- status: built
- src: compositions/frames/01-todo-disperso.html
- type: hook
- persuasion: Pain validation + Concretization (datos dispersos → fragmentos visibles)
- beat: recognition + tension
- blueprint: overwhelm-surround (Adapt)
- focal: seven data fragments ("correo", "hoja de cálculo", "chat", "notas", "facturas", "whatsapp", "post-it") each with its own orange customer dot
- roles: fragments = foreground subjects (scattered upper 2/3) · statement "tus clientes están en todas partes" = supporting display, lower-left above the band · hairline grid = background (dim ~25%)
- sfx: pop

narrativeRole: Abre la brecha: el espectador reconoce el caos de tener la información del cliente repartida.
keyMessage: Sin un centro, cada equipo ve solo un trozo del cliente.

Adapt: keep the accumulation-until-crowded signature (surfaces pile up and close in); drop the avatar morph — the "you" is the orange dots, one per fragment, i.e. the same customer duplicated.
Scene 1 (0.0–0.4s): empty navy ground + faint hairline grid; kicker "01 / el problema" fades in top-left. Nothing else yet.
Scene 2 (0.4–1.6s): on "tus clientes están en todas partes" the statement assembles lower-left via per-word staggered reveal (`dynamic-content-sequencing`), "en todas partes" inked orange; asymmetric 60/40 — type bottom-left, empty field above.
Scene 3 (1.6–4.8s): fragments enter on their cues — "correo" (≈1.9s), "hoja de cálculo" (≈2.7s), "chat" (≈3.6s), then notas / facturas / whatsapp / post-it in a quick stagger (≈4.2–4.8s) — each a fade + small rise at its slight tilt, its orange dot popping a beat later (`spring-pop-entrance`, smooth). Accumulation reads as clutter spreading across the upper 2/3.
Scene 4 (4.8–6.0s): the fragments drift ~1–2% inward toward the center (the "closing in" signature, one finite power2 tween) and hold; no breathing.

## Frame 2 — El centro: el CRM

- scene: Los fragmentos del frame 1 son absorbidos hacia el centro y se funden en un único nodo "crm"; dentro aparecen cuatro etiquetas: contactos · empresas · negocios · tickets.
- voiceover: "HubSpot empieza por el centro: un CRM. Contactos, empresas, negocios y tickets, en una sola ficha por cliente."
- duration: 8s
- transition_in: zoom-through
- status: built
- src: compositions/frames/02-el-centro-crm.html
- type: product_intro
- persuasion: Frame-then-fill (el centro primero, luego su contenido) + Progressive disclosure
- beat: clarity + orientation
- blueprint: constellation-hub (Adapt)
- focal: the crm core — orange circle ~17% of frame width at (50%,42%), "crm" in ink display
- roles: crm core = foreground subject · four tags (contactos · empresas · negocios · tickets) = supporting, inside the core · caption line "una sola ficha por cliente" = supporting, lower-left · grid = background
- sfx: whoosh, click-soft

narrativeRole: Nombra la idea protagonista — el CRM como fuente única de verdad — y ancla el nodo que no se moverá en todo el video.
keyMessage: Todo en HubSpot gira alrededor de una sola base de datos de clientes.

Adapt: keep the hub-resolves-at-center signature, inverted — the satellites (frame 01's fragments, redrawn at their frame-01 positions at t=0) COLLAPSE into the hub rather than orbiting out.
Scene 1 (0.0–1.4s): the seven fragments from 01 sit where 01 left them, then on "HubSpot empieza por el centro" all slide to (50%,42%) and shrink/fade into it (`center-outward-expansion` reversed, lockstep, power3.in→out), while the crm circle scales up from 0.2 to 1 at center (`spring-pop-entrance`, smooth). Kicker "02 / el centro" top-left.
Scene 2 (1.4–2.6s): on "un CRM" the word "crm" lands inside the core (fade + 8px rise).
Scene 3 (2.6–5.4s): the four tags reveal one per spoken word — contactos (≈3.0s) · empresas (≈3.6s) · negocios (≈4.2s) · tickets (≈4.8s) — mono, ink 75%, inside the circle.
Scene 4 (5.4–6.6s): on "en una sola ficha por cliente" the caption line assembles lower-left, "por cliente" orange.
Scene 5 (6.6–8.0s): held read — the thesis sits still (held beat).

## Frame 3 — Marketing Hub

- scene: Mismo diagrama; la cámara se acerca a la izquierda. Un nodo "marketing" se engancha al CRM con una línea; alrededor aparecen tres etiquetas: emails · anuncios · formularios. El punto naranja "visitante" entra y se convierte en "lead" al tocar el CRM.
- voiceover: "Se conecta Marketing Hub: emails, anuncios y formularios atraen visitantes… y los convierten en leads."
- duration: 7s
- transition_in: crossfade
- status: built
- src: compositions/frames/03-marketing-hub.html
- type: feature_showcase
- persuasion: Progressive disclosure + Causal chain (visitante → lead)
- beat: comprehension
- blueprint: spatial-pan-stations (Adapt)
- focal: the "marketing hub" node + its orange wire to crm
- roles: marketing node = foreground subject · crm core = anchor (already present) · customer dot "visitante → lead" = supporting action · three tags = supporting · grid = background
- sfx: click-soft

narrativeRole: Primera pieza del mecanismo: cómo entran los clientes al sistema.
keyMessage: Marketing Hub atrae gente y la registra en el CRM como lead.

Adapt: keep the single virtual camera traversing to a station and revealing its callout; one leg only (crm → marketing station), then lock.
Scene 1 (0.0–1.0s): world starts at the 02 framing (crm centered, scale 1); camera eases to scale 1.3 with origin at (30%,45%) (`viewport-change`), bringing the left side into frame. Kicker "03 / atraer".
Scene 2 (1.0–2.4s): on "se conecta Marketing Hub" the wire self-draws from crm toward the left (`svg-path-draw`), and the marketing node lands at its end (fade + rise), name in orange, border orange.
Scene 3 (2.4–4.2s): tags on cue — emails (≈2.6s) · anuncios (≈3.1s) · formularios (≈3.7s).
Scene 4 (4.2–7.0s): on "atraen visitantes" an orange dot appears at the marketing node labelled "visitante"; on "y los convierten en leads" it travels the wire toward crm (power2.inOut) and its label swaps to "lead" (hard-cut token swap, `discrete-text-sequence`) as it reaches the midpoint; hold.

## Frame 4 — Sales Hub

- scene: Mismo diagrama; la cámara pasa a la derecha. Un nodo "ventas" se engancha al CRM; etiquetas: pipeline · reuniones · cotizaciones. El punto naranja viaja de marketing a ventas y avanza por tres columnas de pipeline hasta "cliente".
- voiceover: "Sales Hub recoge ese lead: pipeline, reuniones, cotizaciones… hasta cerrar la venta."
- duration: 7s
- transition_in: crossfade
- status: built
- src: compositions/frames/04-sales-hub.html
- type: feature_showcase
- persuasion: Signposting (primero… luego…) + Demonstration (el punto recorre el pipeline)
- beat: momentum
- blueprint: spatial-pan-stations (Adapt)
- focal: the "sales hub" node + the three-stage pipeline strip beneath it
- roles: sales node = foreground subject · crm = anchor · marketing node = present, dimmed ~45% (off-camera left edge) · customer dot = supporting action · pipeline strip (nuevo · propuesta · ganado) = supporting · grid = background
- sfx: click-soft, ping

narrativeRole: Segunda pieza: el mismo cliente pasa de marketing a ventas sin reescribir datos.
keyMessage: Ventas trabaja sobre la misma ficha que creó marketing.

Adapt: same camera-to-station signature as 03, mirrored to the right — this is the second station of the same pan.
Scene 1 (0.0–1.0s): world starts at 03's end state (marketing wired, dot at the wire midpoint "lead"); camera eases from origin (30%,45%) to (70%,45%) at scale 1.3 — the pan IS the continuity with 03. Kicker "04 / vender".
Scene 2 (1.0–2.2s): on "Sales Hub recoge ese lead" the right wire self-draws crm → sales and the node lands; simultaneously the dot slides from its mid-left position through the crm to the right wire.
Scene 3 (2.2–4.2s): tags on cue — pipeline (≈2.5s) · reuniones (≈3.1s) · cotizaciones (≈3.7s).
Scene 4 (4.2–7.0s): the pipeline strip (nuevo · propuesta · ganado) appears under the node; on "hasta cerrar la venta" the dot steps through the three columns, the "ganado" cell turns orange and the dot label swaps "lead" → "cliente" (`discrete-text-sequence`); `ping` on "venta"; hold.

## Frame 5 — Service Hub

- scene: Mismo diagrama; la cámara baja. Un nodo "servicio" se engancha al CRM; etiquetas: tickets · chat · base de conocimiento. El punto naranja ("cliente") abre un ticket y las líneas hacia marketing y ventas parpadean: todos ven el caso.
- voiceover: "Y Service Hub cuida al cliente después: tickets, chat, ayuda. Y todo el equipo ve el mismo historial."
- duration: 8s
- transition_in: crossfade
- status: built
- src: compositions/frames/05-service-hub.html
- type: benefit_highlight
- persuasion: Callback (las líneas del frame 3 y 4 se reactivan) + Demonstration
- beat: "aha"
- blueprint: camera-journey (Adapt)
- focal: the "service hub" node and, at the payoff, all three hub wires lighting at once
- roles: service node = foreground subject · crm + marketing + sales = present (full opacity) · customer dot = supporting · three tags = supporting · "ticket abierto" label = supporting · grid = background
- sfx: click-soft, chime

narrativeRole: Cierra el ciclo del cliente y entrega el "por qué importa": un historial compartido por todos.
keyMessage: Marketing, ventas y servicio ven lo mismo porque comparten el CRM.

Adapt: keep the action-roundtrip signature (a beat fires in one place, the consequence renders elsewhere) — the ticket opens at service, the consequence is the marketing + sales wires lighting up.
Scene 1 (0.0–1.0s): camera eases from 04's right framing to scale 1.12, origin (50%,70%), bringing the lower half into frame; marketing and sales nodes at full opacity. Kicker "05 / cuidar".
Scene 2 (1.0–2.4s): on "Service Hub cuida al cliente después" the lower wire self-draws crm → service and the node lands.
Scene 3 (2.4–4.4s): tags on cue — tickets (≈2.8s) · chat (≈3.4s) · ayuda (≈3.9s); on "tickets" the customer dot drops from crm down the wire and stops above the service node with label "ticket abierto".
Scene 4 (4.4–6.4s): on "y todo el equipo ve el mismo historial" the marketing and sales wires turn orange in one sweep outward from crm (stroke color + a travelling highlight via `svg-path-draw` dash offset), `chime`.
Scene 5 (6.4–8.0s): held read — three lit wires, still (held beat).

## Frame 6 — Y además

- scene: Mismo diagrama, plano un poco más abierto; tres nodos más pequeños se enganchan de golpe al anillo exterior: "content" (web y blog) · "operations" (datos) · "commerce" (cobros).
- voiceover: "Y si lo necesitas, más piezas: Content para tu web, Operations para tus datos, Commerce para cobrar."
- duration: 7s
- transition_in: crossfade
- status: built
- src: compositions/frames/06-y-ademas.html
- type: feature_showcase
- persuasion: Rule of three + Numbered enumeration
- beat: foresight
- blueprint: grid-card-assemble (Adapt)
- focal: the three mini nodes content · operations · commerce on the top ring
- roles: mini nodes = foreground subjects · full hub diagram = anchor (present, settled) · kicker "06 / más piezas" = supporting · grid = background
- sfx: click-soft

narrativeRole: Muestra que el sistema es modular: se añaden piezas sin cambiar el centro.
keyMessage: Cada Hub extra se engancha al mismo CRM.

Adapt: keep the staggered self-assemble of N items into a row; the "grid" is the top ring of the diagram, and each item assembles on its spoken name rather than in one cascade.
Scene 1 (0.0–1.0s): camera eases from 05's framing to scale 0.96 centered (the whole diagram in view); wires back to hint color except the crm core. Kicker "06 / más piezas" lower-left above the band.
Scene 2 (1.0–2.4s): on "más piezas" three short wire stubs self-draw upward from crm.
Scene 3 (2.4–6.0s): each mini node lands on its word — content (≈2.8s) · operations (≈4.0s) · commerce (≈5.2s) — wire completes to it in orange, node border orange, `click-soft` each, then its sub-label ("web · blog" / "datos" / "cobros").
Scene 4 (6.0–7.0s): hold, full system visible.

## Frame 7 — Breeze, la IA

- scene: Mismo diagrama completo; un pulso naranja nace en el CRM y recorre cada línea hasta todos los nodos; aparece la etiqueta "breeze · ia". Tres verbos junto al pulso: escribe · resume · responde.
- voiceover: "Por encima trabaja Breeze, la IA de HubSpot: usa esos datos para escribir, resumir y responder por ti."
- duration: 7s
- transition_in: crossfade
- status: built
- src: compositions/frames/07-breeze-ia.html
- type: benefit_highlight
- persuasion: Causal chain (datos compartidos → IA útil) + Rule of three
- beat: fascination
- blueprint: constellation-hub (Adapt)
- focal: an orange pulse travelling from the crm along every wire, plus the "breeze · ia" tag
- roles: pulse = foreground action · whole diagram = anchor · "breeze · ia" tag = supporting label · three verbs (escribe · resume · responde) = supporting display, right side above the band · grid = background
- sfx: sparkle

narrativeRole: Muestra la capa que aprovecha que todo esté conectado.
keyMessage: Como todos los datos están juntos, la IA puede trabajar con todos ellos.

Adapt: keep the hub-as-center signature — the hub radiates; this time the energy flows OUT from the center along the connectors (connectors brighten in narration order).
Scene 1 (0.0–1.6s): same framing as 06 end (scale 0.96). On "por encima trabaja Breeze" the "breeze · ia" tag drops in near the upper-right of the crm (fade + rise), kicker "07 / la ia".
Scene 2 (1.6–3.6s): on "la IA de HubSpot: usa esos datos" a bright orange dash travels from crm out along all six wires simultaneously (dash-offset travel, `svg-path-draw`), each destination node border flashing orange as the dash arrives, then settling back.
Scene 3 (3.6–6.0s): verbs on cue, stacked right — escribe (≈4.2s) · resume (≈4.8s) · responde (≈5.4s), opacities 1 / 0.6 / 0.3 (the fadelist component).
Scene 4 (6.0–7.0s): hold.

## Frame 8 — Así funciona HubSpot

- scene: Alejamiento lento: el diagrama entero queda pequeño y quieto en el centro; debajo, la frase final en tipografía grande: "un centro. muchas piezas. un mismo cliente."
- voiceover: "Un centro, muchas piezas, un mismo cliente. Así funciona HubSpot."
- duration: 8s
- transition_in: zoom-through
- status: built
- src: compositions/frames/08-asi-funciona.html
- type: branding
- persuasion: Distillation + Callback (el caos del frame 1 ahora ordenado)
- beat: "now I get it"
- blueprint: zoom-out-workspace-reveal (Adapt)
- focal: the final statement "un centro. muchas piezas. un mismo cliente."
- roles: final statement = foreground subject (lower-left, display) · complete diagram = supporting (small, upper area) · kicker "así funciona hubspot" = supporting (top-right) · grid = background
- sfx: whoosh

narrativeRole: Aterriza la tesis en una línea memorable sobre el sistema completo, quieto.
keyMessage: HubSpot = un CRM central + piezas conectadas que comparten al cliente.

Adapt: keep the ONE continuous decelerating zoom-out that reveals the whole as the signature; the "workspace" is the finished diagram, which shrinks and rises to make room for the thesis.
Scene 1 (0.0–2.0s): from 07's framing, one continuous decelerating pull-back (power3.out) to scale 0.55, translateY −30% — the diagram becomes a small complete emblem in the upper half. `whoosh` at start.
Scene 2 (2.0–4.6s): the statement lands in three beats on cue — "un centro." (≈2.2s) · "muchas piezas." (≈3.0s) · "un mismo cliente." (≈3.9s, orange) — each a per-word reveal, lower-left, display size.
Scene 3 (4.6–5.8s): on "así funciona HubSpot" the kicker "así funciona hubspot" fades in top-right.
Scene 4 (5.8–8.0s): fully still (held frame, the video's final read); final 0.4s fade to navy (the video's only real exit).

