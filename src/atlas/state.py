from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


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