# Atlas — Asistente Personal Inteligente

Atlas es un asistente personal inteligente desarrollado en Python utilizando **LangGraph** y **LangChain**. El proyecto implementa conversación con memoria, herramientas ejecutables y un flujo basado en el patrón **ReAct (Reason → Act → Observe → Repeat)**.

El objetivo de la aplicación es combinar un agente basado en un modelo de lenguaje con memoria a corto y largo plazo y diferentes herramientas que Atlas puede utilizar según las necesidades del usuario.

---

## Características principales

* Conversación natural mediante un modelo de lenguaje.
* Memoria contextual del usuario.
* Memoria persistente entre sesiones.
* Identificación automática de datos personales básicos.
* Uso autónomo de herramientas mediante llamadas del modelo.
* Patrón ReAct para la ejecución de herramientas.
* Ejecución secuencial de varias herramientas.
* Prevención de bucles infinitos.
* Gestión de errores.
* Persistencia de notas y recordatorios.
* Tests automáticos con `pytest`.
* Arquitectura modular separada por responsabilidades.

---

## Tecnologías utilizadas

* **Python 3.12**
* **LangGraph**
* **LangChain**
* **LangChain OpenAI**
* **OpenAI API**
* **python-dotenv**
* **pytest**
* **JSON** para la persistencia de memoria

---

## Requisitos

Para ejecutar el proyecto se necesita:

* Python 3.9 o superior.
* Una API Key de OpenAI.
* Conexión a Internet para comunicarse con el modelo.

El proyecto ha sido desarrollado y probado con Python 3.12.2.

---

## Instalación

### 1. Clonar o descargar el proyecto

Situarse en la carpeta del proyecto:

```bash
cd atlas-chatbot
```

### 2. Crear el entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

En Windows:

```bash
.venv\Scripts\activate
```

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

## Configuración de OpenAI

La API Key se almacena mediante una variable de entorno para evitar incluir credenciales directamente en el código.

Crear un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=tu_api_key
```

El archivo `.env` está incluido en `.gitignore` para evitar subir la clave a un repositorio.

La configuración del modelo se encuentra en:

```text
src/atlas/config.py
```

Actualmente se utiliza:

```python
llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0
)
```

---

## Estructura del proyecto

```text
atlas-chatbot/
│
├── .env
├── .gitignore
├── memoria.json
├── pytest.ini
├── requirements.txt
├── main.py
│
├── tests/
│   └── test_atlas.py
│
└── src/
    └── atlas/
        ├── __init__.py
        ├── config.py
        ├── errors.py
        ├── state.py
        ├── memory.py
        ├── tools.py
        ├── nodes.py
        ├── graph.py
        └── app.py
```

---

# Arquitectura

Atlas utiliza **LangGraph** para controlar el flujo de ejecución del asistente.

El estado que circula por el grafo es:

```python
class EstadoAtlas(TypedDict):
    usuario_id: str
    mensaje_actual: str
    historial: Annotated[list[BaseMessage], add_messages]
    memoria_usuario: dict
    contexto_mlp: str
    tool_calls_pendientes: list
    tool_results: list
    respuesta_final: str
    iteraciones: int
    error: str
```

Este estado contiene tanto la información necesaria para la conversación como los datos utilizados durante la ejecución de herramientas y la gestión de errores.

---

## Flujo de LangGraph

El grafo está compuesto por los siguientes nodos:

```text
START
  │
  ▼
cargar_contexto
  │
  ▼
recibir_mensaje
  │
  ▼
nodo_agente
  │
  ├───────────────┐
  │               │
  │ necesita      │ respuesta
  │ herramienta   │ directa
  ▼               ▼
ejecutar_tools  finalizar_respuesta
  │               │
  │               │
  └──────► nodo_agente
                  │
                  ▼
          guardar_memoria
                  │
                  ▼
                 END
```

Si se produce un error durante el proceso, el flujo puede dirigirse a:

```text
nodo_error
     │
     ▼
guardar_memoria
     │
     ▼
    END
```

---

# Patrón ReAct

Atlas utiliza un flujo basado en el patrón **ReAct**:

```text
Reason
   ↓
Decidir si necesita una herramienta
   ↓
Act
   ↓
Ejecutar herramienta
   ↓
Observe
   ↓
Recibir resultado
   ↓
Reason
   ↓
¿Necesita otra herramienta?
   ↓
Sí ──────────────► repetir
   │
   No
   ↓
Respuesta final
```

Por ejemplo, ante:

```text
Calcula 100 dividido 4 y luego guarda el resultado en una nota
```

Atlas puede realizar:

```text
Usuario
   ↓
Agente
   ↓
calculadora
   ↓
25
   ↓
Agente
   ↓
gestionar_notas
   ↓
Nota guardada
   ↓
Agente
   ↓
Respuesta final
```

Esto permite ejecutar varias herramientas de forma secuencial dentro de una misma petición.

---

# Memoria

Atlas utiliza memoria persistente mediante un archivo JSON.

La memoria se almacena en:

```text
memoria.json
```

Cada usuario dispone de su propio registro utilizando su `usuario_id` como identificador.

La estructura de memoria contiene:

```python
{
    "nombre": "",
    "ciudad_favorita": "",
    "preferencias": [],
    "notas": [],
    "recordatorios": [],
    "tools_usadas": {
        "calculadora": 0,
        "clima": 0,
        "notas": 0,
        "recordatorios": 0
    },
    "total_sesiones": 0,
    "ultima_sesion": ""
}
```

## Datos almacenados

### Nombre

Atlas puede detectar expresiones como:

```text
Me llamo Ana
```

y almacenar:

```text
nombre = Ana
```

### Ciudad favorita

También puede detectar:

```text
Mi ciudad favorita es Barcelona
```

y almacenar:

```text
ciudad_favorita = Barcelona
```

Estos datos pueden utilizarse posteriormente para personalizar las respuestas.

---

## Notas

Las notas se almacenan junto con:

* Identificador único.
* Contenido.
* Fecha de creación.

Ejemplo:

```json
{
    "id": "uuid",
    "contenido": "Comprar leche",
    "fecha": "2026-09-15T15:00:00"
}
```

---

## Recordatorios

Los recordatorios contienen:

* Identificador.
* Mensaje.
* Momento indicado.
* Estado de completado.

Ejemplo:

```json
{
    "id": "uuid",
    "mensaje": "Llamar al médico",
    "tiempo": "mañana a las 10:00",
    "completado": false
}
```

---

# Herramientas

Atlas dispone de cuatro herramientas principales.

## 1. Calculadora

Herramienta:

```text
calculadora
```

Permite realizar operaciones matemáticas.

Ejemplo:

```text
Usuario:
¿Cuánto es 15% de 250?

Atlas:
37.5
```

La expresión matemática se procesa utilizando el módulo `ast` de Python y un conjunto controlado de operadores permitidos.

Esto evita utilizar directamente `eval()` sobre una entrada proporcionada por el usuario.

Operadores soportados:

```text
+
-
*
/
%
**
```

También se permiten operaciones unarias como:

```text
+5
-5
```

---

## 2. Clima

Herramienta:

```text
consultar_clima
```

Consulta información meteorológica simulada para determinadas ciudades.

Actualmente contiene datos de ejemplo para:

```text
Madrid
Barcelona
Valencia
Sevilla
```

Ejemplo:

```text
Usuario:
¿Qué clima hace en Madrid?

Atlas:
[respuesta basada en el resultado de la herramienta]
```

La herramienta está preparada para devolver un mensaje controlado cuando no dispone de información sobre una ciudad.

---

## 3. Notas

Herramienta:

```text
gestionar_notas
```

Permite realizar tres operaciones:

```text
guardar
listar
buscar
```

Ejemplos:

```text
Guarda una nota que diga comprar leche
```

```text
Lista mis notas
```

```text
Busca mis notas relacionadas con leche
```

Las notas se almacenan persistentemente en `memoria.json`.

---

## 4. Recordatorios

Herramienta:

```text
crear_recordatorio
```

Permite crear recordatorios asociados al usuario.

Ejemplo:

```text
Crea un recordatorio para mañana a las 10:00
que diga llamar al médico
```

El recordatorio se guarda en la memoria persistente.

---

# Gestión de errores

Atlas dispone de diferentes niveles de gestión de errores.

Entre ellos:

* Errores de autenticación con OpenAI.
* Límites de uso de OpenAI.
* Errores de conexión.
* Errores de la API.
* Errores de ejecución de herramientas.
* Errores de lectura y escritura de memoria.
* Datos de memoria inválidos.
* Expresiones matemáticas incorrectas.
* División entre cero.
* Entradas inválidas.
* Número máximo de iteraciones.

Los errores se transforman en respuestas controladas para evitar que la aplicación termine inesperadamente.

---

# Prevención de bucles

Para evitar que el agente pueda quedarse ejecutando herramientas indefinidamente, Atlas utiliza un límite máximo de iteraciones.

Actualmente:

```python
MAX_ITERACIONES = 5
```

Si el agente alcanza este límite, el flujo termina mediante un error controlado:

```text
MAX_ITERATIONS
```

y Atlas informa al usuario de que se ha alcanzado el límite de ejecución.

Esta protección es especialmente importante porque el agente puede volver a `nodo_agente` después de ejecutar una herramienta.

---

# Archivos principales

## `config.py`

Contiene la configuración general de la aplicación:

* Carga del `.env`.
* Ruta de memoria.
* Número máximo de iteraciones.
* Configuración del modelo de OpenAI.

---

## `errors.py`

Contiene las excepciones personalizadas de la aplicación.

Actualmente incluye:

```python
ErrorMemoria
```

---

## `state.py`

Define el estado utilizado por LangGraph:

```python
EstadoAtlas
```

---

## `memory.py`

Gestiona la memoria persistente:

* Cargar memoria.
* Preparar estructura de memoria.
* Guardar memoria.
* Extraer información personal del mensaje.

---

## `tools.py`

Contiene las cuatro herramientas disponibles:

```text
calculadora
consultar_clima
gestionar_notas
crear_recordatorio
```

También contiene la configuración necesaria para registrarlas en el agente.

---

## `nodes.py`

Contiene la lógica principal de los nodos de LangGraph:

```text
cargar_contexto
recibir_mensaje
nodo_agente
ejecutar_tools
finalizar_respuesta
guardar_memoria
nodo_error
```

También contiene los routers utilizados para controlar las decisiones del grafo.

---

## `graph.py`

Construye y compila el grafo de LangGraph.

Es el archivo que conecta todos los nodos y define las transiciones entre ellos.

---

## `app.py`

Contiene la interfaz principal de la aplicación:

```python
ejecutar_atlas()
```

y el modo interactivo:

```python
modo_interactivo()
```

---

## `main.py`

Es el punto de entrada de la aplicación.

Ejecuta:

```python
modo_interactivo()
```

---

# Ejecución

Para iniciar Atlas:

```bash
python main.py
```

Aparecerá:

```text
========================================
        ATLAS - ASISTENTE PERSONAL
========================================

Introduce tu ID de usuario:
```

Después se puede comenzar a conversar.

Para finalizar:

```text
salir
```

También se aceptan:

```text
exit
quit
```

---

# Ejemplos de uso

### Conversación y memoria

```text
Tú: Hola, me llamo Pedro

Atlas: ...
```

Posteriormente:

```text
Tú: ¿Cómo me llamo?

Atlas: ...
```

---

### Calculadora

```text
Tú: ¿Cuánto es 15% de 250?

Atlas: ...
```

---

### Clima

```text
Tú: ¿Qué clima hace en Madrid?

Atlas: ...
```

---

### Notas

```text
Tú: Guarda una nota que diga comprar leche

Atlas: ...
```

Después:

```text
Tú: Lista mis notas

Atlas: ...
```

---

### Varias herramientas

```text
Tú: Calcula 100 dividido 4 y luego guarda el resultado en una nota

Atlas: ...
```

En este caso el agente puede ejecutar:

```text
calculadora → gestionar_notas
```

---

### Memoria + herramienta

Primera sesión:

```text
Tú: Me llamo Ana y mi ciudad favorita es Barcelona
```

Segunda sesión:

```text
Tú: ¿Qué clima hace en mi ciudad favorita?
```

Atlas recupera la ciudad almacenada y utiliza la herramienta de clima correspondiente.

---

# Tests automáticos

El proyecto incluye una batería de tests utilizando `pytest`.

Los tests cubren los casos principales del ejercicio:

```text
1. Conversación y memoria del nombre
2. Calculadora
3. Clima
4. Persistencia de notas
5. Ejecución secuencial de herramientas
6. Memoria + herramientas
7. Prevención de bucles
8. Recordatorios
```

Para ejecutar todos los tests:

```bash
pytest
```

El resultado esperado es:

```text
8 passed
```

---

## Memoria aislada durante los tests

Los tests no utilizan la memoria real de Atlas.

Mediante un fixture de `pytest`, cada prueba utiliza un archivo temporal:

```text
memoria_test.json
```

Esto permite ejecutar los tests repetidamente sin modificar:

```text
memoria.json
```

La memoria utilizada por cada prueba se elimina al finalizar la prueba.

---

# Seguridad

Se han aplicado algunas medidas básicas de seguridad y robustez.

### API Key

La API Key de OpenAI no está incluida directamente en el código.

Se utiliza:

```text
.env
```

y este archivo está excluido mediante:

```text
.gitignore
```

### Calculadora

No se utiliza:

```python
eval()
```

para ejecutar directamente las expresiones proporcionadas por el usuario.

En su lugar se analiza la expresión mediante `ast` y solamente se permiten determinados operadores matemáticos.

### Herramientas

Las herramientas validan sus argumentos y controlan errores para evitar que entradas incorrectas provoquen el cierre de la aplicación.

### Memoria

Los errores de lectura, escritura y formato del archivo JSON se controlan mediante excepciones específicas.

---

# Objetivos cumplidos

La implementación actual cubre los principales requisitos planteados para el ejercicio:

* [x] Conversación natural.
* [x] Memoria a corto plazo mediante el historial de mensajes.
* [x] Memoria persistente del usuario.
* [x] Herramienta de calculadora.
* [x] Herramienta de clima.
* [x] Gestión de notas.
* [x] Creación de recordatorios.
* [x] Decisión autónoma del agente sobre el uso de herramientas.
* [x] Flujo ReAct.
* [x] Ejecución secuencial de herramientas.
* [x] Persistencia de notas.
* [x] Memoria entre sesiones.
* [x] Prevención de bucles infinitos.
* [x] Gestión de errores.
* [x] Tests automáticos.
* [x] Aislamiento de la memoria durante los tests.
* [x] Código dividido por responsabilidades.

---

# Posibles mejoras futuras

La arquitectura permite ampliar Atlas con nuevas funcionalidades.

Algunas posibles mejoras son:

* Integración de una API meteorológica real.
* Búsqueda web.
* Resumen automático de conversaciones.
* Memoria semántica mediante embeddings y una base de datos vectorial.
* Sistema más avanzado de preferencias del usuario.
* Gestión y consulta de recordatorios.
* Ejecución paralela de herramientas independientes.
* Persistencia mediante una base de datos en lugar de JSON.
* Interfaz web.
* Autenticación de usuarios.
* Streaming de respuestas del modelo.
* Visualización del grafo de LangGraph.

---

# Autor

Proyecto desarrollado como parte de la formación **AI Engineer**.

**Atlas — Asistente Personal Inteligente**
