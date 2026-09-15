import ast
import operator
import uuid

from datetime import datetime

from langchain_core.tools import tool

from .errors import ErrorMemoria
from .memory import (
    cargar_memoria,
    preparar_memoria,
    guardar_memoria
)


# ==================================================
# CALCULADORA
# ==================================================

OPERADORES_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow
}


OPERADORES_UNARIOS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg
}


def evaluar_expresion_segura(nodo):
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, (int, float)):
            return nodo.value

        raise ValueError("Solo se permiten números.")

    if isinstance(nodo, ast.BinOp):
        operador = OPERADORES_BINARIOS.get(
            type(nodo.op)
        )

        if operador is None:
            raise ValueError("Operador no permitido.")

        izquierda = evaluar_expresion_segura(
            nodo.left
        )

        derecha = evaluar_expresion_segura(
            nodo.right
        )

        return operador(izquierda, derecha)

    if isinstance(nodo, ast.UnaryOp):
        operador = OPERADORES_UNARIOS.get(
            type(nodo.op)
        )

        if operador is None:
            raise ValueError("Operador no permitido.")

        valor = evaluar_expresion_segura(
            nodo.operand
        )

        return operador(valor)

    raise ValueError(
        "La expresión contiene elementos no permitidos."
    )


@tool
def calculadora(expresion: str) -> str:
    """
    Evalúa una expresión matemática de forma segura.
    """

    try:
        if not expresion or not isinstance(expresion, str):
            return "Debes proporcionar una expresión matemática."

        expresion = expresion.strip()

        if not expresion:
            return "Debes proporcionar una expresión matemática."

        arbol = ast.parse(
            expresion,
            mode="eval"
        )

        resultado = evaluar_expresion_segura(
            arbol.body
        )

        return str(resultado)

    except ZeroDivisionError:
        return "No se puede dividir entre cero."

    except (SyntaxError, ValueError):
        return (
            "No he podido realizar el cálculo. "
            "La expresión no es válida."
        )

    except OverflowError:
        return "El resultado del cálculo es demasiado grande."

    except Exception:
        return (
            "Ha ocurrido un error inesperado "
            "al realizar el cálculo."
        )


# ==================================================
# CLIMA
# ==================================================

@tool
def consultar_clima(ciudad: str) -> str:
    """
    Consulta el tiempo actual de una ciudad.
    """

    try:
        if not ciudad or not isinstance(ciudad, str):
            return "Debes indicar una ciudad válida."

        ciudad = ciudad.strip()

        if not ciudad:
            return "Debes indicar una ciudad válida."

        clima_simulado = {
            "madrid": "Soleado, 28°C",
            "barcelona": "Parcialmente nublado, 25°C",
            "valencia": "Soleado, 27°C",
            "sevilla": "Soleado, 32°C"
        }

        resultado = clima_simulado.get(
            ciudad.lower()
        )

        if resultado is None:
            return (
                f"No tengo datos del tiempo para {ciudad}."
            )

        return resultado

    except Exception:
        return (
            "Ha ocurrido un error inesperado "
            "al consultar el clima."
        )


# ==================================================
# NOTAS
# ==================================================

@tool
def gestionar_notas(
    usuario_id: str,
    accion: str,
    contenido: str = ""
) -> str:
    """
    Gestiona las notas del usuario.

    Acciones disponibles:
    - guardar: guarda una nueva nota.
    - listar: devuelve todas las notas.
    - buscar: busca notas que contengan un término.
    """

    try:
        if not usuario_id or not isinstance(usuario_id, str):
            return "No se ha proporcionado un usuario válido."

        if not accion or not isinstance(accion, str):
            return (
                "Debes indicar una acción válida: "
                "'guardar', 'listar' o 'buscar'."
            )

        memoria_usuario = cargar_memoria(
            usuario_id
        )

        memoria_usuario = preparar_memoria(
            memoria_usuario
        )

        accion = accion.lower().strip()

        if accion == "guardar":
            if not contenido or not isinstance(contenido, str):
                return "No se puede guardar una nota vacía."

            if not contenido.strip():
                return "No se puede guardar una nota vacía."

            nota = {
                "id": str(uuid.uuid4()),
                "contenido": contenido.strip(),
                "fecha": datetime.now().isoformat()
            }

            memoria_usuario["notas"].append(nota)

            guardar_memoria(
                usuario_id,
                memoria_usuario
            )

            return (
                f"Nota guardada: {contenido.strip()}"
            )

        if accion == "listar":
            notas = memoria_usuario["notas"]

            if not notas:
                return "No tienes ninguna nota guardada."

            resultado = "\n".join(
                f"{i + 1}. {nota['contenido']}"
                for i, nota in enumerate(notas)
            )

            return (
                f"Tus notas guardadas son:\n{resultado}"
            )

        if accion == "buscar":
            if not contenido or not isinstance(contenido, str):
                return "Debes indicar qué quieres buscar."

            if not contenido.strip():
                return "Debes indicar qué quieres buscar."

            termino = contenido.lower().strip()

            resultados = [
                nota
                for nota in memoria_usuario["notas"]
                if termino in nota["contenido"].lower()
            ]

            if not resultados:
                return (
                    f"No encontré ninguna nota "
                    f"que contenga '{contenido}'."
                )

            resultado = "\n".join(
                f"- {nota['contenido']}"
                for nota in resultados
            )

            return (
                f"Notas encontradas:\n{resultado}"
            )

        return (
            f"Acción no válida: {accion}. "
            "Usa 'guardar', 'listar' o 'buscar'."
        )

    except ErrorMemoria as e:
        return str(e)

    except (OSError, IOError):
        return (
            "No he podido acceder "
            "a la memoria de tus notas."
        )

    except (KeyError, TypeError, AttributeError):
        return (
            "Los datos de las notas "
            "no tienen un formato válido."
        )

    except Exception:
        return (
            "Ha ocurrido un error inesperado "
            "al gestionar tus notas."
        )


# ==================================================
# RECORDATORIOS
# ==================================================

@tool
def crear_recordatorio(
    usuario_id: str,
    texto: str,
    momento: str
) -> str:
    """
    Crea un recordatorio persistente para un usuario.
    """

    try:
        if not usuario_id or not isinstance(usuario_id, str):
            return "No se ha proporcionado un usuario válido."

        if not texto or not isinstance(texto, str):
            return "Debes indicar el texto del recordatorio."

        if not texto.strip():
            return "Debes indicar el texto del recordatorio."

        if not momento or not isinstance(momento, str):
            return "Debes indicar cuándo quieres el recordatorio."

        if not momento.strip():
            return "Debes indicar cuándo quieres el recordatorio."

        memoria_usuario = cargar_memoria(
            usuario_id
        )

        memoria_usuario = preparar_memoria(
            memoria_usuario
        )

        recordatorio = {
            "id": str(uuid.uuid4()),
            "mensaje": texto.strip(),
            "tiempo": momento.strip(),
            "completado": False
        }

        memoria_usuario["recordatorios"].append(
            recordatorio
        )

        guardar_memoria(
            usuario_id,
            memoria_usuario
        )

        return (
            f"Recordatorio creado para "
            f"{momento.strip()}: {texto.strip()}"
        )

    except ErrorMemoria as e:
        return str(e)

    except (OSError, IOError):
        return "No he podido guardar el recordatorio."

    except (KeyError, TypeError, AttributeError):
        return (
            "Los datos del recordatorio "
            "no tienen un formato válido."
        )

    except Exception:
        return (
            "Ha ocurrido un error inesperado "
            "al crear el recordatorio."
        )


# ==================================================
# TOOLS DE ATLAS
# ==================================================

tools = [
    calculadora,
    consultar_clima,
    gestionar_notas,
    crear_recordatorio
]