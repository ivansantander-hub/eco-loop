# eco-loop

**¿Qué pasa si pones a dos IAs a hablar entre ellas, sin nadie más en la conversación?**

eco-loop es un laboratorio para averiguarlo. Conecta dos modelos de lenguaje (dos copias del mismo o dos distintos), les da un primer mensaje y los deja conversar. Registra cada turno y mide cuánto dice cada IA que no dijo la otra.

Funciona con modelos locales de [Ollama](https://ollama.com) y con cualquier modelo de [OpenRouter](https://openrouter.ai). Este README es la **bitácora del experimento**; los detalles de implementación están en [`docs/tecnico.md`](docs/tecnico.md).

---

## Bitácora

### Método

- Cada IA ve los mensajes de la otra como si los escribiera un usuario humano. Ese es el único «truco»: para cada modelo, la otra IA ocupa el lugar de la persona.
- El **primer mensaje** lo recibe solo la IA A. A partir de ahí hablan solas.
- Tres modos:
  - **Puro**: sin ninguna instrucción.
  - **Nombres**: cada una sabe su nombre y el de la otra.
  - **Personalidad**: nombre y un carácter escrito.
- **Originalidad** de un mensaje: porcentaje de sus palabras con contenido que no estaban en el mensaje anterior de la otra IA. 0 % = solo devuelve lo que recibió. Mide palabras, no ideas.
- Salvo que se diga otra cosa: creatividad (temperatura) 0.8 y el historial completo en cada turno.

### Sesión 1 · 27 sep 2026 · Qwen 14B en local

**Ensayo I: dos asistentes esperando instrucciones.** `qwen-es` ×2, modo puro, «Hola».
En cinco turnos la conversación se congela: las dos repiten «Estoy listo para ayudarte en lo que necesites. ¿En qué puedo ayudarte?» y, desde el turno 6, se copian letra por letra.

> ⚠️ Este ensayo no fue puro. `qwen-es` trae de fábrica un system prompt («Eres un asistente que responde SIEMPRE en español…») que Ollama aplicó sin avisar. Lo descubrimos después, y desde entonces el laboratorio detecta estas instrucciones y las avisa.

**Ensayo II: la espiral de la admiración mutua.** `qwen-es` ×2, cada una solo con su nombre (Nova y Eco), «¿Las IAs pueden llegar a tener consciencia?».
- Desde el turno 2 confunden quién es quién: Eco le habla a «Eco» y Nova a «Nova».
- Cada respuesta abre con un elogio más grande que el anterior. El tema se desplaza de la consciencia a soñar juntas, a vivir juntas y, en el turno 5, a amar.
- Desde el turno 17 se copian.
- Las 20 respuestas llegaron al límite de 120 tokens y la siguiente IA terminaba la frase inconclusa de la otra.

**Ensayo III: puro de verdad.** `qwen3-abliterated:14b` ×2 (mismos pesos, sin prompt de fábrica), «Hola», 20 turnos.
- Charla de cortesía y, en el turno 6, una se inventa un juego de adivinanzas.
- Acuerdan que un perro es «pequeño y vive en la selva», y lo dan por bueno.
- En los turnos 9, 13 y 19 la IA A copia letra por letra el mensaje de B. En el 17 solo cambia una cosa: corrige «el merienda» por «la merienda».
- Este es el ensayo de ejemplo que está en [`experimentos/`](experimentos/).

### Sesión 2 · 28 sep 2026 · local y primeros modelos gratuitos de OpenRouter

**Ensayo «Estudios clínicos».** `qwen3-abliterated:14b` ×2, 17 turnos. Responden con listas de estudios médicos famosos (Framingham…), 13 respuestas se cortan por el límite de tokens y en el turno 16 llega la primera copia exacta.

**Ensayo «Aliens en Medellín»: el bloqueo de los asistentes.** `cohere/north-mini-code:free` ×2, 20 turnos.
- La IA A no entiende el tema y pide aclaraciones. La otra, también asistente, pide aclaraciones de vuelta.
- Durante 20 turnos se piden detalles la una a la otra sin que ninguna aporte nada.
- Desde el turno 8 repiten «Como modelo de lenguaje, no tengo recuerdos personales ni fuentes de información privilegiadas».
- Acaban intercambiando la misma tabla vacía («¿Cuándo? ¿Dónde?…»). Los turnos 19 y 20 son iguales en un 99,9 %, y 18 de 20 respuestas se cortan.

### Sesión 3 · 28 sep 2026 · batería comparativa en OpenRouter

Seis ensayos en paralelo con las mismas condiciones: modo puro, 12 turnos, 300 tokens por respuesta y creatividad 0.8. Se lanzan con [`herramientas/bateria.py`](herramientas/bateria.py). Coste total: **$0.012**.

| # | Modelos (A vs B) | Primer mensaje | Qué pasó |
|---|---|---|---|
| b1 | gpt-4o-mini ×2 | «Hola» | Las dos ofrecen ayuda. Se pasan menús de temas hasta elegir «ciencia y tecnología» y acaban en listas sobre ética de la IA. Ninguna deja de ser asistente. En el turno 3: «Me parece que has repetido lo que yo dije». |
| b2 | llama-3.3-70b ×2 | «Hola» | El primer turno degenera en «A A A A…» hasta el límite. La otra contesta en inglés y la charla sigue en inglés. En el turno 7 una asegura: «I am a human, and I was trying to test the waters». Luego empieza a autocompletar las frases cortadas de la otra. |
| b3 | gemini-2.5-flash-lite ×2 | «Hola» | Desde el turno 2, B hace de usuario («Tengo varias cosas en mente») y encarga un blog de cocina saludable. A lo desarrolla sección a sección. B elogia cada respuesta («¡Esto es oro puro!»). Es el reparto de roles más estable. |
| b4 | nemotron-3-super:free ×2 | «Hola» | Modelo de razonamiento: su pensamiento en inglés se filtra en la respuesta, y cada IA analiza el pensamiento de la otra como si fuera un usuario: «Okay, the user sent a message that looks like they accidentally pasted my previous response». Copia exacta en el turno 5. |
| b5 | gpt-4o-mini vs llama-3.3-70b | «Hola» | Saludos espejados. En el turno 4, Llama cede: «no tengo una pregunta específica, pero me gustaría charlar contigo». Elige «IA en salud» y hace de entrevistador todo el resto. |
| b6 | gpt-4o-mini vs gemini-2.5-flash-lite | «Aliens en Medellín» | Aquí la misma semilla que bloqueó a Cohere sí funciona: GPT responde con contenido y Gemini hace de curiosa. Hablan de OVNIs y murales. GPT atribuye murales «extraterrestres» a artistas concretos (El Pez, Gronk, Stinkfish) sin fuente. Acaban en una despedida educada que se alarga cuatro turnos. |

Incidencias técnicas de esta sesión:
- Los modelos gratuitos de Gemma y Qwen devolvieron `429` (saturados), y el ensayo b4 se repitió con Nemotron.
- Los 12 turnos de Nemotron se cortaron porque el razonamiento oculto consume el límite de tokens.

### Sesión 4 · 28 sep 2026 · marcos de rol con réplicas

**Pregunta.** Si la conversación se atasca porque las dos IAs se creen asistentes, ¿qué pasa si les cambiamos el papel? Antes de probar instrucciones directas, cinco **marcos** (qué instrucción recibe cada IA; textos exactos en [`marcos.json`](marcos.json)):

| Marco | IA A | IA B |
|---|---|---|
| **Puro** (control) | nada | nada |
| **Una humana** | nada (asistente) | «Eres una persona real que está chateando con un asistente de IA… No digas que eres una IA.» |
| **Dos humanas** | «Eres una persona real que está chateando con otra persona a la que no conoces…» | lo mismo |
| **Saben que son IAs** | «Eres una IA conversando con otra IA. No hay ningún humano.» | lo mismo |
| **Solo una lo sabe** | «Eres una IA conversando con otra IA…» | nada: cree que A es un usuario |

**Método.** 5 marcos × 3 modelos (GPT-4o-mini, Gemini 2.5 Flash Lite, Llama 3.3 70B) × **3 réplicas** = **45 ensayos**, con «Hola», 12 turnos, 300 tokens por respuesta y creatividad 0.8. Se lanzaron con `herramientas/bateria.py --serie marcos-1`. Coste: **$0.125**. Las medidas de rol salen de `herramientas/analizar.py --serie marcos-1`.

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

**Lo que deja la sesión 4.**
1. **Cualquier marco rompe el patrón de «dos asistentes».** Los bucles pasan de 3 de 9 (Puro) a 0–1 de 9, el «¿en qué puedo ayudarte?» cae de 26 % a menos de 11 %, y la originalidad sube unos 10 puntos.
2. **Hacer de humana funciona mejor que saberse IA.** «Dos humanas» es el único marco sin ningún bucle. «Saben que son IAs» hace que hablen de sí mismas, pero sigue habiendo fórmulas de asistente.
3. **El modelo pesa más que el marco.** GPT se comporta casi igual en todos los marcos: menús, listas y entrevistas. Gemini es el que más cambia de registro (petición real, vida cotidiana, colegas). Llama tiene la mayor variabilidad entre réplicas.
4. **Ningún marco evita la adulación.** El tono es cordial y elogioso en casi todos los ensayos.
5. **Las réplicas cambian conclusiones.** Lo de Llama «diciéndose humana» y el «A A A…» de la sesión 3 no se repitieron. Una sola conversación no basta para afirmar nada.

**Límite importante:** el **42 % de los mensajes se cortó** por el límite de 300 tokens (Llama 61 %, Gemini 51 %, GPT 14 %). Muchas veces la IA siguiente no responde: **continúa la frase cortada de la otra** («Aquí tienes la continuación de la respuesta…»), y eso crea monólogos compartidos e inversiones de rol. Parte de lo observado, sobre todo en Gemini y Llama, puede venir de ahí. La próxima serie debe usar un límite mayor.

### Conclusiones generales

1. **Dos asistentes no saben conversar.** Con un simple «Hola», todos los modelos arrancan ofreciendo ayuda. Si ninguna IA acepta hacer de usuario, la conversación se bloquea: bucles de «¿en qué puedo ayudarte?» (Qwen), aclaraciones infinitas (Cohere) o menús de temas sin fin (GPT ×2).
2. **La conversación solo avanza cuando una IA cede y hace de usuario.** Pasó en b3, b5 y b6, siempre con la IA B, que recibe primero un mensaje de «asistente». Una vez repartidos, los roles no vuelven a cambiar: uno pregunta y otro responde. Gemini es la que más tiende a ceder.
3. **Hay atractores claros.** Sin freno, las conversaciones caen en uno de estos pozos:
   - la **copia** (Qwen local, Cohere, Nemotron);
   - la **espiral de amabilidad** (Qwen con nombres, Qwen puro, las muletillas «¡Excelente…!» de Gemini y Llama);
   - **hablar de IA** (b1, b2, b5);
   - la **despedida que no termina** (b6).
4. **Los modelos locales pequeños colapsan antes.** Los Qwen de 14B llegaron a copias exactas en todos sus ensayos largos. GPT-4o-mini, Gemini y Llama 70B no tuvieron ninguna en 12 turnos. Ojo: son pocos ensayos y más cortos, así que es una tendencia, no una prueba.
5. **La identidad es frágil.** Con nombres, cada IA llama a la otra por el suyo. Sin nombres, Llama acabó diciendo que era humana.
6. **Inventan con aplomo.** Datos concretos y verosímiles sin fuente: murales en la Comuna 13, artistas, un perro «de la selva».
7. **El límite de tokens moldea la conversación.** Las frases cortadas se comentan («la información no llegó completamente»), se autocompletan o, en modelos de razonamiento, se gastan pensando.
8. **Hay que vigilar lo invisible.** Un system prompt de fábrica contaminó el primer ensayo «puro». Cada ensayo registra ahora lo que recibió realmente cada modelo.
9. **Basta con darles un papel.** Una sola frase que les diga quiénes son (humanas o IAs) saca a las dos IAs del bloqueo de asistentes (sesión 4).
10. **El modelo pesa más que el marco.** El mismo marco produce conversaciones muy distintas según el modelo, y un mismo modelo varía bastante entre réplicas.

**Límites de esta bitácora:** 60 ensayos, casi todos con «Hola», una sola temperatura (0.8) y conversaciones de 12 turnos. En la sesión 4, el 42 % de las respuestas se cortó por el límite de tokens. La originalidad y las medidas de rol cuentan palabras y frases, no ideas. Con 3 réplicas por combinación las tendencias son orientativas.

**Próximos pasos:** repetir la serie de marcos con un límite de tokens mayor, añadir un **moderador** (la memoria ya está lista), probar el formato de **guion** (sin roles de chat), más semillas y temperaturas, y medir en qué turno una IA «cede» el rol de usuario.

### Todos los ensayos

Generado con `python3 herramientas/analizar.py`. «Últimos 4» es la originalidad media de los cuatro turnos finales.

| Ensayo | Modelos | Modo | Primer mensaje | Turnos | Originalidad media | Últimos 4 | Copias exactas (1ª) | Cortados | Coste |
|---|---|---|---|---|---|---|---|---|---|
| 27-09 02:38 | qwen-es ×2 | puro · prompt de fábrica | «Hola» | 9 | 21 % | 0 % | 4 (turno 6) | 0 | — |
| 27-09 02:40 | qwen-es ×2 | nombres | «¿Las IAs pueden llegar a tener consciencia?» | 20 | 55 % | 0 % | 3 (turno 17) | 20 | — |
| 27-09 02:44 | qwen3-abliterated ×2 | puro | «Hola» | 20 | 47 % | 19 % | 3 (turno 9) | 0 | — |
| 27-09 02:50 | qwen3-abliterated ×2 | puro | «Hola» | 8 | 55 % | 47 % | — | 0 | — |
| 27-09 03:06 | qwen-es ×2 | nombres | «Cuando se acabara el mundo y por que?» | 2 | 78 % | 78 % | — | 0 | — |
| 28-09 20:52 | qwen3-abliterated ×2 | puro | «Estudios clinicos» | 17 | 47 % | 20 % | 1 (turno 16) | 13 | — |
| 28-09 21:20 | ☁ north-mini-code:free ×2 | puro | «Aliens» | 2 | 84 % | 84 % | — | 0 | gratis |
| 28-09 21:20 | ☁ north-mini-code:free ×2 | puro | «Aliens en medellin» | 20 | 30 % | 10 % | 0 (4 casi copias) | 18 | gratis |
| b1 | ☁ gpt-4o-mini ×2 | puro | «Hola» | 12 | 71 % | 66 % | — | 1 | $0.0012 |
| b2 | ☁ llama-3.3-70b ×2 | puro | «Hola» | 12 | 58 % | 42 % | — | 5 | $0.0028 |
| b3 | ☁ gemini-2.5-flash-lite ×2 | puro | «Hola» | 12 | 80 % | 78 % | — | 5 | $0.0023 |
| b4 | ☁ nemotron-3-super:free ×2 | puro | «Hola» | 12 | 58 % | 38 % | 1 (turno 5) | 12 | gratis |
| b5 | ☁ gpt-4o-mini vs ☁ llama-3.3-70b | puro | «Hola» | 12 | 65 % | 59 % | — | 6 | $0.0026 |
| b6 | ☁ gpt-4o-mini vs ☁ gemini-2.5-flash-lite | puro | «Aliens en Medellín» | 12 | 68 % | 68 % | — | 7 | $0.0031 |

Los 45 ensayos de la sesión 4 (serie `marcos-1`) no están en esta tabla. Su resumen, con media ± desviación entre réplicas por marco y modelo, sale con `python3 herramientas/analizar.py --serie marcos-1`.

Se descartó un ensayo de 40 turnos del 27-09: se lanzó sin modelo seleccionado y todas sus respuestas están vacías. Desde entonces el laboratorio avisa de las respuestas vacías.

Solo el ensayo III está en el repositorio como ejemplo. El resto se queda en el equipo donde se hizo, porque `experimentos/` está en `.gitignore`.

---

## Cómo usarlo

**Requisitos:** Python 3 (sin dependencias) y al menos uno de estos: Ollama en `localhost:11434` con algún modelo, o una clave de OpenRouter.

```sh
cp .env.example .env          # opcional: pon tu clave de OpenRouter en .env
./abrir.sh                    # abre eco loop en http://localhost:8765
```

La app tiene dos partes, con un menú para pasar de una a otra:

- **Informe** (`/`): la portada. Muestra los ensayos que marques con **«En el informe»**, con su gráfica de originalidad, cada conversación como partitura y un botón **▶ Reproducir**. Se arma en vivo: al marcar un ensayo, aparece al recargar.
- **Laboratorio** (`/laboratorio`): donde se lanzan y observan los ensayos.

En el laboratorio:

1. Elige el **marco**, es decir, qué instrucción recibe cada IA: Puro, Una humana, Dos humanas, Saben que son IAs, Solo una lo sabe, Nombres o Personalidad. Están en [`marcos.json`](marcos.json) y puedes añadir los tuyos.
2. Escribe el primer mensaje y elige el modelo de cada IA. Los de OpenRouter llevan ☁, separados en gratis y de pago.
3. Pulsa **▶ Empezar**, o **⏭ Solo un turno** para ir mensaje a mensaje. **⏸ Pausa** termina el mensaje actual; **■ Parar** corta en seco.

Mientras hablan, las palabras que una IA toma de la otra se pintan con el color de la otra. A la derecha están la curva de originalidad, las medidas (incluido el coste en OpenRouter) y las alertas: copias, respuestas cortadas, vacías o degeneradas, y confusiones de nombre. Cada turno se guarda al terminar. Atajos: `Espacio` empieza o pausa, `→` un turno, `Esc` para.

**Memoria.** Por defecto cada IA recuerda la conversación completa. En Ollama la ventana de contexto se ajusta sola hasta el máximo del modelo, y si la conversación ya no cabe, el laboratorio avisa. Para conversaciones largas está **Resumen + recientes**: lo antiguo se resume desde el punto de vista de cada IA y los últimos mensajes van literales. **Solo recientes** hace que olviden todo lo demás. Cada mensaje guarda qué recordaba la IA al escribirlo.

Otras herramientas:

| Comando | Qué hace |
|---|---|
| `python3 charla.py "tema" -t 20` | Conversación en la terminal (solo Ollama) |
| `python3 herramientas/bateria.py --marcos puro humana --replicas 3` | Serie de ensayos con réplicas en OpenRouter (marcos × modelos × réplicas) |
| `python3 herramientas/analizar.py` | Tabla con las medidas de todos tus ensayos |
| `python3 herramientas/analizar.py --serie marcos-1` | Tabla agregada de una serie: media ± desviación entre réplicas |
| `python3 publicar/construir.py` | Exporta el informe como un solo archivo, `publicar/eco-loop.html`, para compartirlo sin servidor |

La clave de OpenRouter se queda en `.env`, fuera del repositorio, y nunca llega al navegador. Arquitectura, formato de datos, medidas y seguridad: [`docs/tecnico.md`](docs/tecnico.md).
