from .graph import graph


# ==================================================
# EJECUCIÓN
# ==================================================

def ejecutar_atlas(
    usuario_id: str,
    mensaje: str
):
    return graph.invoke({
        "usuario_id": usuario_id,
        "mensaje_actual": mensaje,
        "historial": [],
        "memoria_usuario": {},
        "contexto_mlp": "",
        "tool_calls_pendientes": [],
        "tool_results": [],
        "respuesta_final": "",
        "iteraciones": 0,
        "error": ""
    })


def modo_interactivo():
    print("\n========================================")
    print("        ATLAS - ASISTENTE PERSONAL")
    print("========================================")

    usuario_id = input(
        "\nIntroduce tu ID de usuario: "
    ).strip()

    if not usuario_id:
        usuario_id = "usuario_prueba"

    print(
        "\nEscribe 'salir' para terminar.\n"
    )

    while True:
        try:
            mensaje = input("Tú: ").strip()

            if not mensaje:
                continue

            if mensaje.lower() in (
                "salir",
                "exit",
                "quit"
            ):
                print("\nHasta luego.")
                break

            resultado = ejecutar_atlas(
                usuario_id,
                mensaje
            )

            print(
                f"Atlas: "
                f"{resultado['respuesta_final']}\n"
            )

        except KeyboardInterrupt:
            print("\n\nHasta luego.")
            break

        except EOFError:
            print("\n\nHasta luego.")
            break

        except Exception:
            print(
                "Atlas: Ha ocurrido un error inesperado "
                "al procesar tu solicitud.\n"
            )