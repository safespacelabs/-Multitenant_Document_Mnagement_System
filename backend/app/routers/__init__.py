# Routers package initialization
from . import auth
from . import companies
from . import users
from . import documents
from . import chatbot
from . import user_management
from . import esignature
from . import ai_assistant
from . import hr_admin

__all__ = [
    'auth',
    'companies', 
    'users',
    'documents',
    'chatbot',
    'user_management',
    'esignature',
    'ai_assistant',
    'hr_admin'
] 