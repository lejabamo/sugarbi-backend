"""
Módulo de Chatbot para SugarBI
Incluye agente SQL con LangChain para consultas inteligentes
"""

from .sql_agent import SugarBISQLAgent, SQLQueryOutputParser

__all__ = ['SugarBISQLAgent', 'SQLQueryOutputParser']
