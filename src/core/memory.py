from typing import Dict, Any, List
import redis.asyncio as redis
import json
import uuid
from src.config.settings import settings


class RedisManager:
    def __init__(self: str):
        """
        Inicializa el gestor de memoria con Redis.

        Args:
            redis_url: URL de conexión a Redis
        """
        self.redis_url = settings.REDIS_URL
        self.redis_client = redis.from_url(
            self.redis_url, decode_responses=True)

    async def set_value(self, key: str, value: Any, expiry: int = 3600) -> bool:
        """
        Guarda un valor en Redis con expiración.

        Args:
            key: Clave para almacenar
            value: Valor a guardar
            expiry: Tiempo de expiración en segundos

        Returns:
            True si se guardó correctamente
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        try:
            await self.redis_client.set(key, value, ex=expiry)
            return True
        except Exception as e:
            print(f"❌ Error al guardar en Redis: {e}")
            return False

    async def get_value(self, key: str) -> Any:
        """
        Obtiene un valor de Redis.

        Args:
            key: Clave a buscar

        Returns:
            Valor almacenado o None si no existe
        """
        try:
            value = await self.redis_client.get(key)

            if value:
                try:
                    # Intentar deserializar como JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Devolver como string si no es JSON
                    return value

            return None
        except Exception as e:
            print(f"❌ Error al obtener valor de Redis: {e}")
            return None

    async def delete_key(self, key: str) -> bool:
        """
        Elimina una clave de Redis.

        Args:
            key: Clave a eliminar

        Returns:
            True si se eliminó correctamente
        """
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error al eliminar clave de Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Verifica si una clave existe en Redis.

        Args:
            key: Clave a verificar

        Returns:
            True si la clave existe
        """
        try:
            return await self.redis_client.exists(key)
        except Exception as e:
            print(f"❌ Error al verificar existencia en Redis: {e}")
            return False

    async def update_expiry(self, key: str, seconds: int = 3600) -> bool:
        """
        Actualiza el tiempo de expiración de una clave.

        Args:
            key: Clave a actualizar
            seconds: Nuevos segundos de expiración

        Returns:
            True si se actualizó correctamente
        """
        try:
            await self.redis_client.expire(key, seconds)
            return True
        except Exception as e:
            print(f"❌ Error al actualizar expiración en Redis: {e}")
            return False

    async def get_or_create_chat_id(self, user_id: str) -> str:
        """
        Obtiene o crea un ID de chat para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            ID del chat actual
        """
        if not user_id:
            return str(uuid.uuid4())

        chat_key = f"taborra:user:{user_id}:current_chat"
        chat_id = await self.get_value(chat_key)

        if not chat_id:
            chat_id = str(uuid.uuid4())
            await self.set_value(chat_key, chat_id, 86400)  # 1 día

        return chat_id

    async def save_message_id(self, message_id: str, expiry: int = 86400) -> bool:
        """
        Guarda un ID de mensaje para evitar duplicados.

        Args:
            message_id: ID del mensaje
            expiry: Tiempo de expiración en segundos

        Returns:
            True si se guardó correctamente
        """
        key = f"message:{message_id}"
        return await self.set_value(key, "1", expiry)

    async def get_message_history(self, chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de mensajes de un chat.

        Args:
            chat_id: ID del chat
            limit: Número máximo de mensajes a obtener

        Returns:
            Lista de mensajes
        """
        key = f"taborra:chat:{chat_id}:messages"
        try:
            messages = await self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(msg) for msg in messages if msg]
        except Exception as e:
            print(f"❌ Error al obtener historial de mensajes: {e}")
            return []

    async def add_message_to_history(self, chat_id: str, role: str, content: str) -> bool:
        """
        Añade un mensaje al historial de un chat.

        Args:
            chat_id: ID del chat
            role: Rol del mensaje ('user' o 'assistant')
            content: Contenido del mensaje

        Returns:
            True si se añadió correctamente
        """
        key = f"taborra:chat:{chat_id}:messages"
        message = json.dumps({"role": role, "content": content})

        try:
            # Añadir al inicio de la lista (más reciente primero)
            await self.redis_client.lpush(key, message)
            # Limitar el tamaño del historial
            # Mantener últimos 50 mensajes
            await self.redis_client.ltrim(key, 0, 49)
            # Establecer expiración
            await self.redis_client.expire(key, 86400 * 7)  # 7 días
            return True
        except Exception as e:
            print(f"❌ Error al añadir mensaje al historial: {e}")
            return False
