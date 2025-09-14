"""
Chatbot mejorado con LangChain para SugarBI
Integra procesamiento de lenguaje natural avanzado con el data mart
"""

import os
from typing import Dict, List, Any, Optional
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain.memory import ConversationBufferMemory
import json

class SugarBIOutputParser(BaseOutputParser):
    """Parser personalizado para respuestas de SugarBI"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parsea la respuesta del LLM a un formato estructurado"""
        try:
            # Intentar parsear como JSON
            return json.loads(text)
        except:
            # Si no es JSON válido, crear estructura básica
            return {
                "query_type": "basic",
                "metric": "toneladas",
                "dimension": "finca",
                "limit": 10,
                "filters": {},
                "explanation": text
            }

class LangChainChatbot:
    """Chatbot mejorado con LangChain para SugarBI"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.memory = ConversationBufferMemory()
        
        # Template para el prompt
        self.prompt_template = PromptTemplate(
            input_variables=["query", "context", "history"],
            template="""
Eres un asistente especializado en Business Intelligence para la industria de la caña de azúcar.

CONTEXTO DEL DATA MART:
- Tabla principal: hechos_cosecha (métricas de cosecha)
- Dimensiones: dimfinca (fincas), dimvariedad (variedades), dimzona (zonas), dimtiempo (tiempo)
- Métricas disponibles: toneladas_cana_molida, tch, brix, sacarosa, area_cosechada, rendimiento_teorico

HISTORIAL DE CONVERSACIÓN:
{history}

CONSULTA ACTUAL: {query}

CONTEXTO ADICIONAL: {context}

INSTRUCCIONES:
1. Analiza la consulta del usuario
2. Identifica el tipo de consulta (top_ranking, statistics, comparison, trend, basic)
3. Determina la métrica principal (toneladas, tch, brix, sacarosa, area, rendimiento)
4. Identifica la dimensión (finca, variedad, zona, tiempo)
5. Extrae filtros temporales si los hay
6. Determina el límite de resultados

Responde en formato JSON:
{{
    "query_type": "tipo_de_consulta",
    "metric": "métrica_principal",
    "dimension": "dimensión_principal",
    "limit": número_o_null,
    "filters": {{"año": 2025, "mes": 1}},
    "explanation": "explicación_en_español_de_lo_que_entendiste"
}}

Si no puedes determinar algún valor, usa valores por defecto apropiados.
"""
        )
        
        # Inicializar LLM si hay API key
        if self.openai_api_key:
            self.llm = OpenAI(api_key=self.openai_api_key, temperature=0.1)
            self.chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt_template,
                memory=self.memory,
                output_parser=SugarBIOutputParser()
            )
        else:
            self.llm = None
            self.chain = None
    
    def process_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Procesa una consulta usando LangChain
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Dict con la intención parseada
        """
        if not self.chain:
            # Fallback al parser original si no hay LangChain
            from .query_parser import QueryParser
            parser = QueryParser()
            intent = parser.parse(query)
            return {
                "query_type": intent.query_type.value,
                "metric": intent.metric.value,
                "dimension": intent.dimension.value,
                "limit": intent.limit,
                "filters": intent.filters,
                "explanation": f"Consulta procesada: {query}"
            }
        
        try:
            # Obtener historial de conversación
            history = self.memory.chat_memory.messages[-5:] if self.memory.chat_memory.messages else []
            history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in history])
            
            # Procesar con LangChain
            result = self.chain.run(
                query=query,
                context=context,
                history=history_text
            )
            
            return result
            
        except Exception as e:
            # Fallback al parser original en caso de error
            from .query_parser import QueryParser
            parser = QueryParser()
            intent = parser.parse(query)
            return {
                "query_type": intent.query_type.value,
                "metric": intent.metric.value,
                "dimension": intent.dimension.value,
                "limit": intent.limit,
                "filters": intent.filters,
                "explanation": f"Consulta procesada (fallback): {query}"
            }
    
    def generate_response(self, query: str, data: List[Dict], sql: str) -> str:
        """
        Genera una respuesta natural basada en los datos
        
        Args:
            query: Consulta original
            data: Datos obtenidos
            sql: Query SQL ejecutado
            
        Returns:
            Respuesta en lenguaje natural
        """
        if not self.llm:
            return f"Se encontraron {len(data)} registros para tu consulta."
        
        response_template = PromptTemplate(
            input_variables=["query", "data", "sql", "count"],
            template="""
Consulta: {query}
Registros encontrados: {count}
SQL ejecutado: {sql}
Datos: {data}

Genera una respuesta natural y útil en español explicando los resultados encontrados.
Incluye insights relevantes sobre los datos.
"""
        )
        
        try:
            response_chain = LLMChain(llm=self.llm, prompt=response_template)
            response = response_chain.run(
                query=query,
                data=json.dumps(data[:5], indent=2),  # Solo primeros 5 registros
                sql=sql,
                count=len(data)
            )
            return response
        except:
            return f"Se encontraron {len(data)} registros para tu consulta."

# Instancia global del chatbot
langchain_chatbot = LangChainChatbot()
