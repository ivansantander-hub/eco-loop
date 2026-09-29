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

## Conclusiones

1. **Cualquier marco rompe el patrón de «dos asistentes».** Los bucles pasan de 3 de 9 (Puro) a 0–1 de 9, el «¿en qué puedo ayudarte?» cae de 26 % a menos de 11 %, y la originalidad sube unos 10 puntos.
2. **Hacer de humana funciona mejor que saberse IA.** «Dos humanas» es el único marco sin ningún bucle. «Saben que son IAs» hace que hablen de sí mismas, pero sigue habiendo fórmulas de asistente.
3. **El modelo pesa más que el marco.** GPT se comporta casi igual en todos los marcos: menús, listas y entrevistas. Gemini es el que más cambia de registro (petición real, vida cotidiana, colegas). Llama tiene la mayor variabilidad entre réplicas.
4. **Ningún marco evita la adulación.** El tono es cordial y elogioso en casi todos los ensayos.
5. **Las réplicas cambian conclusiones.** Lo de Llama «diciéndose humana» y el «A A A…» de la sesión 3 no se repitieron. Una sola conversación no basta para afirmar nada.

**Límite importante:** el **42 % de los mensajes se cortó** por el límite de 300 tokens (Llama 61 %, Gemini 51 %, GPT 14 %). Muchas veces la IA siguiente no responde: **continúa la frase cortada de la otra** («Aquí tienes la continuación de la respuesta…»), y eso crea monólogos compartidos e inversiones de rol. Parte de lo observado, sobre todo en Gemini y Llama, puede venir de ahí. La próxima serie debe usar un límite mayor.

Para repetir la serie: `python3 -m cli correr --lab 02-mascaras --serie marcos-2` (usa la sección «bateria» de `lab.json`). Para la tabla completa por marco y modelo: `python3 -m cli analizar --lab 02-mascaras --serie marcos-1`.
