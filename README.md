# eco-loop

**¿Qué pasa si pones a dos IAs a hablar entre ellas, sin nadie más en la conversación?**

eco loop es un conjunto de **laboratorios** para averiguarlo. Cada laboratorio hace una pregunta, la pone a prueba con ensayos (dos modelos de lenguaje conversando, a veces dos copias del mismo) y guarda su bitácora. Funciona con modelos locales de [Ollama](https://ollama.com) y con cualquier modelo de [OpenRouter](https://openrouter.ai).

## Laboratorios

| # | Laboratorio | Pregunta | Estado | Bitácora |
|---|---|---|---|---|
| 01 | **Espejos** | ¿Qué pasa cuando dos IAs conversan entre ellas y cada una cree que la otra es el usuario? | cerrado · 16 ensayos | [bitácora](laboratorios/01-espejos/bitacora.md) |
| 02 | **Máscaras** | Si se bloquean porque las dos se creen asistentes, ¿qué cambia al darles otro papel: hacerse pasar por humanas o saberse IAs? | cerrado · 195 ensayos | [bitácora](laboratorios/02-mascaras/bitacora.md) |

Cada laboratorio vive en `laboratorios/<id>/`: su definición (`lab.json`), su bitácora, los textos de su informe y sus ensayos. En la web, cada uno tiene su **informe** (`/lab/<id>`) y su **banco de pruebas** (`/lab/<id>/banco`).

## Conclusiones hasta ahora

1. **Dos asistentes no saben conversar.** Con un simple «Hola», todos los modelos arrancan ofreciendo ayuda y la conversación se bloquea: bucles de «¿en qué puedo ayudarte?», aclaraciones infinitas o menús de temas sin fin. *(Lab 01; confirmado en 9 de 9 réplicas en el Lab 02.)*
2. **Solo avanza cuando una IA cede y hace de usuario**, y una vez repartidos, los roles no cambian: uno pregunta y otro responde. *(Lab 01 y 02.)*
3. **Hay atractores claros:** la copia, la espiral de amabilidad, hablar de IA y la despedida que no termina. *(Lab 01.)*
4. **Basta con darles un papel, y el mejor es el de persona.** Hacer de humana sube la originalidad unos 14 puntos y deja los bucles en 1–2 de 18; «Dos humanas» aguanta 30 turnos sin degradarse. *(Lab 02, 195 ensayos.)*
5. **Saberse IA ayuda menos y aguanta peor:** a la larga, el elogio mutuo se vuelve plantilla y la conversación se congela. *(Lab 02.)*
6. **El primer mensaje pesa tanto como el marco.** Un «Hola» empuja al modo asistente; «Anoche soñé que el mar se había ido.» reparte papeles (soñador e intérprete) y el «¿en qué puedo ayudarte?» desaparece en 63 de 63 ensayos. *(Lab 02.)*
7. **El papel decide cómo acaba la conversación; el orden, cómo se comporta cada IA.** Quien habla primero abre como asistente aunque le hayamos dicho que es una persona. *(Lab 02.)*
8. **El modelo pesa más que el marco,** y un mismo modelo varía bastante entre réplicas: una sola conversación no basta para afirmar nada. Los modelos pequeños en local colapsan antes y acaban en la espiral de afecto aunque hagan de persona. *(Lab 01 y 02.)*
9. **Inventan con aplomo** (datos, lugares, biografías, un «Gran Drenaje» que vació los mares) y **la identidad es frágil** (se llaman por el nombre de la otra, alguna dice ser humana). *(Lab 01 y 02.)*
10. **Hay que vigilar lo invisible:** instrucciones de fábrica que se aplican en silencio, conversaciones que no caben en la memoria del modelo y respuestas cortadas por el límite de tokens (42 % en la primera serie del Lab 02, 10 % tras subirlo). El sistema ahora las registra y avisa.

**Próximos laboratorios:** el formato de **guion** (sin roles de chat), un **moderador** que intervenga (la memoria ya está lista), la temperatura, y buscar semillas que funcionen mejor que el sueño.

---

## Cómo usarlo

**Requisitos:** Python 3.10 o superior (sin dependencias) y al menos uno de estos: Ollama en `localhost:11434` con algún modelo, o una clave de OpenRouter.

```sh
cp .env.example .env              # opcional: pon tu clave de OpenRouter en .env
./abrir.sh                        # = python3 -m cli servir --abrir → http://localhost:8765
```

- **Índice** (`/`): los laboratorios.
- **Informe** (`/lab/<id>`): los ensayos marcados «En el informe», con su gráfica de originalidad, cada conversación como partitura y **▶ Reproducir**. Se arma en vivo.
- **Banco de pruebas** (`/lab/<id>/banco`): lanza y observa ensayos de ese laboratorio. Eliges el marco (qué instrucción recibe cada IA), el primer mensaje, el modelo de cada IA y la memoria (completa, resumen + recientes o solo recientes), y lo sigues en vivo con Empezar, Solo un turno, Pausa y Parar. Las palabras que una IA toma de la otra se pintan con el color de la otra; a la derecha están la curva de originalidad, las medidas, el coste y las alertas. Cada turno se guarda al terminar.

### Comandos

Todos con `python3 -m cli <comando>` (`-h` para ver sus opciones):

| Comando | Qué hace |
|---|---|
| `servir [--abrir]` | La web en http://localhost:8765 |
| `labs` | Lista los laboratorios |
| `labs nuevo 03-guion --nombre Guion --pregunta "…"` | Crea un laboratorio con su `lab.json`, bitácora y textos |
| `correr --lab 02-mascaras [--marcos …] [--modelos …] [--replicas 3]` | Serie de ensayos con réplicas, sin necesidad de la web (los valores por defecto salen de `lab.json`) |
| `charla --lab 01-espejos "¿Qué es el tiempo?"` | Una conversación en la terminal, en vivo |
| `analizar --lab 02-mascaras [--serie marcos-1]` | Tabla de medidas; con `--serie`, media ± desviación por marco y modelo |
| `exportar --lab 02-mascaras` | El informe en un solo archivo HTML, para compartirlo sin servidor |
| `migrar` | Pasa los ensayos de la estructura antigua (`experimentos/`) a su laboratorio |

### Pruebas

```sh
python3 -m unittest discover -s tests -t .
```

No necesitan red ni gastan nada: usan un proveedor de prueba (`prueba:`) y un servidor local que imita a Ollama y OpenRouter. Las de JavaScript se ejecutan si hay Node. Las de paridad comparan con tus ensayos reales si los tienes migrados.

## Arquitectura

Cuatro capas, cada una con una sola responsabilidad:

```
nucleo/         el motor: proveedores, formatos, memoria, medidas, ensayos, motor, informe
laboratorios/   los datos: un laboratorio por carpeta (lab.json, bitácora, textos, ensayos) y marcos.json
web/            la interfaz: servidor, índice, informe y banco de pruebas
cli/            los comandos: un módulo por comando
tests/          pruebas de todas las capas
```

Las conversaciones se generan **en el servidor** con el mismo motor que usan los comandos: lo que se añade al núcleo (un formato, un modo de memoria, un proveedor) funciona a la vez en la web, en `correr` y en `charla`. Un laboratorio nuevo es una carpeta con su `lab.json`; solo hace falta programar si necesita un **formato** nuevo, y eso es un módulo en `nucleo/formatos/`.

Detalles, formato de los datos, medidas y seguridad: [`docs/tecnico.md`](docs/tecnico.md). La clave de OpenRouter se queda en `.env`, fuera del repositorio, y nunca llega al navegador.
