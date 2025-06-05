from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from src.config.settings import settings


class ConversationalAI:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.llm = ChatOpenAI(
            model=model_name or settings.MODEL_NAME,
            temperature=0.7,
            openai_api_key=api_key or settings.OPENAI_API_KEY,
        )

    def generate(self, history: List[BaseMessage], business_info: Dict[str, Any]) -> str:
        """Genera una respuesta usando el historial de la conversación."""
        system_text = (
            "Eres el asistente virtual de Taborra Alarmas SRL. "
            "Utiliza la siguiente información del negocio en tus respuestas cuando sea relevante: "
            f"{business_info}. Responde siempre en español."
        )
        messages = [SystemMessage(content=system_text)] + history
        response = self.llm.invoke(messages)
        return response.content
