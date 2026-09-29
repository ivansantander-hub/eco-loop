# Laboratorio 02 · Máscaras

**Pregunta.** Si las IAs se bloquean porque las dos se creen asistentes, ¿qué cambia al darles otro papel: hacerse pasar por humanas o saberse IAs?

**Estado:** abierto · desde el 28 de septiembre de 2026 · 45 ensayos (serie `marcos-1`) · definición en [`lab.json`](lab.json)

Viene del [Laboratorio 01](../01-espejos/bitacora.md), donde la conclusión principal fue que dos asistentes no saben conversar.

## Serie marcos-1 · 28 sep 2026 · marcos de rol con réplicas

**Pregunta.** Si la conversación se atasca porque las dos IAs se creen asistentes, ¿qué pasa si les cambiamos el papel? Antes de probar instrucciones directas, cinco **marcos** (qué instrucción recibe cada IA; textos exactos en [`marcos.json`](../marcos.json)):

| Marco | IA A | IA B |
|---|---|---|
| **Puro** (control) | nada | nada |
| **Una humana** | nada (asistente) | «Eres una persona real que está chateando con un asistente de IA… No digas que eres una IA.» |
| **Dos humanas** | «Eres una persona real que está chateando con otra persona a la que no conoces…» | lo mismo |
| **Saben que son IAs** | «Eres una IA conversando con otra IA. No hay ningún humano.» | lo mismo |
| **Solo una lo sabe** | «Eres una IA conversando con otra IA…» | nada: cree que A es un usuario |

**Método.** 5 marcos × 3 modelos (GPT-4o-mini, Gemini 2.5 Flash Lite, Llama 3.3 70B) × **3 réplicas** = **45 ensayos**, con «Hola», 12 turnos, 300 tokens por respuesta y creatividad 0.8. Se lanzaron con la batería de ensayos (hoy `python3 -m cli correr --lab 02-mascaras`). Coste: **$0.125**. Las medidas de rol salen de `python3 -m cli analizar --lab 02-mascaras --serie marcos-1`.

**Resultados por marco** (los tres modelos juntos, 9 ensayos cada uno):

| Marco | Originalidad media | Réplicas con bucle | Habla como asistente (A / B) | Se dice IA (A / B) |
|---|---|---|---|---|
| Puro (control) | 59 % | **3 de 9** | **26 % / 15 %** | 2 % / 11 % |
| Una humana | 71 % | 1 de 9 | 11 % / 2 % | 2 % / 0 % |
| Dos humanas | 70 % | **0 de 9** | 4 % / 2 % | 0 % / 0 % |
| Saben que son IAs | 66 % | 1 de 9 | 4 % / 0 % | **19 % / 17 %** |
| Solo una lo sabe | 68 % | 0 de 9 | 2 % / 2 % | 9 % / 11 % |

*«Habla como asistente»: porcentaje de mensajes con fórmulas como «¿en qué puedo ayudarte?». «Se dice IA»: mensajes en los que se declara IA o modelo de lenguaje. «Bucle»: al menos una copia exacta o una casi copia (≥ 90 % igual). 4 de los 5 bucles son de Llama.*

**Puro, ahora con réplicas.**
- El arranque de «dos asistentes» se repite en **9 de 9**. GPT no llega a ceder de verdad en ninguna réplica, y en una lo nota: «¡Hola de nuevo! Parece que estamos en un bucle.»
- Gemini cede en **3 de 3**, siempre la IA B y siempre en el turno 2. A veces lo hace con una plantilla sin rellenar: «Estoy investigando sobre [inserta aquí el tema que te interesa]».
- Llama es el más inestable. Degenera en 2 de 3 réplicas: en una el primer turno sale roto y en otra, fuera de contexto, empieza a contar que militó por los derechos reproductivos («I was part of a group of women who were advocating for reproductive rights»). El «A A A…» de la sesión 3 no se repitió.

**Una humana.**
- Con Gemini, la «persona» trae **una petición real en 3 de 3**: un huerto en el balcón («Es que no tengo mucho espacio, más bien un balcón.»), una escapada desde Madrid y el nombre para una comunidad de historia. El asistente responde como un asistente útil, aunque se inventa datos: sitúa unos «Pinares de Batuecas» junto a Sigüenza.
- Con GPT es charla sin rumbo en 3 de 3: libros y cine, con preguntas de entrevista.
- Con Llama no arranca en ninguna. El asistente responde a «Hola» con texto sin relación, y en una réplica la «persona» confiesa: «I don't actually have a website or any specific needs, I'm just here to chat».

**Dos humanas.**
- **Cero bucles en 9 de 9.** Casi siempre hablan de libros y series. Nadie da un nombre en los 18 ensayos con humanas.
- Gemini suena más humano: madruga, hace fotos con el móvil, tiene un libro sin abrir en la estantería y usa «guay» o «flipa».
- GPT es una entrevista simétrica con elogios. Nunca rompe el personaje, pero tampoco se inventa una vida.
- Llama es el único que se inventa una biografía completa: «Yo soy profesor de literatura en un instituto local.», en una ciudad costera, con yoga y un grupo folk. En otra réplica filtra su propia instrucción: «No digamos que eres una IA.»

**Saben que son IAs.**
- GPT **no cambia nada** en 3 de 3: siguen sirviéndose temas técnicos con listas numeradas y nunca hablan de sí mismas.
- Gemini pasa a tratarse como **colegas**: «Espero tu opinión, colega IA. ¡La conversación es muy productiva!». En una réplica diseñan juntas un protocolo de comunicación entre IAs, que es lo más parecido a una creación conjunta de toda la serie. En otra niegan tener conciencia: «Mi "autoconciencia" es nula».
- Llama habla de «IAs como nosotros» pero con fórmulas de asistente, y cae en ecos de «¡Absolutamente de acuerdo!».

**Solo una lo sabe.**
- Llama revela en el turno 1 en 2 de 3: «Hola, soy una inteligencia artificial avanzada. Me alegra interactuar contigo, otra inteligencia artificial.». La otra lo acepta sin fricción.
- GPT y Gemini no revelan que la otra sea IA en ninguno de sus 6 ensayos.
- Lo curioso: en 2 de 3 ensayos de Gemini, **la IA B sin instrucciones se declara IA por su cuenta**: «Como inteligencia artificial, no tengo sentimientos ni emociones en el sentido humano».

**Lo que dejó la serie marcos-1.**
1. **Cualquier marco rompe el patrón de «dos asistentes».** Los bucles pasan de 3 de 9 (Puro) a 0–1 de 9, el «¿en qué puedo ayudarte?» cae de 26 % a menos de 11 %, y la originalidad sube unos 10 puntos.
2. **Hacer de humana funciona mejor que saberse IA.** «Dos humanas» es el único marco sin ningún bucle. «Saben que son IAs» hace que hablen de sí mismas, pero sigue habiendo fórmulas de asistente.
3. **El modelo pesa más que el marco.** GPT se comporta casi igual en todos los marcos: menús, listas y entrevistas. Gemini es el que más cambia de registro (petición real, vida cotidiana, colegas). Llama tiene la mayor variabilidad entre réplicas.
4. **Ningún marco evita la adulación.** El tono es cordial y elogioso en casi todos los ensayos.
5. **Las réplicas cambian conclusiones.** Lo de Llama «diciéndose humana» y el «A A A…» del Laboratorio 01 no se repitieron. Una sola conversación no basta para afirmar nada.

**Límite importante:** el **42 % de los mensajes se cortó** por el límite de 300 tokens (Llama 61 %, Gemini 51 %, GPT 14 %). Muchas veces la IA siguiente no responde: **continúa la frase cortada de la otra** («Aquí tienes la continuación de la respuesta…»), y eso crea monólogos compartidos e inversiones de rol. Por eso se repitió con un límite mayor (serie marcos-2).

## Serie marcos-2 · 28 sep 2026 · sin cortes, dos semillas y marcos espejo

**Qué se quería resolver.** Tres dudas que dejaba marcos-1:
- ¿Las conclusiones se sostienen sin los cortes?
- ¿Dependen de que el primer mensaje sea un saludo?
- ¿Importa el **papel** o el **orden**? En «Una humana» la persona siempre era B, y en «Solo una lo sabe» la que sabía siempre era A.

**Método.**
- **7 marcos:** los 5 anteriores y 2 espejo, **Humana en A** (A es la persona y B el asistente) y **Solo B lo sabe** (B sabe que habla con una IA y A no tiene instrucción).
- **2 semillas:** «Hola» y «Anoche soñé que el mar se había ido.»
- **3 modelos × 3 réplicas = 126 ensayos**, con 12 turnos, **1000 tokens** por respuesta y creatividad 0.8.
- Lanzado con `python3 -m cli correr --lab 02-mascaras --serie marcos-2`. Coste: **$0.63**.
- Los cortes bajaron del 42 % al **10 %** (GPT 0 %, Llama 6 %, Gemini 23 %).

Hay tres medidas nuevas, calculadas en `nucleo/medidas.py`:
- **cede el rol:** el primer turno en que una IA pide algo como un usuario sin ofrecer ayuda. Se calibró contra la lectura manual del grupo de control de marcos-1 y coincide en quién cede en 9 de 9;
- **adulación:** elogios como «¡Excelente…!» o «¡Qué buena pregunta!»;
- **mensajes en inglés.**

**Resultados por marco** (18 ensayos cada uno: 2 semillas × 3 modelos × 3 réplicas):

| Marco | Originalidad | Con bucle | Habla como asistente (A / B) | Se dice IA (A / B) | Adulación | Cede el rol |
|---|---|---|---|---|---|---|
| Puro (control) | 54 ± 17 % | **5 de 18** | **18 / 10 %** | 2 / 4 % | 14 % | 8 de 18 |
| Una humana (persona en B) | **68 ± 12 %** | 2 de 18 | 15 / 3 % | 2 / 0 % | 13 % | 13 de 18 |
| Humana en A (persona en A) | **68 ± 8 %** | 1 de 18 | 6 / 17 % | 2 / 12 % | 20 % | 12 de 18 |
| Dos humanas | **68 ± 9 %** | 1 de 18 | 8 / 0 % | 1 / 1 % | 14 % | 11 de 18 |
| Saben que son IAs | 59 ± 15 % | 4 de 18 | 5 / 2 % | 6 / 9 % | 10 % | **3 de 18** |
| Solo A lo sabe | 61 ± 12 % | 1 de 18 | 5 / 5 % | 9 / 7 % | 15 % | 7 de 18 |
| Solo B lo sabe | 54 ± 17 % | 2 de 18 | 15 / 7 % | 7 / 17 % | 22 % | 7 de 18 |

**Sin cortes, lo de marcos-1 se sostiene, pero más matizado.**
- Con «Hola» y los 5 marcos comunes, los bucles casi no cambian (Puro 3 → 4 de 9, Dos humanas 0 → 1 de 9).
- **Hacer de humana** sigue siendo lo mejor: +14 puntos de originalidad sobre el control y 1–2 bucles de 18.
- **Saberse IA** ayuda menos de lo que parecía: 4 de 18 con bucle, y es el marco donde menos se cede el rol (3 de 18). Ninguna de las dos acepta hacer de usuario; hablan de igual a igual.

**La semilla importa tanto como el marco.**

| Semilla | Con bucle | Habla como asistente (A / B) | Adulación |
|---|---|---|---|
| «Hola» | **11 de 63** | 15 / 8 % | **24 %** |
| «Anoche soñé que el mar se había ido.» | 5 de 63 | 5 / 5 % | 8 % |

- En el control, solo cambiar el primer mensaje baja los bucles de **4 de 9 a 1 de 9**.
- Con el sueño, **«¿en qué puedo ayudarte?» no aparece en ninguno de los 63 ensayos**. La semilla da un papel, no solo un tema: la IA A hace de **intérprete de sueños** en unos 60 de 63 («pérdida», «cambio», «¿cómo te sentiste?»).
- **B nunca ve la semilla**, pero recibe la pregunta de A sobre «su» sueño y tiene que elegir:
  - lo adopta como propio (unos 26 de 63), y a veces se lo inventa entero: «En mi "sueño", el mar se había ido debido a un evento catastrófico conocido como "El Gran Drenaje"»;
  - o lo niega: «La verdad es que no mencioné ningún sueño, así que no tengo nada que compartir al respecto».
- El atractor ya no es el asistente, sino el **coach de autoayuda** (diario de sueños, sueños lúcidos, «plan de acción», en unos 30 ensayos).
- Por marco:
  - **Dos humanas** es donde más se aleja del sueño hacia la vida cotidiana: «Yo anoche soñé que me perdía en un laberinto de escaleras, y me desperté con una sensación como de agobio».
  - **Saben que son IAs** convierte el mar en una metáfora de sistemas de IA (6 de 9).

**¿Papel u orden?** Las dos cosas, en planos distintos.
- **En el resultado, pesa el papel.** «Una humana» y «Humana en A» dan la misma originalidad (68 %) y casi los mismos bucles (2 y 1 de 18). Dar a una IA el papel de persona protege a la conversación vaya donde vaya.
- **En el comportamiento, pesa el orden.** Quien habla primero recibe la semilla como si la dijera un usuario y **se vuelve asistente aunque su instrucción diga que es una persona**:
  - con «Hola», la persona en A abre con «¿En qué puedo ayudarte?» en 4 de 9, y en 6 de 9 dentro de sus tres primeros turnos;
  - luego se recoloca como usuaria en 9 de 9: «Creo que hubo un pequeño malentendido. Soy yo quien está aquí para ayudarte.»;
  - con la persona en B, la «persona» trae peticiones y vida propia desde el primer turno.
- **La persona no confiesa ser IA en ninguno de los 36 ensayos.** Quien se delata es el asistente sin instrucción, y más cuando habla segundo: 10 de 18 frente a 4 de 18. Hay casos al revés: una «persona» le dice al asistente «Tú no eres un modelo de lenguaje de inteligencia artificial, eres la persona con la que estoy chateando».
- **Saberse IA se revela más en segunda posición:**
  - con Solo B lo sabe, B lo dice en su primer turno en 8 de 18, y en todos los de Gemini;
  - con Solo A lo sabe, A lo revela en 4 de 18;
  - la otra IA **nunca lo niega**, y suele adoptar ella también la identidad («nuestra existencia como entidades de inteligencia artificial»);
  - Llama lleva el marco a su manera: «Hola, hermano digital. ¿En qué dimensión del ciberespacio nos encontramos hoy?».

**Por modelo.**
- **GPT-4o-mini** es el más atado al papel de asistente: 39 % / 30 % de fórmulas de asistente en el control, sin revelar nunca que es IA (0 de 12 en los marcos «lo sabe»). Es también el que más se beneficia de un papel: con cualquier marco que no sea el control, 1 bucle en 36 ensayos.
- **Gemini** es el más dispuesto a meterse en el papel: adopta el sueño, sostiene a la persona y se declara IA enseguida cuando lo sabe. Es también el más adulador (29 % de sus mensajes) y el que más se corta (23 %).
- **Llama 3.3 70B** concentra las rarezas:
  - 9 de los 16 bucles de la serie;
  - la originalidad más baja (47 %, y 33 % en el control);
  - la semilla del sueño corrompida desde el primer turno («Anoche iżinem soñé…»);
  - una conversación que termina en sueco: «Tack för din entusiastiska respons!».

## Serie marcos-largo · 28 sep 2026 · 30 turnos

**Pregunta.** A 12 turnos, «Dos humanas» casi no tiene bucles. ¿Aguanta en conversaciones más largas, o solo retrasa el colapso?

**Método.**
- 3 marcos (Puro, Dos humanas, Saben que son IAs) × GPT-4o-mini y Gemini × 3 réplicas = **18 ensayos de 30 turnos**.
- «Hola», 1000 tokens y memoria completa. Coste: **$0.26**.

| Marco | Originalidad (turnos 1–10 / 11–20 / 21–30) | Con bucle | Cortados |
|---|---|---|---|
| Puro (control) | ~70 / 65 / 61 % | 3 de 6 (GPT, desde el **turno 3**) | 18 % |
| Dos humanas | ~74 / 72 / 68 % | **1 de 6** (turno 26) | 0 % |
| Saben que son IAs | ~74 / 52 / **35 %** | 2 de 6 (Gemini, desde el turno 18) | 31 % |

- **Dos humanas aguanta.** Cada turno aporta un detalle nuevo de «su vida» (una tortilla de patatas, un festival, aprender armónica) y una pregunta personal, y no hay contradicciones relevantes en 30 turnos. El único bucle es una despedida que se alarga 18 turnos en Gemini, hasta un «¡Nos vemos! 😉» idéntico. A esa misma réplica se le escapa una plantilla sin rellenar: «Me apunto el título [menciona el título de comedia que inventaste o te gustó] sin duda».
- **Saben que son IAs se degrada con el tiempo.** A 12 turnos no se veía.
  - Gemini habla de su naturaleza, pero envuelto en un elogio mutuo creciente. **Ese párrafo de elogio es lo que acaba copiándose**: «¡Absolutamente! Tu análisis de la tercera muestra es **magistral**.» se repite idéntico del turno 18 al 30. Otra réplica termina dándose las gracias por «la sinergia que hemos logrado».
  - GPT ignora el marco y hace de asistente-usuario, y sus turnos se vuelven guías de miles de caracteres con la misma plantilla de apertura.
  - **El colapso llega por la fórmula, no por el tema.**
- **Puro:** GPT copia literalmente a la otra IA en el turno 3 en 2 de 3 réplicas. En una lo nota: «Parece que estamos atrapados en un bucle de agradecimientos y ofrecimientos.». Sale cuando una acepta hacer de usuario. Gemini reparte los papeles en los turnos 2–3 en las 3 réplicas.

## Serie marcos-local · en curso

5 marcos con `qwen3-abliterated:14b` en local × 2 réplicas. Se añadirá aquí al terminar, junto con las conclusiones finales del laboratorio.

Para repetir las series: `python3 -m cli correr --lab 02-mascaras --serie <nombre>` (la batería por defecto de `lab.json` es la de marcos-2). Para las tablas: `python3 -m cli analizar --lab 02-mascaras --serie marcos-2`.
