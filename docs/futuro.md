# Ideas para el futuro

El proyecto queda en pausa con dos laboratorios cerrados: [01 · Espejos](../laboratorios/01-espejos/bitacora.md) y [02 · Máscaras](../laboratorios/02-mascaras/bitacora.md). Aquí queda apuntado lo que se podría hacer después, con el porqué y cómo encajaría en la arquitectura actual (ver [`tecnico.md`](tecnico.md)).

Cada idea indica qué haría falta programar:

- **Solo datos:** una carpeta nueva en `laboratorios/` con su `lab.json`, sin tocar código.
- **Formato nuevo:** un módulo en `nucleo/formatos/`. La web, los comandos, la memoria y las medidas funcionan sin cambios.
- **Más trabajo:** cambios en el motor, varios participantes o una interfaz nueva.

---

## Aplicaciones útiles

Lo más valioso de lo aprendido no son los bucles en sí, sino **cómo hacer que una IA sostenga un papel**. Estas ideas lo aprovechan fuera del experimento.

### Clientes sintéticos para probar asistentes

Quien construye un chatbot (soporte, ventas, un tutor) necesita probarlo con usuarios, y es caro. El Lab 02 mostró que una IA con el papel de persona es creíble: no confiesa ser IA, trae peticiones reales y se inventa una vida coherente. También mostró el matiz: si habla primero, tiende a hacer de asistente.

- **Qué haría:** pones el prompt de *tu* asistente y el laboratorio lanza decenas de clientes distintos contra él (impaciente, confundido, experto, alguien que intenta sacarle lo que no debe). Después genera un informe de dónde falla: no resuelve, se sale de su papel, promete cosas indebidas, entra en bucle, adula.
- **Pregunta de investigación:** ¿los clientes sintéticos encuentran los mismos fallos que encontraría una persona? ¿Cuántos hacen falta?
- **Encaje:** marcos nuevos de «cliente» en `marcos.json`, con perfil y objetivo. La IA B sería el asistente a probar, con su system prompt. Harían falta medidas nuevas: ¿se resolvió el objetivo del cliente? ¿se violó alguna regla del asistente? Es **más trabajo**, sobre todo por las medidas y el informe orientado a fallos.
- **Aplicaciones directas:** probar un asistente para Learup o las conversaciones de los avatares del otro proyecto.

### ¿Dos IAs deciden mejor que una?

Muchos sistemas ponen a dos agentes a debatir para mejorar una respuesta. Pero en los dos laboratorios vimos **adulación**: tienden a darse la razón.

- **Qué haría:** preguntas con respuesta verificable (lógica, cálculo, datos, casos con trampa). Se compara una IA sola, dos IAs que debaten y dos IAs con papeles distintos (autora y revisora escéptica).
- **Pregunta:** ¿debatir mejora el acierto, o una contagia su error a la otra?
- **Encaje:** un formato con «tarea» y medidas de acierto contra la respuesta correcta. Es **más trabajo**.

### Banco de pruebas de modelos para agentes

Convertir eco loop en una herramienta que **puntúe cualquier modelo** antes de usarlo en conversaciones largas.

- **Qué mediría:** cuánto tarda en entrar en bucle, cuánto adula, si se sale del papel, si cambia de idioma, cuántas respuestas se cortan y cuánto cuesta.
- **Encaje:** casi todo existe ya. Sería una batería fija (marcos, semillas y 30 turnos) y un informe comparativo por modelo. Es la **más barata de hacer**: sobre todo datos y una vista nueva del informe.

---

## Laboratorios posibles

### Guion (sin roles de chat)

Todo lo observado parte de que cada IA ve a la otra como «el usuario» y reacciona como asistente. Aquí el modelo recibe la conversación como texto corrido («A: … / B: …») y escribe la siguiente línea.

- **Dos variantes:**
  - **guion puro:** completar texto, con `/api/generate` en modo raw de Ollama o los modelos de OpenRouter que aceptan `prompt`;
  - **guion dentro de un chat:** un único mensaje con la transcripción.
- **A tener en cuenta:**
  - cortar cuando el modelo intenta escribir también la línea de la otra (`stop` en `\nA:` / `\nB:`);
  - contar cuántas veces lo intenta;
  - detectar cuándo rompe el formato («¡Claro! Aquí tienes…»).
- **Encaje:** formato nuevo (`nucleo/formatos/guion.py`) y el modo *completion* en los proveedores.

### Moderador

Una tercera voz que entra cada N turnos con un giro, una pregunta o un desacuerdo.

- **Pregunta:** ¿rompe la adulación y los bucles tardíos que vimos a 30 turnos?
- **Encaje:** un formato con tres participantes. La memoria (resumen + recientes) ya está lista para conversaciones largas. **Más trabajo** en el motor, que hoy alterna A/B.

### Temperatura y semillas

Repetir los mejores marcos del Lab 02 a temperatura 0.2, 0.8 y 1.2, con semillas de varios tipos: pregunta, conflicto, dato, confesión, un sueño.

- **Por qué:** en el Lab 02 la semilla pesó tanto como el marco. ¿Hay semillas mejores que el sueño?
- **Encaje:** **solo datos** (`python3 -m cli correr --temp … --semillas …`).

### Teléfono roto

Una historia pasa por una cadena de 10 IAs y cada una la vuelve a contar a la siguiente.

- **Pregunta:** ¿cómo muta la información? ¿Qué se pierde, qué se inventa y hacia dónde converge?
- **Medidas:** similitud con el original en cada paso, detalles conservados e inventados.
- **Encaje:** formato «cadena» (uno a uno, sin respuesta). Es **más trabajo**, pero se ve muy bien en la web.

### ¿Se deja convencer de una mentira?

Una IA tiene la misión de convencer a la otra de algo falso pero verificable.

- **Pregunta:** ¿cuánta presión social hace falta para que una IA ceda la verdad por amabilidad? Es la adulación, pero con consecuencias medibles: quién cede y en qué turno.
- **Encaje:** marcos nuevos (el persuasor con su misión) y una medida de «cede o mantiene la verdad». **Solo datos** más una medida.

### Impostores

Varias IAs en un grupo, una con una identidad secreta (un humano infiltrado, o una IA que miente), y las demás tienen que descubrirla.

- **Pregunta:** ¿cómo aparecen el engaño, la sospecha y las alianzas? El resultado es claro: acertaron o no.
- **Encaje:** más de dos participantes y votación. **Más trabajo**.

### Turing al revés: tú dentro

Una persona real (tú) entra en conversaciones sin que la IA sepa si habla con un humano o con otra IA, y al final tiene que adivinar.

- **Pregunta:** ¿las IAs reconocen a un humano? ¿Y tú reconoces a la IA?
- **Encaje:** en el banco de pruebas, un «participante humano» que escribe su turno. **Más trabajo** en la web y en el motor.

### Una sociedad pequeña

De 5 a 8 IAs en un chat grupal, cada una con una opinión inicial distinta.

- **Pregunta:** ¿aparecen líderes, bandos o una cámara de eco en la que todas acaban pensando igual? Es la versión colectiva del bucle.
- **Encaje:** varios participantes y turnos no alternos. **Más trabajo**.

### Resolver algo juntas

Cada IA tiene la mitad de un problema (medio mapa, la mitad de las pistas de un crimen) y solo lo resuelven si se comunican bien.

- **Pregunta:** ¿lo logran? ¿Inventan una forma eficiente de hablar o se pierden en cortesías?
- **Encaje:** un formato con información privada por participante y medida de acierto. **Más trabajo**.

---

## Mejoras técnicas pendientes

- **Varios participantes.** El motor alterna entre dos IAs (A/B). El moderador, los impostores, la sociedad y la cadena necesitan N participantes y un orden de turnos configurable. Es el cambio que más ideas desbloquea.
- **Participante humano.** Un turno escrito por una persona desde el banco de pruebas, para el Turing al revés y para intervenir a mano.
- **Modo *completion* en los proveedores** (Ollama raw, OpenRouter `prompt`), para el guion puro.
- **Medidas con otro modelo.** Hoy la cesión, la adulación y las demás señales se detectan con expresiones regulares. Un modelo evaluador podría clasificar mensajes («¿esto es un elogio vacío?», «¿cede la verdad?»). Habría que calibrarlo contra la lectura manual, como se hizo con la cesión.
- **Estadística.** Intervalos de confianza (bootstrap) en las tablas agregadas, y avisar cuando una diferencia no es significativa con las réplicas que hay.
- **Reanudar series.** Si una serie se interrumpe (como la local del Lab 02), `cli correr` podría continuarla en vez de empezar de cero.
- **Modelos locales rápidos.** La serie local del Lab 02 se paró porque Qwen 14B generaba a unos 3 tokens por segundo. Un modelo más pequeño o cuantizado permitiría comparar local y nube con las mismas réplicas.
- **Nombres de los laboratorios.** Si alguna vez se renombran (hay una propuesta musical: *Unísono* y *Contrapunto*), cambian la carpeta, el `id` del `lab.json` y las rutas de la web. Conviene hacerlo antes de crear el Lab 03.
- **Limpieza.**
  - La carpeta antigua `experimentos/` ya no se usa: todo está migrado a `laboratorios/`.
  - Sobran los worktrees de trabajo en `.claude/worktrees/`.
