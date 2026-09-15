import pytest

import src.atlas.memory as memory
from src.atlas.app import ejecutar_atlas
from src.atlas.nodes import nodo_agente


@pytest.fixture(autouse=True)
def memoria_temporal(tmp_path, monkeypatch):
    ruta_temporal = tmp_path / "memoria_test.json"

    monkeypatch.setattr(
        memory,
        "RUTA_MEMORIA",
        ruta_temporal
    )

    yield


def obtener_llamadas_tools(resultado):
    """Devuelve todas las llamadas a herramientas realizadas por Atlas."""
    llamadas = []

    for mensaje in resultado["historial"]:
        tool_calls = getattr(mensaje, "tool_calls", [])

        for tool_call in tool_calls:
            llamadas.append(tool_call)

    return llamadas


def obtener_resultados_tools(resultado):
    """Devuelve los resultados producidos por las herramientas."""
    resultados = []

    for mensaje in resultado["historial"]:
        if getattr(mensaje, "type", None) == "tool":
            resultados.append(mensaje.content)

    return resultados


def test_conversacion_y_memoria_nombre():
    resultado = ejecutar_atlas(
        "test_nombre",
        "Hola, me llamo Pedro"
    )

    assert resultado["respuesta_final"]
    assert "Pedro" in resultado["respuesta_final"]

    assert resultado["memoria_usuario"]["nombre"] == "Pedro"


def test_calculadora():
    resultado = ejecutar_atlas(
        "test_calculadora",
        "¿Cuánto es 15% de 250?"
    )

    assert resultado["respuesta_final"]

    assert (
        "37,5" in resultado["respuesta_final"]
        or "37.5" in resultado["respuesta_final"]
    )

    llamadas = obtener_llamadas_tools(resultado)

    assert any(
        getattr(mensaje, "tool_calls", [])
        for mensaje in resultado["historial"]
    )


def test_clima():
    resultado = ejecutar_atlas(
        "test_clima",
        "¿Qué clima hace en Madrid?"
    )

    assert resultado["respuesta_final"]

    llamadas = obtener_llamadas_tools(resultado)

    assert any(
        llamada["name"] == "consultar_clima"
        for llamada in llamadas
    )

    resultados = obtener_resultados_tools(resultado)

    assert any(
        "28" in resultado_tool
        for resultado_tool in resultados
    )


def test_notas():
    usuario_id = "test_notas"

    resultado_guardar = ejecutar_atlas(
        usuario_id,
        "Guarda una nota que diga comprar leche"
    )

    assert resultado_guardar["respuesta_final"]

    llamadas_guardar = obtener_llamadas_tools(
        resultado_guardar
    )

    assert any(
        llamada["name"] == "gestionar_notas"
        for llamada in llamadas_guardar
    )

    resultado_listar = ejecutar_atlas(
        usuario_id,
        "Lista mis notas"
    )

    assert resultado_listar["respuesta_final"]

    assert (
        "comprar leche"
        in resultado_listar["respuesta_final"].lower()
    )

    llamadas_listar = obtener_llamadas_tools(
        resultado_listar
    )

    assert any(
        llamada["name"] == "gestionar_notas"
        for llamada in llamadas_listar
    )


def test_herramientas_secuenciales():
    usuario_id = "test_secuencial"

    resultado = ejecutar_atlas(
        usuario_id,
        "Calcula 100 dividido 4 y luego guarda "
        "el resultado en una nota"
    )

    assert resultado["respuesta_final"]

    llamadas = obtener_llamadas_tools(resultado)

    nombres_tools = [
        llamada["name"]
        for llamada in llamadas
    ]

    assert "calculadora" in nombres_tools
    assert "gestionar_notas" in nombres_tools

    resultado_notas = ejecutar_atlas(
        usuario_id,
        "Lista mis notas"
    )

    assert "25" in resultado_notas["respuesta_final"]


def test_memoria_y_tools():
    usuario_id = "test_memoria_tools"

    resultado_sesion_1 = ejecutar_atlas(
        usuario_id,
        "Me llamo Ana y mi ciudad favorita es Barcelona"
    )

    assert resultado_sesion_1["memoria_usuario"]["nombre"] == "Ana"
    assert (
        resultado_sesion_1["memoria_usuario"]["ciudad_favorita"]
        == "Barcelona"
    )

    resultado_sesion_2 = ejecutar_atlas(
        usuario_id,
        "¿Qué clima hace en mi ciudad favorita?"
    )

    assert resultado_sesion_2["respuesta_final"]

    llamadas = obtener_llamadas_tools(
        resultado_sesion_2
    )

    assert any(
        llamada["name"] == "consultar_clima"
        for llamada in llamadas
    )

    resultados = obtener_resultados_tools(
        resultado_sesion_2
    )

    assert any(
        "25" in resultado_tool
        for resultado_tool in resultados
    )

    assert "Barcelona" in resultado_sesion_2["respuesta_final"]


def test_prevencion_bucle():
    estado = {
        "usuario_id": "test_bucle",
        "mensaje_actual": "Haz algo",
        "historial": [],
        "memoria_usuario": {},
        "contexto_mlp": "",
        "tool_calls_pendientes": [],
        "tool_results": [],
        "respuesta_final": "",
        "iteraciones": 5,
        "error": ""
    }

    resultado = nodo_agente(estado)

    assert resultado["error"] == "MAX_ITERATIONS"

def test_recordatorio():
    resultado = ejecutar_atlas(
        "test_recordatorio",
        "Crea un recordatorio para mañana a las 10:00 "
        "que diga llamar al médico"
    )

    assert resultado["respuesta_final"]

    llamadas = obtener_llamadas_tools(resultado)

    assert any(
        llamada["name"] == "crear_recordatorio"
        for llamada in llamadas
    )

    memoria = resultado["memoria_usuario"]

    assert len(memoria["recordatorios"]) >= 1

    recordatorio = memoria["recordatorios"][-1]

    assert "llamar al médico" in recordatorio["mensaje"].lower()
    assert recordatorio["completado"] is False