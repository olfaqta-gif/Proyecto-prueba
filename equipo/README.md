# Kit para sumar socias

En Farmasi también se crece armando equipo. Este kit hace que **nadie que pregunte "¿cómo vendo
Farmasi?" se pierda**, que Isabella sepa qué decirle sin presionar, y que cada socia nueva tenga
un primer mes acompañado. **Nunca se promete dinero**: todo lleva el aviso de que lo que se gana
depende del trabajo de cada una.

**En el día a día:**
1. Alguien comenta o escribe "quiero vender Farmasi". El agente de comunidad le responde y la
   anota sola en la lista del equipo (o Isa la agrega con `agregar`).
2. `hoy` le dice a Isabella a quién escribirle y con qué mensaje: a la nueva interesada, mandarle
   la **presentación** (6 imágenes 4:5 para WhatsApp o carrusel); a quien ya la vio, preguntarle si
   le quedó alguna duda (máximo 2 veces, después queda en pausa); y a cada socia nueva, los mensajes
   de acompañamiento de los días 0, 3, 7, 14 y 30.
3. Cuando una persona se une (`paso "<nombre>" se-unio`), Isabella le manda su **guía de 30 días**:
   una página para el celular con 18 pasos para marcar (día 1, días 2 y 3, semanas 1 a 4).
4. La hoja de **mensajes para invitar** tiene 6 mensajes para copiar: para quien preguntó, para una
   clienta fiel, para quien comentó, después de la presentación, cuando decide unirse y cuando no es el momento.

```bash
python3 equipo/socias.py agregar --nombre "Paola Ríos" --usuario pao.rios --red instagram --nota "..."
python3 equipo/socias.py paso "Paola" explicada      # interesada, explicada, se-unio, primera-venta, activa, pausa
python3 equipo/socias.py hoy                         # a quién escribirle hoy, con el mensaje y el enlace al chat
python3 equipo/socias.py hecho <id de la tarea>      # ya le escribí
python3 equipo/socias.py lista
python3 equipo/socias.py presentacion                # salida/presentacion.html + presentacion-1..6.png
python3 equipo/socias.py mensajes                    # salida/mensajes.html
python3 equipo/socias.py guia "Paola"                # salida/guia-paola.html
python3 equipo/socias.py falta                       # lo que falta en negocio.json
python3 equipo/socias.py demo                        # ejemplo en salida/ejemplo/
```

**`negocio.json`:** lo que dice el kit sobre Farmasi. Lo que está entre [corchetes] (su enlace para
unirse, el grupo del equipo, qué hace falta para empezar y qué recibe una socia) lo completa Isabella
con los datos de su oficina: costos y descuentos cambian y no se inventan.

Lo que queda en cada computadora (no se sube): `datos/` y `salida/`.
