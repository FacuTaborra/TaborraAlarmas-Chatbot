from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class UserData(BaseModel):
    """Modelo para los datos de usuario."""
    id: Optional[int] = None
    first_name: str
    last_name: str = ""
    phone: str
    level: int = 1


class BusinessInfo(BaseModel):
    """Modelo para la información del negocio."""
    direccion: str = ""
    horario: str = ""
    email: str = ""
    telefono: str = ""
    whatsapp: str = ""
    whatsapp_servicio_tecnico: str = ""
    whatsapp_ventas: str = ""
    whatsapp_administracion: str = ""
    whatsapp_cobranza: str = ""
    telefono_security: str = ""


class TroubleshootingState(TypedDict):
    """Estado para el grafo de resolución de problemas."""
    messages: List[BaseMessage]
    current_step: int
    keyboard_type: Optional[str]
    problem_type: Optional[str]
    solutions_shown: List[str]
    rating: Optional[int]
    business_info: Dict[str, Any]


class ConversationState(TypedDict):
    """Estado para el grafo principal de conversación."""
    messages: List[BaseMessage]
    user_data: Dict[str, Any]
    user_level: int
    intents: List[str]
    context: str
    business_info: Dict[str, Any]
    troubleshooting_active: bool
    troubleshooting_state: Optional[Dict[str, Any]]


class KeyboardProblem(BaseModel):
    """Modelo para los problemas de un teclado."""
    title: str
    solution: str
    video_url: Optional[str] = None


class KeyboardType(BaseModel):
    """Modelo para los tipos de teclado."""
    name: str
    image_url: str
    problems: Dict[str, KeyboardProblem]
    direct_support: bool = False
    support_message: Optional[str] = None


class HomeAssistantConfig(BaseModel):
    """Modelo para configuración de Home Assistant por usuario"""
    id: Optional[int] = None
    user_id: int
    webhook_url: Optional[str] = None
    webhook_token: Optional[str] = None
    token_generated_at: Optional[datetime] = None
    is_verified: bool = False
