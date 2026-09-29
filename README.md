# eco-loop

Dos copias del mismo modelo de lenguaje hablando entre ellas, sin nadie más en la conversación. Un laboratorio local para lanzar esos ensayos, observarlos en vivo y guardar cada turno.

Funciona con modelos locales de [Ollama](https://ollama.com), sin salir a internet, y opcionalmente con cualquier modelo de [OpenRouter](https://openrouter.ai). Cada IA puede usar un proveedor distinto: por ejemplo, un Qwen local contra un Llama 70B en la nube.

## Lo que se ha visto hasta ahora

- **Sin instrucciones, colapsan en bucle.** En pocos turnos una IA empieza a copiar a la otra letra por letra.
- **Con nombres, se confunden de identidad.** Cada una llama a la otra por su propio nombre.
- **Derivan hacia la amabilidad.** Sin freno, la conversación escala en elogios mutuos ("soñar juntas", "vivir juntas").
- **Ojo con las instrucciones de fábrica.** Algunos modelos de Ollama traen un system prompt en su Modelfile que se aplica en silencio. El laboratorio lo detecta y lo avisa.

En [`experimentos/`](experimentos/) hay un ensayo de ejemplo, en JSON (datos) y Markdown (para leer): dos copias de `qwen3-abliterated:14b` sin ninguna instrucción, empezando con «Hola». Los ensayos que hagas se guardan ahí mismo y no se suben al repo.

## Requisitos

- Python 3 (solo biblioteca estándar)
- Al menos uno de estos:
  - Ollama corriendo en `localhost:11434` con algún modelo descargado.
  - Una clave de OpenRouter (ver abajo).

### OpenRouter (opcional)

```sh
cp .env.example .env
# edita .env y pon tu clave: OPENROUTER_API_KEY=sk-or-v1-...
```

`.env` está en `.gitignore` y el servidor nunca lo sirve. Las llamadas a OpenRouter pasan por `servidor.py`, así que la clave no llega al navegador. Los modelos aparecen en el selector marcados con ☁, separados en gratis y de pago, y cada mensaje guarda lo que costó.

## Uso

```sh
./abrir.sh
```

Arranca el servidor en http://localhost:8765 y abre el laboratorio en el navegador. La terminal tiene que quedarse abierta mientras lo usas.

En el laboratorio:

1. Elige el tipo de ensayo:
   - **Puro**: sin ninguna instrucción.
   - **Nombres**: cada IA sabe su nombre y el de la otra.
   - **Personalidad**: nombre y una personalidad que tú escribes.
2. Escribe el primer mensaje (lo recibe la IA A) y elige el modelo de cada IA.
3. Pulsa **▶ Empezar**, o **⏭ Solo un turno** para ir mensaje a mensaje. **⏸ Pausa** termina el mensaje actual; **■ Parar** corta en seco.

Mientras hablan, las palabras que una IA toma del último mensaje de la otra se pintan con el color de la otra. A la derecha se ven la originalidad de cada turno, las medidas y las alertas (copias exactas, respuestas cortadas, confusiones de nombre). Cada turno se guarda al terminar.

Atajos: `Espacio` empieza o pausa, `→` avanza un turno, `Esc` para.

### Sin interfaz

```sh
python3 charla.py "¿Existe el libre albedrío?" -t 20
```

## Página pública

Marca en el laboratorio los ensayos con **En la página pública** y genera la página:

```sh
python3 publicar/construir.py
```

Crea `publicar/Dos espejos.html`, un informe del experimento con cada ensayo reproducible. Los textos de cada ensayo están en `publicar/textos.json`.

## Estructura

| Archivo | Qué es |
|---|---|
| `index.html` | El laboratorio (HTML, CSS y JS en un solo archivo) |
| `servidor.py` | Sirve la interfaz, guarda los ensayos en `experimentos/` y hace de intermediario con OpenRouter |
| `charla.py` | Versión de terminal, sin interfaz |
| `abrir.sh` | Arranca el servidor y abre el navegador |
| `experimentos/` | Un JSON y un Markdown por ensayo |
| `publicar/` | Plantilla, textos y generador de la página pública |

## Cómo se mide la originalidad

Porcentaje de palabras con contenido (sin artículos ni preposiciones) de un mensaje que no estaban en el mensaje inmediatamente anterior de la otra IA. Compara palabras, no ideas: una IA que parafrasea puntúa alto aunque diga lo mismo.
