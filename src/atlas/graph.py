from langgraph.graph import StateGraph, START, END

from .state import EstadoAtlas

from .nodes import (
    cargar_contexto,
    recibir_mensaje,
    nodo_agente,
    ejecutar_tools,
    finalizar_respuesta,
    guardar_memoria_nodo,
    nodo_error,
    router,
    router_contexto
)


# ==================================================
# GRAFO
# ==================================================

builder = StateGraph(EstadoAtlas)


builder.add_node(
    "cargar_contexto",
    cargar_contexto
)

builder.add_node(
    "recibir_mensaje",
    recibir_mensaje
)

builder.add_node(
    "nodo_agente",
    nodo_agente
)

builder.add_node(
    "ejecutar_tools",
    ejecutar_tools
)

builder.add_node(
    "finalizar_respuesta",
    finalizar_respuesta
)

builder.add_node(
    "guardar_memoria",
    guardar_memoria_nodo
)

builder.add_node(
    "nodo_error",
    nodo_error
)


builder.add_edge(
    START,
    "cargar_contexto"
)


builder.add_conditional_edges(
    "cargar_contexto",
    router_contexto,
    {
        "continuar": "recibir_mensaje",
        "error": "nodo_error"
    }
)


builder.add_edge(
    "recibir_mensaje",
    "nodo_agente"
)


builder.add_conditional_edges(
    "nodo_agente",
    router,
    {
        "tools": "ejecutar_tools",
        "finalizar": "finalizar_respuesta",
        "error": "nodo_error"
    }
)


builder.add_edge(
    "ejecutar_tools",
    "nodo_agente"
)


builder.add_edge(
    "nodo_error",
    "guardar_memoria"
)


builder.add_edge(
    "finalizar_respuesta",
    "guardar_memoria"
)


builder.add_edge(
    "guardar_memoria",
    END
)


graph = builder.compile()