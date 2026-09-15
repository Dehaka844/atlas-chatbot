from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# ==================================================
# CONFIGURACIÓN
# ==================================================

load_dotenv()


RUTA_MEMORIA = Path("memoria.json")

MAX_ITERACIONES = 5


llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0
)