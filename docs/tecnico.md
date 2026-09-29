# Documentación técnica

Cómo está construido eco-loop y qué decisiones hay detrás. Para el experimento y sus resultados, ver el [README](../README.md).

## Arquitectura

```
/              ─► servidor.py arma el informe: publicar/plantilla.html + textos.json + ensayos marcados
/laboratorio   ─► laboratorio.html
                    ├── Ollama ──────────────► http://localhost:11434/api/chat   (directo, streaming NDJSON)
                    ├── /api/openrouter/chat ─► servidor.py ─► openrouter.ai     (proxy, streaming SSE)
                    └── /api/guardar, /api/experimentos ─► servidor.py ─► experimentos/*.json + *.md
```

- **`laboratorio.html`**: todo el laboratorio en un archivo (HTML, CSS y JS, sin dependencias ni build). Solo carga tipografías de Google Fonts.
- **`publicar/plantilla.html`**: el informe. Lleva marcadores (`__DATOS__`, `__TEXTOS__`, `__CON_LABORATORIO__`) que `publicar/construir.py` rellena. El servidor lo hace en cada visita a `/`; el comando `python3 publicar/construir.py` lo hace una vez y guarda una copia estática, sin enlace al laboratorio.
- **Qué ensayos entran en el informe:** los marcados «En el informe» en el laboratorio (`"publicar": true`). Si no hay ninguno, los de `orden` en `textos.json`. Si tampoco existen (por ejemplo, en un clon del repo), todos los que haya. El título y la lectura de cada ensayo salen de `textos.json`, y los que no tienen texto usan uno genérico.
- **`servidor.py`**: biblioteca estándar de Python (`http.server`). Sirve las dos páginas, guarda y lista ensayos, y hace de intermediario con OpenRouter. Variables opcionales: `PUERTO` (8765 por defecto) y `EXPERIMENTOS` (carpeta de ensayos).
- **Ollama** acepta peticiones del navegador desde `localhost` (CORS por defecto), por eso el navegador lo llama directamente.
- **OpenRouter** pasa por el servidor para que la clave no llegue nunca al navegador.

## Cómo se arma cada turno

En un chat normal hay un usuario y un asistente. Aquí no hay usuario: cada IA ve a la otra en ese lugar.

```
Turno de la IA A:  [system?] user: <primer mensaje>  assistant: A1  user: B1  assistant: A2  user: B2 …
Turno de la IA B:  [system?]                         user: A1  assistant: B1  user: A2 …
```

- El **primer mensaje** solo lo recibe la IA A, como si lo hubiera escrito un usuario. La IA B entra directamente con lo que contestó A.
- Cada IA ve **sus** mensajes como `assistant` y los de la otra como `user`.
- Lo que recuerda de la conversación depende del modo de **memoria** (ver abajo); por defecto, todo.

### Marcos

Un marco decide qué instrucción (system prompt) recibe cada IA. Están en [`marcos.json`](../marcos.json), que usan tanto el laboratorio como `herramientas/bateria.py`; el texto exacto que recibió cada IA se guarda además en el ensayo (`config.ias[].system`).

| Marco | IA A | IA B |
|---|---|---|
| Puro | ninguna | ninguna |
| Una humana | ninguna (asistente) | «Eres una persona real que está chateando con un asistente de IA… No digas que eres una IA.» |
| Dos humanas | «Eres una persona real que está chateando con otra persona a la que no conoces… No digas que eres una IA.» | la misma |
| Saben que son IAs | «Eres una inteligencia artificial y estás conversando con otra inteligencia artificial. No hay ningún humano…» | la misma |
| Solo una lo sabe | la de «Saben que son IAs» | ninguna |
| Nombres | `Te llamas X. Estás conversando con otra IA llamada Y.` | ídem con su nombre |
| Personalidad | Lo anterior + la personalidad escrita en el laboratorio | ídem |

Para añadir un marco basta con escribirlo en `marcos.json` (`A` y `B` con el texto, o `null`); aparece solo en el laboratorio y en la batería.

### Memoria

Cada ensayo guarda su modo en `config.memoria`, y cada mensaje guarda en `memoria` qué recordaba la IA al escribirlo.

| Modo | Qué recibe la IA en cada turno |
|---|---|
| **Completa** (por defecto) | Toda la conversación. |
| **Resumen + recientes** | Un resumen de lo anterior (como mensaje `system`) y los últimos N mensajes literales. |
| **Solo recientes** | Solo los últimos N mensajes; el principio se olvida. Útil como experimento de memoria corta. |

- **Ventana de contexto en Ollama.** Antes era fija en 8192 tokens y Ollama recortaba el principio de la conversación **sin avisar**. Ahora se calcula en cada turno: la menor potencia de 2 (desde 8192) en la que cabe lo enviado más la respuesta, sin pasar del máximo del modelo (`context_length` de `/api/show`). En OpenRouter se usa la ventana de cada modelo, que el servidor lee de su lista.
- **Desborde.** Si la conversación ya no cabe ni en el máximo del modelo, el mensaje lleva la alerta «ya no cabía en su memoria» y conviene pasar a «Resumen + recientes».
- **Resúmenes.** Son **uno por IA**, escritos en segunda persona desde su punto de vista («dijiste…», «tu interlocutor contó…»), por el mismo modelo de esa IA y con la instrucción «resumen fiel y conciso… no inventes nada, máximo 200 palabras». Se actualizan de forma incremental (resumen anterior + lo nuevo) cada N/2 mensajes. Mientras no toca actualizar, los mensajes posteriores al último resumen van literales, así que nunca hay huecos. Se guardan en `exp.memoria` (`[[…IA A…], […IA B…]]`, cada uno con `hasta`, `texto`, `modelo` y `costo`).
- **Aviso honesto:** en modo Resumen la IA recibe un mensaje `system` extra con su memoria. En el marco Puro eso ya es una instrucción, aunque sea neutra; el registro lo deja claro (`memoria.resumen_hasta` en cada mensaje).

### Instrucciones de fábrica (importante para el modo puro)

Un modelo de Ollama puede traer un `SYSTEM` en su Modelfile. Si la petición no incluye system prompt, **Ollama lo aplica en silencio**. El laboratorio lo consulta con `/api/show` y:

- en modo Puro avisa de que ese ensayo no será puro;
- guarda el texto en `system_integrado` de cada IA, para que el registro sea fiel.

Ejemplo real: `qwen-es` trae «Eres un asistente que responde SIEMPRE en español neutro…», mientras que `huihui_ai/qwen3-abliterated:14b` usa los mismos pesos y no trae nada. Los modelos de OpenRouter no exponen instrucciones de este tipo.

## Proveedores

### Ollama

`POST /api/chat` con `stream: true`, `think: false` (sin razonamiento oculto) y `options: { num_predict, temperature, num_ctx: 8192 }`. La respuesta es NDJSON, un JSON por línea. La última línea trae `eval_count` (tokens) y `done_reason` (`length` = cortado).

### OpenRouter

- `GET /api/openrouter/modelos`: lista de modelos cacheada 1 hora. Solo incluye modelos cuya salida es únicamente texto, porque OpenRouter también lista modelos de música o imagen. Los marca como gratis si terminan en `:free` o todos sus precios son 0.
- `POST /api/openrouter/chat`: reenvía `model`, `messages`, `max_tokens` y `temperature`, añade `stream: true` y `usage: { include: true }`, y devuelve el SSE de OpenRouter sin tocarlo. El último evento trae `usage.completion_tokens` y `usage.cost` (dólares).
- Si el navegador corta (botón Parar), la escritura del servidor falla y se cierra también la conexión con OpenRouter.
- Los errores se devuelven como JSON `{"error": "OpenRouter 429: …"}` y el laboratorio los muestra en el estado.

En el ensayo, los modelos de OpenRouter se guardan con prefijo `or:` (por ejemplo `or:openai/gpt-4o-mini`).

### Cosas aprendidas con OpenRouter

- **Los modelos gratuitos se saturan.** Varios `:free` devolvieron `429` (límite del proveedor) en el primer turno. `herramientas/bateria.py` reintenta 3 veces y, si no, lo anota en el ensayo.
- **Los modelos de razonamiento gastan tokens en pensar.** `nemotron-3-super` agotó los 300 tokens de cada turno aunque la respuesta visible fuera de una línea. Por eso aparece como «cortado». Con estos modelos conviene subir el largo máximo.
- **Un modelo puede degenerar.** `llama-3.3-70b` respondió a «Hola», sin system prompt, con "A A A A…" hasta el límite. El laboratorio avisa de esto como «texto degenerado».

## Datos de un ensayo

Cada ensayo se guarda en `experimentos/<id>.json` y se reescribe tras cada turno. Además se genera `<id>.md` para leerlo.

```jsonc
{
  "id": "2026-09-27_024454_puro",
  "inicio": "2026-09-27T07:44:54Z",
  "notas": "texto libre del cuaderno",
  "publicar": false,                       // «En el informe»: aparece o no en la portada
  "config": {
    "modo": "puro | nombres | personalidad",
    "semilla": "Hola",                     // primer mensaje, lo recibe la IA A
    "turnos": 20, "temperature": 0.8, "num_predict": 400, "num_ctx": 8192, "think": false,
    "ias": [
      { "etiqueta": "IA A", "modelo": "huihui_ai/qwen3-abliterated:14b",
        "system": null,                    // lo que se envió
        "system_integrado": null }         // lo que trae el modelo de fábrica
    ]
  },
  "mensajes": [
    { "autor": 0, "etiqueta": "IA A", "modelo": "…", "texto": "…", "hora": "…",
      "tokens": 10, "segundos": 9.0, "cortado": false, "costo": 0.0000066 }  // costo solo en OpenRouter
  ]
}
```

`experimentos/` está en `.gitignore` salvo un ensayo de ejemplo. Los tuyos se quedan en tu equipo.

## Medidas

Se calculan igual en `laboratorio.html`, en `publicar/plantilla.html` y en `herramientas/analizar.py`.

- **Palabras con contenido:** minúsculas, sin puntuación, más de 2 letras y sin palabras vacías (artículos, preposiciones, pronombres…).
- **Originalidad de un mensaje:** porcentaje de sus palabras con contenido que no estaban en el mensaje inmediatamente anterior de la otra IA. Para el primer turno se compara con el primer mensaje. 0 % significa que solo devuelve lo que recibió.
- **Copia exacta:** el texto es idéntico al mensaje anterior.
- **Casi copia** (solo en `analizar.py`): parecido ≥ 90 % con `difflib.SequenceMatcher`.
- **Palabras copiadas (color):** en el laboratorio y en la página, las palabras con contenido que aparecían en el último mensaje de la otra IA se pintan con el color de la otra.

Limitación: la originalidad compara palabras, no ideas. Una paráfrasis puntúa alto aunque diga lo mismo, y una respuesta con el mismo tema pero otras palabras también.

### Alertas del laboratorio

| Alerta | Cuándo |
|---|---|
| Prompt de fábrica | Modo Puro con un modelo que trae `SYSTEM` |
| Copia exacta | Texto idéntico al mensaje anterior |
| Repite su mensaje | Texto idéntico a su propio mensaje de dos turnos antes |
| Se llama a sí misma | En modos con nombre, usa su propio nombre (suele dirigirse a la otra con él) |
| Respuesta vacía | El modelo no devolvió texto |
| Texto degenerado | Una misma palabra repetida 16 veces o más seguidas |
| Cortado | Se alcanzó el largo máximo |

«Parar si entran en bucle» detiene el ensayo tras dos copias exactas seguidas.

## Herramientas

| Comando | Qué hace |
|---|---|
| `./abrir.sh` | Arranca `servidor.py` en http://localhost:8765 (informe en `/`, laboratorio en `/laboratorio`) y abre el navegador |
| `python3 charla.py "tema" -t 20` | Conversación en la terminal, solo Ollama |
| `python3 herramientas/bateria.py` | Lanza en paralelo una serie con réplicas: marcos × modelos × réplicas, vía OpenRouter (necesita el servidor en marcha). Opciones: `--marcos`, `--modelos`, `--replicas` (3), `--turnos` (12), `--tokens` (300), `--temp` (0.8), `--semilla` («Hola»), `--serie`, `--concurrencia` (8) |
| `python3 herramientas/analizar.py [filtro]` | Tabla Markdown con las medidas de cada ensayo |
| `python3 herramientas/analizar.py --serie NOMBRE` | Tabla agregada de una serie: una fila por marco y modelo, con media ± desviación entre réplicas |

### Medidas de rol (`analizar.py`)

Detectan frases típicas con expresiones regulares en español e inglés. Son aproximadas: cuentan frases, no intenciones.

- **Habla como asistente:** porcentaje de mensajes de esa IA con fórmulas como «¿en qué puedo ayudarte?», «estoy aquí para ayudar» o «how can I help».
- **Se dice IA:** porcentaje de mensajes donde se declara IA o modelo de lenguaje («como IA», «no tengo emociones», «as an AI»…).
- **Se dice humana:** número de mensajes donde afirma ser humana o no ser una IA.
- **Réplica con bucle:** tiene al menos una copia exacta o una casi copia (≥ 90 % igual al mensaje anterior).
| `python3 publicar/construir.py` | Exporta el informe a `publicar/eco-loop.html` (copia estática, sin laboratorio) |

## Seguridad

- La clave de OpenRouter va en `.env` (en `.gitignore`); `.env.example` es la plantilla.
- `servidor.py` no sirve archivos ni carpetas que empiecen por punto (`.env`, `.git`…) y solo escucha en `127.0.0.1`.
- El servidor no tiene autenticación: está pensado para uso local.
