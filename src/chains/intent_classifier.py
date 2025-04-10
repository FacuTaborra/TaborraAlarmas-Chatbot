# src/chains/intent_classifier.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict, Any
from src.config.settings import settings
from src.template import prompts


class IntentClassifier:
    def __init__(self, api_key: str = None, model_name: str = None, ha_methods: Dict[str, Any] = None):
        """
        Inicializa el clasificador de intenciones usando LangChain

        Args:
            api_key: API key para OpenAI (opcional, se puede usar desde settings)
            model_name: Modelo a utilizar (opcional, se puede usar desde settings)
            ha_methods: Métodos de Home Assistant disponibles (opcional)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.MODEL_NAME
        self.ha_methods = ha_methods or {}

        # Verificar que tenemos una API key
        if not self.api_key:
            raise ValueError("No se ha proporcionado una API key para OpenAI")

        # Crear el modelo
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0,
            openai_api_key=self.api_key
        )

        # Generar la lista de intenciones de Home Assistant
        intents_ha_text = ""
        if self.ha_methods:
            intents_ha_lines = []
            for method_name, method_info in self.ha_methods.items():
                description = method_info.get('description', "")
                intents_ha_lines.append(f"- {method_name}: {description}")
            intents_ha_text = "\n".join(intents_ha_lines)

        # Crear el template completo con las intenciones de HA ya incluidas
        template_text = prompts.INTENT_CLASSIFIER_BASE_TEMPLATE
        if intents_ha_text:
            ha_section = f"\nIntenciones de Home Assistant:\n{intents_ha_text}\n"
            # Insertar la sección antes de la parte "Mensaje del usuario"
            template_parts = template_text.split("Mensaje del usuario:")
            template_text = template_parts[0] + ha_section + \
                "Mensaje del usuario:" + template_parts[1]

        # Crear el prompt con el texto de template modificado
        self.prompt = ChatPromptTemplate.from_template(template_text)

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
