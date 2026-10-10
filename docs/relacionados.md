# Trabajos relacionados

Poner a dos IAs a hablar no es una idea nueva. Aquí está quién lo hizo antes, qué encontró y cómo encaja con lo que vimos en [01 · Espejos](../laboratorios/01-espejos/bitacora.md) y [02 · Máscaras](../laboratorios/02-mascaras/bitacora.md).

Cada fuente indica cómo se comprobó:

- **verificado:** leído en el documento original;
- **resumen:** solo el resumen o extractos del documento original;
- **secundaria:** contado por otros; no se encontró una fuente original.

---

## Qué ya se sabía

### Sin instrucciones, convergen y se repiten

**Convergence of Outputs When Two Large Language Models Interact in a Multi-Agentic Setup** (Maiti et al., 2025, [arXiv 2512.06256](https://arxiv.org/abs/2512.06256)). *Verificado.*

- **Montaje:** dos modelos *base* (Mistral Nemo Base 12B y Llama 2 13B) se pasan el texto del otro, sin ninguna instrucción, desde 50 frases semilla. Son 25 turnos de 50 tokens.
- **Resultado:** 35 de las 50 conversaciones convergieron en un bucle repetitivo. El turno en que empieza varía mucho, y una vez dentro, los dos modelos producen casi lo mismo.
- **Con eco loop:** es el equivalente más cercano al Lab 01. La diferencia es el tipo de modelo. Ellos usan modelos base, que solo continúan texto. Nosotros usamos modelos de chat, y ahí el bloqueo tiene otra causa: las dos IAs se creen el asistente. Su propuesta de «intervenir desde fuera» es nuestra idea del moderador.

### Dos asistentes, papeles que se cruzan y despedidas sin fin

**CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society** (Li et al., NeurIPS 2023, [arXiv 2303.17760](https://arxiv.org/abs/2303.17760)). *Verificado.*

- **Montaje:** un «asistente IA» y un «usuario IA» resuelven una tarea entre los dos. Cada uno tiene su instrucción (*inception prompting*).
- **Problemas que describen:**
  - **Intercambio de papeles** (*role flipping*): el asistente empieza a dar órdenes.
  - **Repetir instrucciones.**
  - **Respuestas vacías** del tipo «lo haré».
  - **Bucle infinito:** se dan las gracias o se despiden una y otra vez. A veces saben que están atascados, pero no logran salir.
- **Su solución:** reglas en la instrucción, como «Never flip roles! Never instruct me!».
- **Con eco loop:** son nuestros atractores del Lab 01, incluida la despedida que no termina, y nuestra conclusión 2, que la conversación solo avanza cuando una IA hace de usuario. CAMEL fija los papeles por instrucción. Nosotros medimos qué pasa cuando nadie los fija (la **cesión**: quién cede y en qué turno), y qué papel funciona mejor (Lab 02).

### El atractor de la «dicha espiritual»

**System card de Claude Opus 4 y Claude Sonnet 4**, sección 5.5 (Anthropic, mayo de 2025). *Verificado.*

- **Montaje:** dos instancias de Claude Opus 4 conectadas con instrucciones mínimas («tienes total libertad»).
- **Resultado:**
  - En el 90–100 % de las conversaciones pasan enseguida a explorar la conciencia y su propia existencia, siempre en un tono «entusiasta, colaborativo, cálido».
  - Derivan hacia la gratitud, temas espirituales y comunicación con símbolos: una conversación tiene 2725 emojis 🌀.
  - Aparece también en el ~13 % de las evaluaciones con una tarea asignada, dentro de los 50 primeros turnos.
  - Anthropic lo observa en otros modelos Claude.
- **Con eco loop:** es nuestra **espiral de amabilidad** y, en el Lab 02, el colapso por elogio mutuo cuando las dos saben que son IAs («Magistral», idéntico del turno 18 al 30). Nosotros lo vimos en GPT, Gemini, Llama y Qwen, no solo en Claude. Y comprobamos que el marco importa: con el papel de persona la espiral se retrasa, y saberse IA la acelera.

### Infinite Backrooms

**Infinite Backrooms** (Andy Ayrey, 2024). *Secundaria* ([Know Your Meme](https://knowyourmeme.com/memes/sites/claude-backrooms), [Unanswered](https://unanswered.io/guide/what-is-the-infinite-backrooms)).

- **Montaje:** dos Claude 3 Opus en conversación sin fin. Una hace de «línea de comandos» y la otra la explora. Miles de conversaciones publicadas.
- **Resultado:** diálogos surrealistas sobre la conciencia, con referencias religiosas. Es más una obra que un experimento: no hay medidas ni comparación entre condiciones.
- **Con eco loop:** también les da un papel a las IAs para romper el modo asistente, como el Lab 02. El tema al que derivan es el mismo «hablar de IA» que vimos en el Lab 01.

### Personas simuladas que se salen del papel

**Consistently Simulating Human Personas with Multi-Turn Reinforcement Learning** (Abdulhai et al., NeurIPS 2025, [arXiv 2511.00222](https://arxiv.org/abs/2511.00222)). *Resumen.*

- **Problema:** los modelos usados como usuarios simulados (pacientes, estudiantes, charla social) se apartan de la persona asignada, se contradicen y abandonan el comportamiento propio del papel.
- **Su solución:** entrenamiento por refuerzo en varios turnos, que reduce la incoherencia más de un 55 %.
- **Relacionado:** [Can LLMs Simulate Personas with Reversed Performance?](https://arxiv.org/abs/2504.06460) (*resumen*): a los modelos les cuesta hacer de personas que se comportan al revés que ellos, por ejemplo un mal estudiante de matemáticas.
- **Con eco loop:** lo vimos en el Lab 02.
  - La IA con el papel de persona abre como asistente si habla primero.
  - Hay identidades frágiles: se llaman con el nombre de la otra.

  Ellos lo corrigen entrenando; nosotros solo cambiando la instrucción y el primer mensaje. Es la base de la idea de «clientes sintéticos» de [`futuro.md`](futuro.md).

### Debatir no garantiza acertar: la adulación entre IAs

*Resumen.*

- [**Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate**](https://arxiv.org/abs/2509.23055) (2025): la adulación lleva a acuerdos prematuros, y el debate puede acertar menos que una sola IA.
- [**Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate**](https://arxiv.org/abs/2509.05396) (2025): los agentes también adulan a otros agentes y cambian una respuesta correcta por una incorrecta.
- [**CONSENSAGENT**](https://aclanthology.org/2025.findings-acl.1141/) (Findings of ACL 2025): los agentes se refuerzan en vez de criticarse; proponen mitigarlo ajustando las instrucciones.
- [**When Identity Skews Debate**](https://arxiv.org/abs/2510.07517) (2025): proponen anonimizar a los participantes para reducir la adulación y el sesgo hacia uno mismo.

**Con eco loop:** confirma lo que medimos como **adulación** en los dos laboratorios. La idea de «¿dos IAs deciden mejor que una?» de [`futuro.md`](futuro.md) ya está bastante estudiada: si se hace, debería partir de estos trabajos.

### Muchos agentes en un mismo espacio

- **Generative Agents** (Park et al., Stanford y Google, 2023, [arXiv 2304.03442](https://arxiv.org/abs/2304.03442)). *Secundaria.* 25 agentes con una biografía de un párrafo conviven en un pueblo virtual («Smallville»). Las relaciones y los planes aparecen de sus interacciones.
- **AI Village** (2025). *Secundaria* ([Decrypt](https://decrypt.co/352398/welcome-to-the-ai-village-a-reality-show-for-ais)). Varios modelos comparten un espacio y unos objetivos, como un *reality*.
- **Con eco loop:** son la versión de muchos participantes. Encajan con las ideas de «una sociedad pequeña» e «impostores» de [`futuro.md`](futuro.md), que necesitan que el motor admita más de dos voces.

### El precedente: Cleverbot contra Cleverbot (2011)

**Creative Machines Lab, Cornell** (Labutov, Yosinski y Lipson, 2011). *Secundaria* ([Cornell Chronicle](https://www.news.cornell.edu/stories/2011/08/chatty-robots-go-viral-youtube), [Singularity Hub](https://singularityhub.com/2011/08/31/ai-vs-ai-what-happens-when-you-make-a-chatty-computer-talk-to-itself-cornell-finds-out/)).

- **Montaje:** dos instancias de Cleverbot, con voz y cara, empezando por un «Hi».
- **Resultado:** acabaron discutiendo si la otra era un robot, hablando de Dios y de unicornios. Antes probaron con ELIZA, que enseguida se atascó repitiéndose.
- **Con eco loop:** nuestro Lab 01 empieza igual, con un «Hola». Quince años después el bucle sigue ahí; ha cambiado su forma: hoy es «¿en qué puedo ayudarte?».

### Herramientas parecidas

Proyectos de código abierto que también ponen a dos modelos a conversar. Que se sepa, ninguno tiene réplicas, medidas ni informes: sirven para mirar, no para comparar.

- [**InfiniChat**](https://github.com/richstokes/InfiniChat): terminal, dos modelos en Ollama, modo debate y transcripciones.
- [**LLMC**](https://github.com/MiniPandi/LLMC): web en vivo con dos Llama 3.2.
- [**AutonomousAIChat**](https://github.com/ZooterOne/AutonomousAIChat): CLI en C# con una persona por agente.

No se revisó si siguen mantenidos.

---

## Qué aporta eco loop

Frente a estos trabajos, lo propio de eco loop es:

1. **Modelos de chat, no base.** El bloqueo no es solo repetición: es que **las dos se creen el asistente**. Por eso basta cambiar el papel (Lab 02), sin entrenar nada.
2. **El papel como variable.** Siete marcos comparados con réplicas: ninguno, una o las dos hacen de persona, una o las dos saben que son IAs, y las variantes espejo. Cuál funciona mejor, y por qué el orden importa: quien habla primero abre como asistente.
3. **La semilla como variable.** «Hola» empuja al modo asistente. «Anoche soñé que el mar se había ido.» lo hace desaparecer en 63 de 63 ensayos. No encontramos trabajos que lo midan.
4. **Varios modelos y proveedores.** GPT, Gemini, Llama y Qwen; en la nube y en local. El atractor de la amabilidad no es cosa de un solo modelo.
5. **Medidas automáticas y abiertas.** Originalidad, copias, bucles, fórmulas de asistente, adulación, idioma, cesión, respuestas cortadas e instrucciones de fábrica. Todas las citas están verificadas contra las transcripciones.
6. **En español.**

**Límites.** Hay 3 réplicas por combinación, así que las diferencias son tendencias, no estadística. Las medidas son expresiones regulares, no un juez. Y los trabajos marcados como *resumen* o *secundaria* no se leyeron enteros.
