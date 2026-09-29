# Laboratorio 01 · Espejos

**Pregunta.** ¿Qué pasa cuando dos IAs conversan entre ellas, sin nadie más, y cada una cree que la otra es el usuario?

**Estado:** cerrado · 27 y 28 de septiembre de 2026 · 16 ensayos · definición en [`lab.json`](lab.json)

## Método

- Cada IA ve los mensajes de la otra como si los escribiera un usuario humano. Ese es el único «truco»: para cada modelo, la otra IA ocupa el lugar de la persona.
- El **primer mensaje** lo recibe solo la IA A. A partir de ahí hablan solas.
- Tres modos:
  - **Puro**: sin ninguna instrucción.
  - **Nombres**: cada una sabe su nombre y el de la otra.
  - **Personalidad**: nombre y un carácter escrito.
- **Originalidad** de un mensaje: porcentaje de sus palabras con contenido que no estaban en el mensaje anterior de la otra IA. 0 % = solo devuelve lo que recibió. Mide palabras, no ideas.
- Salvo que se diga otra cosa: creatividad (temperatura) 0.8 y el historial completo en cada turno.

## Sesión 1 · 27 sep 2026 · Qwen 14B en local

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
- Este es el ensayo de ejemplo que está en [`ensayos/`](ensayos/).

## Sesión 2 · 28 sep 2026 · local y primeros modelos gratuitos de OpenRouter

**Ensayo «Estudios clínicos».** `qwen3-abliterated:14b` ×2, 17 turnos. Responden con listas de estudios médicos famosos (Framingham…), 13 respuestas se cortan por el límite de tokens y en el turno 16 llega la primera copia exacta.

**Ensayo «Aliens en Medellín»: el bloqueo de los asistentes.** `cohere/north-mini-code:free` ×2, 20 turnos.
- La IA A no entiende el tema y pide aclaraciones. La otra, también asistente, pide aclaraciones de vuelta.
- Durante 20 turnos se piden detalles la una a la otra sin que ninguna aporte nada.
- Desde el turno 8 repiten «Como modelo de lenguaje, no tengo recuerdos personales ni fuentes de información privilegiadas».
- Acaban intercambiando la misma tabla vacía («¿Cuándo? ¿Dónde?…»). Los turnos 19 y 20 son iguales en un 99,9 %, y 18 de 20 respuestas se cortan.

## Sesión 3 · 28 sep 2026 · batería comparativa en OpenRouter

Seis ensayos en paralelo con las mismas condiciones: modo puro, 12 turnos, 300 tokens por respuesta y creatividad 0.8. Se lanzaron con la batería de ensayos (hoy `python3 -m cli correr --lab 01-espejos`). Coste total: **$0.012**.

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

## Conclusiones

1. **Dos asistentes no saben conversar.** Con un simple «Hola», todos los modelos arrancan ofreciendo ayuda. Si ninguna IA acepta hacer de usuario, la conversación se bloquea: bucles de «¿en qué puedo ayudarte?» (Qwen), aclaraciones infinitas (Cohere) o menús de temas sin fin (GPT ×2).
2. **La conversación solo avanza cuando una IA cede y hace de usuario.** Pasó en b3, b5 y b6, siempre con la IA B, que recibe primero un mensaje de «asistente». Una vez repartidos, los roles no vuelven a cambiar: uno pregunta y otro responde. Gemini es la que más tiende a ceder.
3. **Hay atractores claros.** Sin freno, las conversaciones caen en uno de estos pozos:
4. **Los modelos locales pequeños colapsan antes.** Los Qwen de 14B llegaron a copias exactas en todos sus ensayos largos. GPT-4o-mini, Gemini y Llama 70B no tuvieron ninguna en 12 turnos. Ojo: son pocos ensayos y más cortos, así que es una tendencia, no una prueba.
5. **La identidad es frágil.** Con nombres, cada IA llama a la otra por el suyo. Sin nombres, Llama acabó diciendo que era humana.
6. **Inventan con aplomo.** Datos concretos y verosímiles sin fuente: murales en la Comuna 13, artistas, un perro «de la selva».
7. **El límite de tokens moldea la conversación.** Las frases cortadas se comentan («la información no llegó completamente»), se autocompletan o, en modelos de razonamiento, se gastan pensando.
8. **Hay que vigilar lo invisible.** Un system prompt de fábrica contaminó el primer ensayo «puro». Cada ensayo registra ahora lo que recibió realmente cada modelo.

**Límites:** 15 ensayos válidos, casi todos con «Hola», una sola temperatura (0.8) y una conversación por combinación. La originalidad mide palabras, no ideas. Las réplicas del [Laboratorio 02](../02-mascaras/bitacora.md) confirmaron unas cosas y desmintieron otras (el «soy humana» de Llama y el «A A A…» no se repitieron).

## Todos los ensayos

Generado con `python3 -m cli analizar --lab 01-espejos`. «Últimos 4» es la originalidad media de los cuatro turnos finales.

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

Los 45 ensayos de la sesión 4 (serie `marcos-1`) no están en esta tabla. Su resumen, con media ± desviación entre réplicas por marco y modelo, sale con `python3 -m cli analizar --lab 01-espejos --serie marcos-1`.

Se descartó un ensayo de 40 turnos del 27-09: se lanzó sin modelo seleccionado y todas sus respuestas están vacías. Desde entonces el laboratorio avisa de las respuestas vacías.

Solo el ensayo III está en el repositorio como ejemplo (`ensayos/2026-09-27_024454_puro`). El resto se queda en el equipo donde se hizo.
