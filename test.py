"""
Script para probar el chatbot localmente.
"""
import asyncio
import os
from langchain_core.messages import HumanMessage
from src.chains.intent_classifier import IntentClassifier
from src.core.database import Database
from src.graphs.main_graph import create_conversation_graph


async def test_conversation():
    """Ejecuta una conversación de prueba con el chatbot"""
    # Inicializar componentes
    intent_classifier = IntentClassifier()
    database = Database()
    await database.connect()

    # Obtener información del negocio
    business_info = await database.load_business_info()

    # Crear grafo
    conversation_graph = create_conversation_graph()

    # Mensajes de prueba
    test_messages = [
        "Hola, me llamo Juan",
        "Quiero saber la dirección del local",
        "Tengo un problema con mi alarma",
        "El teclado touch",
        "Pitido continuo",
        "5"  # Calificación del servicio
    ]

    # Historial de mensajes para mantener contexto
    messages_history = []

    # Procesar cada mensaje
    for message in test_messages:
        print(f"\n🔹 USUARIO: {message}")

        # Clasificar intenciones
        intents = await intent_classifier.predict(message)
        print(f"🔍 Intenciones: {intents}")

        # Añadir mensaje al historial
        messages_history.append(HumanMessage(content=message))

        # Crear estado
        state = {
            "messages": messages_history.copy(),
            "user_data": {"first_name": "Usuario", "level": 2},
            "user_level": 2,
            "intents": intents,
            "context": "TEST",
            "business_info": business_info,
            "troubleshooting_active": False,
            "troubleshooting_state": None
        }

        # Procesar con el grafo
        result = conversation_graph.invoke(state)

        # Extraer respuesta
        if result["messages"] and len(result["messages"]) > len(messages_history):
            response = result["messages"][-1].content
            print(f"🤖 ASISTENTE: {response}")
            # Actualizar historial con todas las respuestas
            messages_history = result["messages"].copy()
        else:
            print("❌ No se generó respuesta")

    await database.close()

if __name__ == "__main__":
    asyncio.run(test_conversation())
