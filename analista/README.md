# La Analista de redes

Revisa cómo le va a Isabella en Instagram y TikTok y le dice al equipo qué repetir y qué cambiar.

**Cómo se usa:** Isabella saca capturas de pantalla de las estadísticas de sus publicaciones
(en Instagram: "Ver estadísticas" debajo del post; en TikTok: los tres puntitos ›
"Estadísticas") y de su perfil, las deja en la carpeta `analista/capturas/` y le dice a Isa
*"revisa mis redes"*. La Analista lee las capturas, guarda los números y arma el informe.

`redes.py` (solo Python estándar):

- `pendientes`: capturas sin leer y publicaciones del plan sin números.
- `agregar`: guarda los números de una publicación. Si está en el plan del estratega, también
  los guarda ahí (`planificar.py resultado`), así la reunión del equipo y el estratega los usan.
- `cuenta`: seguidores del perfil en una fecha (para ver cómo crecen).
- `informe [--dias 30]`: informe visual `informes/<fecha>.html` con lo que mejor y peor
  funcionó, por tipo, red, día, horario y duración, los seguidores y los consejos para cada agente.
- `consejos <agente>`: lo que cada agente lee antes de trabajar.
- `lista`: todo lo guardado.

**El puntaje:** cada publicación se compara con lo normal de Isabella (su mediana): vistas,
cuánta gente reacciona, guardados y compartidos, mensajes y ventas, y seguidores nuevos.
50 es lo normal, 100 es el doble o más.

Lo que queda en cada computadora (no se sube al repositorio): `datos/`, `capturas/` e `informes/`.
