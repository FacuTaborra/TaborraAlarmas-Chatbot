# src/chains/intent_classifier.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict, Any
import os
from src.config.settings import settings
from src.template import prompts


class IntentClassifier:
    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Inicializa el clasificador de intenciones usando LangChain

        Args:
            api_key: API key para OpenAI (opcional, se puede usar desde settings)
            model_name: Modelo a utilizar (opcional, se puede usar desde settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.MODEL_NAME

        # Verificar que tenemos una API key
        if not self.api_key:
            raise ValueError("No se ha proporcionado una API key para OpenAI")

        # Crear el modelo y el prompt
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0,
            openai_api_key=self.api_key
        )

        # Definir el prompt para clasificación (si no estás usando el de templates)
        self.prompt_template = """
        Eres un asistente especializado en detectar intenciones en mensajes.
        A continuación, se te dará un mensaje del usuario y deberás identificar todas las intenciones presentes.

        Las posibles intenciones son:
        - estado_alarma: Si pregunta por el estado de la alarma o cómo está la alarma
        - escaneo_camaras: Si quiere ver las cámaras o detectar movimiento
        - direccion: Si pregunta dónde está ubicada la empresa o cómo llegar
        - horario: Si pregunta por los horarios de atención
        - email: Si solicita un correo electrónico de contacto
        - telefono: Si pide un número de teléfono para llamar
        - security: Si quiere contactar con el servicio de seguridad (Security 24)
        - whatsapp: Si pide un número de WhatsApp general
        - whatsapp_servicio_tecnico: Si quiere contactar al servicio técnico
        - whatsapp_ventas: Si quiere contactar con ventas
        - whatsapp_administracion: Si quiere contactar con administración
        - whatsapp_cobranza: Si quiere contactar con cobranzas o pagar
        - saludo: Si está saludando
        - despedida: Si se está despidiendo
        - problema_alarma: Si indica que tiene un problema con su alarma
        - control_alarma: Si intenta controlar la alarma (encender, apagar, etc.)

        Mensaje del usuario: {text}

        Devuelve solo las intenciones detectadas, separadas por comas. Si no detectas ninguna, devuelve "ninguna".
        """

        # Crear el ChatPromptTemplate a partir del template de texto
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)

        # O usar directamente el importado (elige uno de los dos enfoques)
        # self.prompt = prompts.intent_classifier_prompt

        # Crear la cadena
        self.chain = self.prompt | self.llm

    async def predict(self, text: str) -> List[str]:
        """
        Predice las intenciones en un texto

        Args:
            text: Texto del usuario a clasificar

        Returns:
            Lista de intenciones detectadas
        """
        try:
            # Invocar el modelo
            response = await self.chain.ainvoke({"text": text})

            # Procesar la respuesta
            if not response.content or response.content.lower() == "ninguna":
                return []

            # Dividir por comas y limpiar espacios
            intents = [intent.strip().lower()
                       for intent in response.content.split(",")]

            # Filtrar intenciones vacías
            return [intent for intent in intents if intent]

        except Exception as e:
            print(f"❌ Error al clasificar intenciones: {e}")
            # En caso de error, devolver una lista vacía
            return []
