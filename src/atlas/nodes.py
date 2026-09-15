from datetime import datetime

from openai import (
    AuthenticationError,
    APIConnectionError,
    APIError,
    RateLimitError
)

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage
)

from langgraph.prebuilt import ToolNode

from .config import MAX_ITERACIONES, llm
from .errors import ErrorMemoria
from .memory import (
    cargar_memoria,
    preparar_memoria,
    guardar_memoria,
    extraer_datos_usuario
)
from .state import EstadoAtlas
from .tools import tools


# ==================================================
# CONFIGURACIÓN DE TOOLS
# ==================================================

llm_con_tools = llm.bind_tools(tools)

tool_node = ToolNode(
    tools,
    messages_key="historial"
)


# ==================================================
# NODO AGENTE
# ==================================================

def nodo_agente(state: EstadoAtlas):
    contexto = state["contexto_mlp"]

    mensajes = [
        SystemMessage(
            content=f"""
Eres Atlas, un asistente personal inteligente.

ID del usuario actual:
{state["usuario_id"]}

Utiliza la siguiente información del usuario para
personalizar tus respuestas cuando sea relevante.

{contexto}

Cuando utilices una herramienta que necesite
usuario_id, utiliza exactamente el ID del usuario
actual proporcionado arriba.

Si no tienes información suficiente sobre algo,
no inventes datos.

Los datos personales como el nombre y la ciudad favorita
se guardan automáticamente en la memoria del usuario.
NO utilices gestionar_notas para guardar el nombre,
la ciudad favorita u otros datos personales que ya puedan
guardarse en la memoria del perfil.

Utiliza gestionar_notas únicamente cuando el usuario
pida explícitamente guardar, listar o buscar una nota.
"""
        ),
        *state["historial"]
    ]

    try:
        respuesta = llm_con_tools.invoke(
            mensajes
        )

    except AuthenticationError:
        return {
            "error": "OPENAI_AUTH_ERROR",
            "tool_calls_pendientes": []
        }

    except RateLimitError:
        return {
            "error": "OPENAI_RATE_LIMIT_ERROR",
            "tool_calls_pendientes": []
        }

    except APIConnectionError:
        return {
            "error": "OPENAI_CONNECTION_ERROR",
            "tool_calls_pendientes": []
        }

    except APIError:
        return {
            "error": "OPENAI_API_ERROR",
            "tool_calls_pendientes": []
        }

    except Exception:
        return {
            "error": "OPENAI_UNKNOWN_ERROR",
            "tool_calls_pendientes": []
        }

    tool_calls = getattr(
        respuesta,
        "tool_calls",
        []
    )

    iteraciones = state["iteraciones"] + 1

    if iteraciones >= MAX_ITERACIONES:
        return {
            "historial": [respuesta],
            "tool_calls_pendientes": tool_calls,
            "iteraciones": iteraciones,
            "error": "MAX_ITERATIONS"
        }

    return {
        "historial": [respuesta],
        "tool_calls_pendientes": tool_calls,
        "iteraciones": iteraciones,
        "error": ""
    }


# ==================================================
# CARGAR CONTEXTO
# ==================================================

def cargar_contexto(state: EstadoAtlas):
    try:
        memoria_usuario = cargar_memoria(
            state["usuario_id"]
        )

        memoria_usuario = preparar_memoria(
            memoria_usuario
        )

        contexto = f"""
Información conocida del usuario:

Nombre: {memoria_usuario["nombre"] or "No conocido"}
Ciudad favorita: {memoria_usuario["ciudad_favorita"] or "No conocida"}
Preferencias: {memoria_usuario["preferencias"]}
Notas: {memoria_usuario["notas"]}
Recordatorios: {memoria_usuario["recordatorios"]}
"""

        return {
            "memoria_usuario": memoria_usuario,
            "contexto_mlp": contexto,
            "error": ""
        }

    except ErrorMemoria:
        return {
            "error": "MEMORY_ERROR"
        }

    except Exception:
        return {
            "error": "MEMORY_UNKNOWN_ERROR"
        }


# ==================================================
# RECIBIR MENSAJE
# ==================================================

def recibir_mensaje(state: EstadoAtlas):
    return {
        "historial": [
            HumanMessage(
                content=state["mensaje_actual"]
            )
        ]
    }


# ==================================================
# EJECUTAR TOOLS
# ==================================================

def ejecutar_tools(state: EstadoAtlas):
    try:
        resultado = tool_node.invoke(
            state
        )

        tool_results = []

        for mensaje in resultado.get(
            "historial",
            []
        ):
            if isinstance(mensaje, ToolMessage):
                tool_results.append(
                    mensaje.content
                )

        return {
            "historial": resultado.get(
                "historial",
                []
            ),
            "tool_results": tool_results,
            "tool_calls_pendientes": [],
            "error": ""
        }

    except Exception:
        return {
            "tool_results": [],
            "tool_calls_pendientes": [],
            "error": "TOOL_EXECUTION_ERROR"
        }


# ==================================================
# FINALIZAR RESPUESTA
# ==================================================

def finalizar_respuesta(state: EstadoAtlas):
    ultimo_mensaje = state["historial"][-1]

    return {
        "respuesta_final": ultimo_mensaje.content
    }


# ==================================================
# GUARDAR MEMORIA
# ==================================================

def guardar_memoria_nodo(state: EstadoAtlas):
    try:
        memoria_usuario = preparar_memoria(
            cargar_memoria(
                state["usuario_id"]
            )
        )

        memoria_usuario = extraer_datos_usuario(
            state["mensaje_actual"],
            memoria_usuario
        )

        equivalencias = {
            "calculadora": "calculadora",
            "consultar_clima": "clima",
            "gestionar_notas": "notas",
            "crear_recordatorio": "recordatorios"
        }

        for mensaje in state["historial"]:
            if hasattr(mensaje, "tool_calls"):
                for tool_call in mensaje.tool_calls:
                    nombre_tool = tool_call["name"]

                    nombre_memoria = equivalencias.get(
                        nombre_tool
                    )

                    if nombre_memoria:
                        memoria_usuario[
                            "tools_usadas"
                        ][nombre_memoria] += 1

        memoria_usuario["total_sesiones"] += 1
        memoria_usuario["ultima_sesion"] = (
            datetime.now().isoformat()
        )

        guardar_memoria(
            state["usuario_id"],
            memoria_usuario
        )

        return {
            "memoria_usuario": memoria_usuario,
            "error": ""
        }

    except ErrorMemoria:
        return {
            "error": "MEMORY_SAVE_ERROR"
        }

    except Exception:
        return {
            "error": "MEMORY_SAVE_UNKNOWN_ERROR"
        }


# ==================================================
# NODO DE ERROR
# ==================================================

def nodo_error(state: EstadoAtlas):
    error = state["error"]

    if error == "TOOL_EXECUTION_ERROR":
        return {
            "respuesta_final": (
                "No he podido completar la operación porque "
                "ha ocurrido un error al ejecutar una herramienta."
            )
        }

    if error == "OPENAI_AUTH_ERROR":
        return {
            "respuesta_final": (
                "No se ha podido autenticar con OpenAI. "
                "Comprueba la configuración de la API."
            )
        }

    if error == "OPENAI_RATE_LIMIT_ERROR":
        return {
            "respuesta_final": (
                "Se ha alcanzado el límite de uso de OpenAI. "
                "Inténtalo de nuevo más tarde."
            )
        }

    if error == "OPENAI_CONNECTION_ERROR":
        return {
            "respuesta_final": (
                "No se ha podido conectar con OpenAI. "
                "Comprueba tu conexión a Internet e inténtalo de nuevo."
            )
        }

    if error == "OPENAI_API_ERROR":
        return {
            "respuesta_final": (
                "OpenAI ha devuelto un error al procesar la solicitud. "
                "Inténtalo de nuevo más tarde."
            )
        }

    if error == "OPENAI_UNKNOWN_ERROR":
        return {
            "respuesta_final": (
                "Ha ocurrido un error inesperado al comunicarse "
                "con el modelo."
            )
        }

    if error == "MAX_ITERATIONS":
        return {
            "respuesta_final": (
                "He alcanzado el límite máximo de iteraciones "
                "para evitar un bucle en la ejecución."
            )
        }

    if error == "MEMORY_ERROR":
        return {
            "respuesta_final": (
                "Ha ocurrido un problema al acceder a la memoria "
                "del usuario. No se ha podido completar la operación."
            )
        }

    if error == "MEMORY_SAVE_ERROR":
        return {
            "respuesta_final": (
                "La operación se ha completado, pero no he podido "
                "guardar los cambios en la memoria del usuario."
            )
        }

    if error == "MEMORY_SAVE_UNKNOWN_ERROR":
        return {
            "respuesta_final": (
                "La operación se ha completado, pero ha ocurrido "
                "un problema al guardar la memoria."
            )
        }

    return {
        "respuesta_final": (
            "Ha ocurrido un error inesperado al procesar "
            "tu solicitud."
        )
    }


# ==================================================
# ROUTERS
# ==================================================

def router(state: EstadoAtlas):
    if state["error"]:
        return "error"

    if state["iteraciones"] >= MAX_ITERACIONES:
        return "error"

    ultimo_mensaje = state["historial"][-1]

    if (
        hasattr(ultimo_mensaje, "tool_calls")
        and ultimo_mensaje.tool_calls
    ):
        return "tools"

    return "finalizar"


def router_contexto(state: EstadoAtlas):
    if state["error"]:
        return "error"

    return "continuar"