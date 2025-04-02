# src/chains/intent_classifier.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List
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

        # Definir el prompt para clasificación
        self.prompt_template = prompts.INTENT_CLASSIFIER_TEMPLATE

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
