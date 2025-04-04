import asyncmy
# Removed unnecessary import of asyncmy.cursors
from typing import Dict, Any, Optional, List, Tuple
from src.config.settings import settings


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
                autocommit=True  # Para operaciones de solo lectura
            )
        if not self.write_pool:
            # Para operaciones de escritura, desactivamos autocommit para manejar la transacción manualmente.
            self.write_pool = await asyncmy.create_pool(
                host=settings.DB_HOST,
                port=int(settings.DB_PORT),
                user=settings.DB_USER_WRITER,
                password=settings.DB_PASS_WRITER,
                database=settings.DB_NAME,
                autocommit=False
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
