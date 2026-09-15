import json
import re

from datetime import datetime

from .config import RUTA_MEMORIA
from .errors import ErrorMemoria


def cargar_memoria(usuario_id: str) -> dict:
    if not RUTA_MEMORIA.exists():
        return {}

    try:
        with open(
            RUTA_MEMORIA,
            "r",
            encoding="utf-8"
        ) as archivo:
            memoria = json.load(archivo)

        return memoria.get(usuario_id, {})

    except json.JSONDecodeError as e:
        raise ErrorMemoria(
            "El archivo de memoria contiene datos inválidos."
        ) from e

    except OSError as e:
        raise ErrorMemoria(
            "No se ha podido acceder al archivo de memoria."
        ) from e


def preparar_memoria(memoria: dict) -> dict:
    memoria.setdefault("nombre", "")
    memoria.setdefault("ciudad_favorita", "")
    memoria.setdefault("preferencias", [])
    memoria.setdefault("notas", [])
    memoria.setdefault("recordatorios", [])

    if not isinstance(memoria.get("tools_usadas"), dict):
        memoria["tools_usadas"] = {
            "calculadora": 0,
            "clima": 0,
            "notas": 0,
            "recordatorios": 0
        }

    memoria.setdefault("total_sesiones", 0)
    memoria.setdefault("ultima_sesion", "")

    return memoria


def guardar_memoria(
    usuario_id: str,
    memoria_usuario: dict
):
    memoria = {}

    if RUTA_MEMORIA.exists():
        try:
            with open(
                RUTA_MEMORIA,
                "r",
                encoding="utf-8"
            ) as archivo:
                memoria = json.load(archivo)

        except json.JSONDecodeError as e:
            raise ErrorMemoria(
                "El archivo de memoria contiene datos inválidos."
            ) from e

        except OSError as e:
            raise ErrorMemoria(
                "No se ha podido leer el archivo de memoria."
            ) from e

    memoria[usuario_id] = memoria_usuario

    try:
        with open(
            RUTA_MEMORIA,
            "w",
            encoding="utf-8"
        ) as archivo:
            json.dump(
                memoria,
                archivo,
                ensure_ascii=False,
                indent=4
            )

    except OSError as e:
        raise ErrorMemoria(
            "No se ha podido guardar la memoria."
        ) from e


def extraer_datos_usuario(
    mensaje: str,
    memoria_usuario: dict
):
    """
    Extrae información personal sencilla del mensaje del usuario.
    """

    coincidencia_nombre = re.search(
        r"\bme llamo\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)",
        mensaje,
        re.IGNORECASE
    )

    if coincidencia_nombre:
        memoria_usuario["nombre"] = (
            coincidencia_nombre.group(1)
        )

    coincidencia_ciudad = re.search(
        r"\bmi ciudad favorita es\s+([A-Za-zÁÉÍÓÚáéíóúÑñ\s]+)",
        mensaje,
        re.IGNORECASE
    )

    if coincidencia_ciudad:
        memoria_usuario["ciudad_favorita"] = (
            coincidencia_ciudad.group(1).strip()
        )

    return memoria_usuario