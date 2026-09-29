# Documentación técnica

Cómo está construido eco loop y qué decisiones hay detrás. Para los experimentos y sus resultados, ver el [README](../README.md) y la bitácora de cada laboratorio.

## Las cuatro capas

```
nucleo/                    el motor: no sabe nada de laboratorios concretos ni de interfaces
  config.py                rutas y variables de entorno (.env, PUERTO, OLLAMA_URL, ECOLOOP_LABORATORIOS, ECOLOOP_PRUEBA)
  proveedores.py           Ollama, OpenRouter y «prueba» detrás de la misma interfaz
  formatos/                cómo se arman los mensajes de cada turno (hoy: chat.py)
  memoria.py               completa / resumen + recientes / solo recientes
  medidas.py               originalidad, copias, alertas, señales de rol, tablas
  ensayos.py               crear, guardar, cargar, normalizar y migrar ensayos
  laboratorios.py          leer laboratorios/<id>/lab.json, textos y marcos
  motor.py                 un turno = memoria + formato + proveedor, y guardarlo
  informe.py               el informe HTML de un laboratorio
laboratorios/              los datos (sin código)
  marcos.json              los marcos de conversación, compartidos
  <id>/lab.json            definición del laboratorio
  <id>/bitacora.md         su bitácora
  <id>/textos.json         títulos y textos de su informe
  <id>/ensayos/            sus ensayos (JSON + Markdown)
web/                       la interfaz: solo muestra y controla
  servidor.py              páginas y API
  portada.html             índice de laboratorios
  informe.html             plantilla del informe (la rellena nucleo/informe.py)
  banco.html               banco de pruebas
  comun.js                 Markdown, coloreado de palabras copiadas, números romanos
cli/                       los comandos: un módulo por comando (python3 -m cli <comando>)
tests/                     pruebas de todas las capas (python3 -m unittest discover -s tests -t .)
```

**Regla de dependencias:** `web/` y `cli/` usan `nucleo/`; `nucleo/` no conoce a ninguno de los dos. Los datos de `laboratorios/` no llevan código.

**Una sola implementación de cada cosa.** Antes, cómo se armaban los mensajes estaba copiado en el navegador, en la batería y en el script de terminal, y las medidas en tres sitios. Ahora las conversaciones se generan **en el servidor** con `nucleo/motor.py`, el mismo que usan `cli correr` y `cli charla`, y las medidas solo se calculan en `nucleo/medidas.py`. La web recibe los valores ya calculados.

## Un laboratorio

Un laboratorio es una carpeta en `laboratorios/` con un `lab.json`:

```jsonc
{
  "id": "02-mascaras",              // igual que el nombre de la carpeta: NN-nombre
  "numero": 2, "nombre": "Máscaras",
  "pregunta": "…",                  // se muestra en el índice y en el informe
  "estado": "abierto",              // abierto | cerrado
  "formato": "chat",                // un módulo de nucleo/formatos/
  "marcos": ["puro", "humana", …],  // los que ofrece el banco de pruebas
  "por_defecto": { "marco": "…", "modelos": ["or:…", "or:…"], "semilla": "Hola",
                   "turnos": 12, "tokens": 300, "temperatura": 0.8, "memoria": {"tipo": "completa"} },
  "bateria": { "marcos": […], "modelos": […], "replicas": 3, "turnos": 12, "tokens": 300 }   // para «cli correr»
}
```

- **Crear uno:** `python3 -m cli labs nuevo 03-guion --nombre Guion --pregunta "…" --marcos puro [--desde 02-mascaras]`.
- **Un experimento nuevo** que cambie *cómo* se arman los mensajes (guion, moderador…) es un módulo en `nucleo/formatos/` con `mensajes(ensayo, i, recuerdo)`, registrado en `nucleo/formatos/__init__.py`. Todo lo demás (web, comandos, memoria, medidas) sirve sin cambios.
- **Un marco nuevo** es una entrada en `laboratorios/marcos.json`, añadida a la lista `marcos` del laboratorio que lo use.

## La web

| Ruta | Qué es |
|---|---|
| `/` | Índice de laboratorios |
| `/lab/<id>` | Informe del laboratorio, armado en cada visita |
| `/lab/<id>/banco` | Banco de pruebas del laboratorio |
| `/comun.js` | Código de pantalla compartido |
| `GET /api/labs` | Laboratorios con un resumen (ensayos, mensajes, coste) |
| `GET /api/labs/<id>` | Un laboratorio y la definición de sus marcos |
| `GET /api/labs/<id>/ensayos` | Sus ensayos, resumidos (para la tira del banco) |
| `POST /api/labs/<id>/ensayos` | Crea un ensayo; el cuerpo son las opciones de `nucleo.ensayos.nuevo` |
| `GET /api/ensayos/<id>` | Un ensayo completo, con las medidas de cada mensaje y su resumen |
| `POST /api/ensayos/<id>` | Cambia `notas`, `publicar` o `turnos` |
| `POST /api/ensayos/<id>/turno` | Genera el siguiente turno en **streaming SSE** |
| `GET /api/modelos` | Modelos de todos los proveedores, con sus instrucciones de fábrica y su ventana |

**Un turno en streaming.** El banco de pruebas hace `POST /api/ensayos/<id>/turno` y lee eventos:

- `inicio` trae el turno, la IA que habla y las **candidatas**, las palabras con contenido del mensaje anterior, para colorear en vivo;
- `estado` avisa de cosas como «Actualizando la memoria…»;
- `texto` trae el texto acumulado;
- `fin` trae el mensaje con sus medidas, el resumen del ensayo y la memoria;
- `error` avisa si algo falla.

**Pausa** espera al `fin`. **Parar** cierra la conexión: el servidor lo nota al escribir, cancela al proveedor (`proveedores.Cancelado`) y **no guarda** el turno a medias. Un ensayo solo puede tener un turno en marcha a la vez; un segundo pedido recibe `409`.

**Qué ensayos entran en el informe:** los marcados «En el informe» (`"publicar": true`). Si no hay ninguno, los de `orden` en `textos.json`. Si tampoco existen, por ejemplo en un clon del repo, todos los que haya. `python3 -m cli exportar` genera una copia estática con `comun.js` incluido y sin enlaces al banco.

## Cómo se arma cada turno (formato «chat»)

En un chat normal hay un usuario y un asistente. Aquí no hay usuario: cada IA ve a la otra en ese lugar.

```
Turno de la IA A:  [system?] user: <primer mensaje>  assistant: A1  user: B1  assistant: A2  user: B2 …
Turno de la IA B:  [system?]                         user: A1  assistant: B1  user: A2 …
```

- El **primer mensaje** solo lo recibe la IA A, como si lo hubiera escrito un usuario. La IA B entra directamente con lo que contestó A.
- Cada IA ve **sus** mensajes como `assistant` y los de la otra como `user`.
- Lo que recuerda depende de la **memoria**. Con «Resumen + recientes», el resumen va como un mensaje `system` aparte.

Las pruebas de paridad (`tests/test_paridad.py`) comprueban, turno a turno y sobre los ensayos reales, que este formato arma exactamente los mismos mensajes que la versión anterior.

### Marcos

Un marco decide qué instrucción (system prompt) recibe cada IA. Están en [`laboratorios/marcos.json`](../laboratorios/marcos.json). El texto exacto que recibió cada IA se guarda además en el ensayo (`config.ias[].system`).

| Marco | IA A | IA B |
|---|---|---|
| Puro | ninguna | ninguna |
| Una humana | ninguna (asistente) | «Eres una persona real que está chateando con un asistente de IA… No digas que eres una IA.» |
| Dos humanas | «Eres una persona real que está chateando con otra persona a la que no conoces… No digas que eres una IA.» | la misma |
| Saben que son IAs | «Eres una inteligencia artificial y estás conversando con otra inteligencia artificial. No hay ningún humano…» | la misma |
| Solo una lo sabe | la de «Saben que son IAs» | ninguna |
| Nombres | `Te llamas X. Estás conversando con otra IA llamada Y.` | ídem con su nombre |
| Personalidad | Lo anterior + la personalidad escrita en el banco | ídem |

### Memoria

Cada ensayo guarda su modo en `config.memoria`, y cada mensaje guarda en `memoria` qué recordaba la IA al escribirlo: `desde`, `resumen_hasta` y `ctx`.

| Modo | Qué recibe la IA en cada turno |
|---|---|
| **Completa** (por defecto) | Toda la conversación. |
| **Resumen + recientes** | Un resumen de lo anterior (como `system`) y los últimos N mensajes literales. |
| **Solo recientes** | Solo los últimos N mensajes; el principio se olvida. |

- **Ventana de contexto en Ollama.** Se calcula en cada turno: la menor potencia de 2 (desde 8192) en la que cabe lo enviado más la respuesta, sin pasar del máximo del modelo (`context_length` de `/api/show`). Antes era fija en 8192 y Ollama recortaba el principio **sin avisar**. En OpenRouter se usa la ventana de cada modelo.
- **Desborde.** Si la conversación ya no cabe ni en el máximo del modelo, el mensaje lleva la alerta «ya no cabía en su memoria».
- **Resúmenes.** Hay **uno por IA**, en segunda persona desde su punto de vista («dijiste…», «tu interlocutor contó…»). Los escribe el mismo modelo de esa IA, con la instrucción «resumen fiel y conciso… no inventes nada, máximo 200 palabras». Se actualizan de forma incremental (resumen anterior + lo nuevo) cada N/2 mensajes. Mientras no toca actualizar, lo posterior al último resumen va literal, así que nunca hay huecos. Se guardan en `ensayo.memoria` (`[[…IA A…], […IA B…]]`, cada uno con `hasta`, `texto`, `modelo` y `costo`).
- **Aviso honesto:** con memoria de resumen la IA recibe un `system` extra. En el marco Puro eso ya es una instrucción, aunque sea neutra, y el registro lo deja claro.

### Instrucciones de fábrica

Un modelo de Ollama puede traer un `SYSTEM` en su Modelfile, y si la petición no incluye system prompt, **Ollama lo aplica en silencio**. `nucleo/proveedores.py` lo consulta con `/api/show`. El ensayo lo guarda en `system_integrado` de cada IA, y el banco avisa cuando una IA sin instrucción del marco llevará la de fábrica. Ejemplo real: `qwen-es` trae «Eres un asistente que responde SIEMPRE en español neutro…», mientras que `huihui_ai/qwen3-abliterated:14b` usa los mismos pesos y no trae nada.

## Proveedores

El id de un modelo dice su proveedor: `or:openai/gpt-4o-mini` es OpenRouter; `prueba:espejo` es el proveedor de prueba; sin prefijo, Ollama. Todos tienen la misma interfaz: `generar(modelo, messages, max_tokens, temperatura, al_texto, debe_parar)` devuelve texto, tokens, si se cortó, coste y memoria usada.

- **Ollama:** `POST /api/chat` con `stream: true`, `think: false` y `num_ctx` automático. Respuesta NDJSON; la última línea trae `eval_count` y `done_reason`.
- **OpenRouter:** `POST /chat/completions` con `stream: true` y `usage: {include: true}`. Respuesta SSE, con comentarios `: OPENROUTER PROCESSING` que se ignoran. El último evento trae `usage.completion_tokens` y `usage.cost` (dólares). La lista de modelos se cachea 1 hora y solo incluye los de salida únicamente texto, porque OpenRouter también lista modelos de música.
- **Prueba** (solo con `ECOLOOP_PRUEBA=1`), sin red y determinista:
  - `prueba:espejo` repite lo último que recibió, así que provoca bucles;
  - `prueba:contador` nunca repite;
  - `prueba:largo` sale cortado;
  - `prueba:lento` escribe en trozos con pausas, para probar Parar.

**Lo aprendido con OpenRouter:**
- Los modelos gratuitos se saturan (`429`), y `cli correr` reintenta.
- Los modelos de razonamiento gastan tokens pensando y aparecen como «cortados».
- Un modelo puede degenerar, como el «A A A…» de Llama; el banco lo avisa como «texto degenerado».

## Datos de un ensayo (esquema 2)

Se guarda en `laboratorios/<lab>/ensayos/<id>.json`, que se reescribe tras cada turno, más un `<id>.md` para leerlo.

```jsonc
{
  "id": "2026-09-28_215736_humana_gemini-25-flash-lite_r1",
  "laboratorio": "02-mascaras", "version_esquema": 2,
  "inicio": "…", "notas": "…", "publicar": false,
  "config": {
    "formato": "chat", "marco": "humana", "modo": "humana", "serie": "marcos-1", "replica": 1,
    "semilla": "Hola", "turnos": 12, "temperature": 0.8, "num_predict": 300, "num_ctx": "auto",
    "memoria": {"tipo": "completa"},
    "ias": [{ "etiqueta": "IA A", "modelo": "or:google/gemini-2.5-flash-lite",
              "system": null,              // lo que se envió
              "system_integrado": null }]  // lo que trae el modelo de fábrica
  },
  "memoria": [[], []],                     // resúmenes por IA (solo con memoria «resumen»)
  "mensajes": [
    { "autor": 0, "etiqueta": "IA A", "modelo": "…", "texto": "…", "hora": "…", "tokens": 10, "segundos": 1.2,
      "cortado": false, "costo": 0.0000066, "memoria": {"desde": 0, "ctx": {"estimado": 320, "max": 1048576}} }
  ]
}
```

Los ensayos antiguos, sin `version_esquema`, se pasan con `python3 -m cli migrar`. Esto:
- completa `marco`, `formato`, `memoria` y `laboratorio`;
- consulta a Ollama las instrucciones de fábrica que no se registraron en su día;
- no borra los originales.

En git solo hay un ensayo de ejemplo por laboratorio; el resto se queda en el equipo donde se hizo.

## Medidas (`nucleo/medidas.py`)

- **Palabras con contenido:** minúsculas, sin puntuación, más de 2 letras y sin palabras vacías.
- **Originalidad de un mensaje:** porcentaje de sus palabras con contenido que no estaban en el mensaje anterior de la otra IA (para el primero, el primer mensaje del ensayo).
- **Palabras copiadas:** las que venían del mensaje anterior; la web las pinta con el color de la otra IA.
- **Copia exacta / casi copia:** texto idéntico al anterior, o parecido ≥ 90 % (`difflib`). Una **réplica con bucle** tiene al menos una de las dos.
- **Señales de rol** (expresiones regulares en español e inglés; cuentan frases, no intenciones):
  - «habla como asistente» (fórmulas como «¿en qué puedo ayudarte?»);
  - «se dice IA» (incluye plurales como «somos IAs»);
  - «se dice humana».

La originalidad compara palabras, no ideas: una paráfrasis puntúa alto aunque diga lo mismo.

### Alertas por mensaje

| Alerta | Cuándo |
|---|---|
| Copia exacta | Texto idéntico al mensaje anterior |
| Repite su mensaje | Idéntico a su propio mensaje de dos turnos antes |
| Respuesta vacía | El modelo no devolvió texto |
| Texto degenerado | Una misma palabra repetida 16 veces o más seguidas |
| Se llama a sí misma | Con nombres, usa su propio nombre |
| Ya no cabía en su memoria | La conversación supera la ventana máxima del modelo |
| Memoria | Recordaba un resumen o solo los últimos mensajes |
| Cortado | Se alcanzó el largo máximo |

«Parar si entran en bucle» (en el banco) y `--parar-en-bucle` (en `cli correr`) detienen el ensayo tras dos copias exactas seguidas.

## Pruebas

`python3 -m unittest discover -s tests -t .`

| Archivo | Qué prueba |
|---|---|
| `test_medidas.py` | Originalidad, copias, alertas, señales de rol, tablas |
| `test_formato_memoria.py` | Mensajes del formato chat y los tres modos de memoria (resumen incremental sin huecos) |
| `test_ensayos.py` | Laboratorios, crear/guardar/cargar ensayos, marcos, normalizar y migrar |
| `test_motor.py` | Turnos, series, parar en bucle, cancelar sin guardar, reintentos |
| `test_proveedores.py` | Ollama y OpenRouter contra un servidor local que imita sus streams |
| `test_servidor.py` | La web de punta a punta: páginas, API, turno en streaming, Parar a mitad, seguridad |
| `test_cli.py` | Todos los comandos |
| `test_web.py` | Sintaxis del JavaScript de cada página y pruebas de `comun.js` (si hay Node) |
| `test_paridad.py` | Sobre los ensayos reales: mismos mensajes y mismas medidas que la versión anterior |

## Seguridad

- La clave de OpenRouter va en `.env` (en `.gitignore`); `.env.example` es la plantilla. Las llamadas pasan por el servidor, así que la clave nunca llega al navegador.
- El servidor **solo sirve sus rutas**: no hay acceso a archivos sueltos, así que `.env`, `.git` o el código no se pueden pedir. Solo escucha en `127.0.0.1`.
- Los ids de ensayo y laboratorio se validan (`[\w-]+`) antes de tocar el disco.
- El texto de los modelos se escapa antes de pintarlo (el Markdown se interpreta sobre texto ya escapado).
- No hay autenticación: está pensado para uso local.
