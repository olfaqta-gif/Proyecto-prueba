# Reunión de equipo de Isa

Isa reúne a sus agentes, revisa el trabajo de cada uno y acuerda cómo mejorar. Se lo
pides a Isa ("reúne al equipo") o con el botón **Reunir al equipo** del panel.

- `revisar.py reunir` revisa lo que hizo cada agente (anuncios, educativos, guiones, el plan
  y las fichas de productos), le pone nota de 0 a 10 por criterio y la compara con la
  reunión anterior. Si Isabella contó cómo le fue a sus publicaciones, suma "Resultados reales".
- Isa agrega su comentario a cada agente (`nota`), su resumen (`resumen`) y los acuerdos
  (`acuerdo`, `cumplido`, `no-cumplido`).
- Cada agente lee sus acuerdos antes de trabajar (`revisar.py acuerdos <agente>`).

Lo que queda:

- `actas/<fecha>.json` y `actas/<fecha>.html`: el acta y el informe visual (ábrelo en el navegador).
- `acuerdos.json`: los acuerdos de cada agente y si se cumplieron.

Solo usa Python estándar.
