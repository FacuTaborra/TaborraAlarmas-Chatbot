import asyncmy
# Removed unnecessary import of asyncmy.cursors
from typing import Dict, Any, Optional, List, Tuple
from src.config.settings import settings
import json


class Database:
    def __init__(self):
        """Inicializa la clase de base de datos."""
        self.read_pool = None
        self.write_pool = None

    async def connect(self) -> Tuple[asyncmy.Pool, asyncmy.Pool]:
        """Establece los pools de conexión para lectura y escritura.

        Returns:
            Tupla con los pools de lectura y escritura
        """
        if not self.read_pool:
            self.read_pool = await asyncmy.create_pool(
                host=settings.DB_HOST,
                port=int(settings.DB_PORT),
                user=settings.DB_USER_READER,
                password=settings.DB_PASS_READER,
                database=settings.DB_NAME,
                autocommit=True,  # Para operaciones de solo lectura
                charset="utf8mb4",  # Añadir esta línea
                use_unicode=True   # Añadir esta línea
            )
        if not self.write_pool:
            # Para operaciones de escritura, desactivamos autocommit para manejar la transacción manualmente.
            self.write_pool = await asyncmy.create_pool(
                host=settings.DB_HOST,
                port=int(settings.DB_PORT),
                user=settings.DB_USER_WRITER,
                password=settings.DB_PASS_WRITER,
                database=settings.DB_NAME,
                autocommit=False,
                charset="utf8mb4",  # Añadir esta línea
                use_unicode=True    # Añadir esta línea
            )
        return self.read_pool, self.write_pool

    async def close(self) -> None:
        """Cierra ambos pools de conexión."""
        if self.read_pool:
            self.read_pool.close()
            await self.read_pool.wait_closed()
            self.read_pool = None
        if self.write_pool:
            self.write_pool.close()
            await self.write_pool.wait_closed()
            self.write_pool = None

    async def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Recupera un usuario usando el pool de lectura.

        Args:
            phone: Número de teléfono del usuario

        Returns:
            Datos del usuario o None si no existe
        """
        query = "SELECT id, first_name, last_name, phone, level FROM users WHERE phone = %s"
        # Asegurarse de que el pool se ha inicializado
        await self.connect()
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (phone,))
                    result = await cursor.fetchone()
                    return result
        except Exception as e:
            print("❌ Error en get_user_by_phone:", e)
            return None

    async def register_user(self, first_name: str, last_name: str, phone: str) -> bool:
        """Registra un nuevo usuario con nivel 1 utilizando una transacción.

        Args:
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            phone: Número de teléfono

        Returns:
            True si se registró correctamente
        """
        await self.connect()
        query = """
        INSERT INTO users (first_name, last_name, phone, level)
        VALUES (%s, %s, %s, 1)
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (first_name, last_name, phone))
                    await cursor.execute("SELECT LAST_INSERT_ID()")
                    user_id = (await cursor.fetchone())[0]
                    await conn.commit()
                    return user_id
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al registrar usuario: {e}")
                    return False

    async def update_user_level(self, phone: str, new_level: int) -> bool:
        """Actualiza el nivel de un usuario utilizando una transacción.

        Args:
            phone: Número de teléfono del usuario
            new_level: Nuevo nivel de acceso

        Returns:
            True si se actualizó correctamente
        """
        await self.connect()
        query = "UPDATE users SET level = %s WHERE phone = %s"
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (new_level, phone))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al actualizar nivel de usuario: {e}")
                    return False

    async def save_message(self, user_id: int, message: str) -> bool:
        """Guarda un mensaje en la BD utilizando una transacción.

        Args:
            user_id: ID del usuario
            message: Texto del mensaje

        Returns:
            True si se guardó correctamente
        """
        await self.connect()
        query = """
        INSERT INTO messages (user_id, message, timestamp)
        VALUES (%s, %s, NOW())
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (user_id, message))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al guardar mensaje: {e}")
                    return False

    async def get_message_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera los últimos mensajes de un usuario usando el pool de lectura.

        Args:
            user_id: ID del usuario
            limit: Número máximo de mensajes a recuperar

        Returns:
            Lista de mensajes
        """
        await self.connect()
        query = """
        SELECT message, timestamp FROM messages
        WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s
        """
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (user_id, limit))
                    return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener historial de mensajes: {e}")
            return []

    async def load_business_info(self) -> Dict[str, Any]:
        """Carga información del negocio de la base de datos.

        Returns:
            Información del negocio
        """
        await self.connect()
        query = "SELECT * FROM business_info LIMIT 1"
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query)
                    result = await cursor.fetchone()
                    if result:
                        print("✅ Información del negocio cargada correctamente")
                        return result
                    else:
                        print("⚠️ No se encontró información del negocio en la BD")
                        return {}
        except Exception as e:
            print(f"❌ Error al cargar información del negocio: {e}")
            return {}

    async def save_rating(self, user_id: int, rating: int, keyboard_type: str, problem_type: str) -> bool:
        """Guarda una calificación de solución en la BD.

        Args:
            user_id: ID o teléfono del usuario
            rating: Calificación (1-5)
            keyboard_type: Tipo de teclado
            problem_type: Tipo de problema

        Returns:
            True si se guardó correctamente
        """
        await self.connect()
        query = """
        INSERT INTO ratings (user_id, rating, keyboard_type, problem_type, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (user_id, rating, keyboard_type, problem_type))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al guardar calificación: {e}")
                    return False

    async def create_conversation(self, user_id: int, chat_id: str) -> Optional[int]:
        """
        Crea una nueva conversación en la base de datos.

        Args:
            user_id: ID del usuario
            chat_id: ID del chat (generado por Redis)

        Returns:
            ID de la conversación creada o None si hay error
        """
        await self.connect()
        query = """
        INSERT INTO conversations (user_id, chat_id, started_at, active)
        VALUES (%s, %s, NOW(), TRUE)
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (user_id, chat_id))
                    await cursor.execute("SELECT LAST_INSERT_ID()")
                    conversation_id = (await cursor.fetchone())[0]
                    await conn.commit()
                    return conversation_id
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al crear conversación: {e}")
                    return None

    async def find_active_conversation(self, user_id: int, chat_id: str) -> Optional[int]:
        """
        Busca una conversación activa para un usuario y chat_id específicos.

        Args:
            user_id: ID del usuario
            chat_id: ID del chat

        Returns:
            ID de la conversación activa o None si no existe
        """
        await self.connect()
        query = """
        SELECT id FROM conversations 
        WHERE user_id = %s AND chat_id = %s AND active = TRUE
        LIMIT 1
        """
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (user_id, chat_id))
                    result = await cursor.fetchone()
                    return result[0] if result else None
        except Exception as e:
            print(f"❌ Error al buscar conversación activa: {e}")
            return None

    async def close_conversation(self, conversation_id: int) -> bool:
        """
        Cierra una conversación marcándola como inactiva.

        Args:
            conversation_id: ID de la conversación

        Returns:
            True si se cerró correctamente
        """
        await self.connect()
        query = """
        UPDATE conversations 
        SET active = FALSE, ended_at = NOW() 
        WHERE id = %s
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (conversation_id,))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al cerrar conversación: {e}")
                    return False

    async def save_conversation_message(self, conversation_id: int, role: str, content: str) -> bool:
        """
        Guarda un mensaje de conversación en la BD.

        Args:
            conversation_id: ID de la conversación
            role: Rol ('user' o 'assistant')
            content: Contenido del mensaje

        Returns:
            True si se guardó correctamente
        """
        await self.connect()
        query = """
        INSERT INTO conversation_messages (conversation_id, role, content, timestamp)
        VALUES (%s, %s, %s, NOW())
        """
        async with self.write_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, (conversation_id, role, content))
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    print(f"❌ Error al guardar mensaje de conversación: {e}")
                    return False

    async def get_conversation_messages(self, conversation_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Recupera los mensajes de una conversación.

        Args:
            conversation_id: ID de la conversación
            limit: Número máximo de mensajes a recuperar

        Returns:
            Lista de mensajes
        """
        await self.connect()
        query = """
        SELECT id, role, content, timestamp 
        FROM conversation_messages
        WHERE conversation_id = %s 
        ORDER BY timestamp ASC 
        LIMIT %s
        """
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (conversation_id, limit))
                    return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener mensajes de conversación: {e}")
            return []

    async def get_user_conversations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera las conversaciones de un usuario.

        Args:
            user_id: ID del usuario
            limit: Número máximo de conversaciones a recuperar

        Returns:
            Lista de conversaciones
        """
        await self.connect()
        query = """
        SELECT id, chat_id, started_at, ended_at, active 
        FROM conversations
        WHERE user_id = %s 
        ORDER BY started_at DESC 
        LIMIT %s
        """
        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (user_id, limit))
                    return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener conversaciones del usuario: {e}")
            return []

    # Añadir a src/core/database.py

    # En src/core/database.py

    async def get_home_assistant_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de Home Assistant para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Configuración de Home Assistant o None si no existe
        """
        await self.connect()
        query = """
        SELECT webhook_url, token, available_methods 
        FROM home_assistant_config 
        WHERE user_id = %s
        """

        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (user_id,))
                    result = await cursor.fetchone()

                    if result and "available_methods" in result and result["available_methods"]:
                        # Convertir JSON a dict
                        try:
                            if isinstance(result["available_methods"], str):
                                result["available_methods"] = json.loads(
                                    result["available_methods"])
                        except Exception as e:
                            print(
                                f"❌ Error al parsear available_methods: {result['available_methods']}. Detalle del error: {e}")
                            result["available_methods"] = {}

                    return result
        except Exception as e:
            print(f"❌ Error al obtener configuración de Home Assistant: {e}")
            return None

    async def get_home_assistant_methods(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene solo los métodos disponibles de Home Assistant para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con los métodos disponibles o diccionario vacío si no hay
        """
        await self.connect()
        query = """
        SELECT available_methods 
        FROM home_assistant_config 
        WHERE user_id = %s
        """

        try:
            async with self.read_pool.acquire() as conn:
                async with conn.cursor(asyncmy.cursors.DictCursor) as cursor:
                    await cursor.execute(query, (user_id,))
                    result = await cursor.fetchone()

                    if result and "available_methods" in result and result["available_methods"]:
                        # Convertir JSON a dict
                        try:
                            if isinstance(result["available_methods"], str):
                                return json.loads(result["available_methods"])
                            return result["available_methods"]
                        except Exception as e:
                            print(f"❌ Error al parsear available_methods: {e}")
                            return {}

                    return {}
        except Exception as e:
            print(f"❌ Error al obtener métodos de Home Assistant: {e}")
            return {}
