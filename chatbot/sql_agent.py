"""
Módulo para el agente SQL con LangChain
Convierte consultas en lenguaje natural a SQL y ejecuta consultas en la base de datos
"""

import os
from typing import Dict, Any, List, Optional
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_core.output_parsers import StrOutputParser
from .universal_query_analyzer import UniversalQueryAnalyzer, UniversalSQLGenerator
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import json

class SQLQueryOutputParser(BaseOutputParser):
    """Parser personalizado para extraer solo la query SQL del output del modelo"""
    
    def parse(self, text: str) -> str:
        """Extrae solo la query SQL del texto de respuesta"""
        # Buscar patrones comunes de SQL en el texto
        import re
        
        # Patrón para encontrar SELECT statements
        sql_pattern = r'(SELECT\s+.*?;?)'
        matches = re.findall(sql_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if matches:
            # Retornar la primera query encontrada, limpiando espacios extra
            query = matches[0].strip()
            # Asegurar que termine con punto y coma
            if not query.endswith(';'):
                query += ';'
            return query
        
        # Si no encuentra patrón SQL, retornar el texto original
        return text.strip()

class SugarBISQLAgent:
    """Agente SQL especializado para SugarBI con LangChain"""
    
    def __init__(self, database_url: str, openai_api_key: Optional[str] = None):
        """
        Inicializa el agente SQL
        
        Args:
            database_url: URL de conexión a la base de datos MySQL
            openai_api_key: Clave API de OpenAI (opcional, puede usar variable de entorno)
        """
        self.database_url = database_url
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Inicializar componentes
        self.db = None
        self.llm = None
        self.agent = None
        self.query_chain = None
        self.query_analyzer = UniversalQueryAnalyzer()
        self.sql_generator = UniversalSQLGenerator()
        
        self._setup_database()
        self._setup_llm()
        self._setup_agent()
        self._setup_query_chain()
    
    def _setup_database(self):
        """Configura la conexión a la base de datos"""
        try:
            self.db = SQLDatabase.from_uri(self.database_url)
            print("✅ Conexión a base de datos establecida")
        except Exception as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            raise
    
    def _setup_llm(self):
        """Configura el modelo de lenguaje"""
        try:
            if self.openai_api_key:
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0,
                    openai_api_key=self.openai_api_key
                )
                print("✅ Modelo OpenAI configurado")
            else:
                # Usar un modelo simple que genera SQL básico
                from langchain_community.llms import FakeListLLM
                self.llm = FakeListLLM(responses=["SELECT * FROM hechos_cosecha LIMIT 10;"])
                print("⚠️ Usando modelo de fallback - generando SQL básico")
        except Exception as e:
            print(f"❌ Error configurando el modelo: {e}")
            # Fallback a un modelo simple
            from langchain_community.llms import FakeListLLM
            self.llm = FakeListLLM(responses=["SELECT * FROM hechos_cosecha LIMIT 10;"])
            print("⚠️ Usando modelo de prueba")
    
    def _setup_agent(self):
        """Configura el agente SQL principal"""
        try:
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True
            )
            print("✅ Agente SQL configurado")
        except Exception as e:
            print(f"❌ Error configurando agente: {e}")
            self.agent = None
    
    def _setup_query_chain(self):
        """Configura la cadena de generación de queries SQL"""
        try:
            # Template para generar queries SQL
            sql_template = """
            Eres un experto en SQL y análisis de datos de cosecha de caña de azúcar.
            
            Base de datos: {database_info}
            
            Instrucciones:
            1. Genera SOLO la query SQL necesaria para responder la pregunta
            2. NO incluyas explicaciones, comentarios o texto adicional
            3. Usa los nombres exactos de las tablas y columnas
            4. Asegúrate de que la query sea válida para MySQL
            
            Pregunta del usuario: {question}
            
            Query SQL:
            """
            
            prompt = ChatPromptTemplate.from_template(sql_template)
            
            # Parser para extraer solo la query SQL
            output_parser = SQLQueryOutputParser()
            
            # Crear la cadena
            self.query_chain = (
                {"database_info": lambda x: self._get_database_info(), "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | output_parser
            )
            
            print("✅ Cadena de generación de queries configurada")
        except Exception as e:
            print(f"❌ Error configurando cadena de queries: {e}")
            self.query_chain = None
    
    def _get_database_info(self) -> str:
        """Obtiene información del esquema de la base de datos"""
        try:
            # Obtener información de las tablas principales
            tables_info = []
            
            # Tabla de hechos
            tables_info.append("""
            Tabla: hechos_cosecha (tabla principal de hechos)
            - id_finca: ID de la finca
            - codigo_variedad: Código de la variedad
            - codigo_zona: Código de la zona
            - codigo_tiempo: Código del tiempo
            - toneladas_cana_molida: Toneladas de caña molida
            - tch: Toneladas de caña por hectárea
            - brix: Grados Brix (contenido de azúcar)
            - sacarosa: Porcentaje de sacarosa
            - rendimiento_teorico: Rendimiento teórico
            """)
            
            # Tablas de dimensiones
            tables_info.append("""
            Tabla: dimfinca (dimension finca)
            - finca_id: ID de la finca
            - nombre_finca: Nombre de la finca
            - ubicacion: Ubicación de la finca
            """)
            
            tables_info.append("""
            Tabla: dimvariedad (dimension variedad)
            - variedad_id: ID de la variedad
            - nombre_variedad: Nombre de la variedad
            - descripcion: Descripción de la variedad
            """)
            
            tables_info.append("""
            Tabla: dimzona (dimension zona)
            - codigo_zona: Código de la zona
            - nombre_zona: Nombre de la zona
            - tipo_suelo: Tipo de suelo
            """)
            
            tables_info.append("""
            Tabla: dimtiempo (dimension tiempo)
            - tiempo_id: ID del tiempo
            - anio: Año
            - mes: Mes
            - trimestre: Trimestre
            - estacion: Estación del año
            """)
            
            return "\n".join(tables_info)
        except Exception as e:
            print(f"Error obteniendo información de la base de datos: {e}")
            return "Información de base de datos no disponible"
    
    def generate_sql_query(self, question: str) -> str:
        """
        Genera una query SQL a partir de una pregunta en lenguaje natural
        
        Args:
            question: Pregunta en lenguaje natural
            
        Returns:
            Query SQL generada
        """
        try:
            # Análisis de patrones para generar SQL más específico
            question_lower = question.lower()
            
            # Patrones para consultas específicas
            if "top" in question_lower or "mejor" in question_lower or "ranking" in question_lower:
                if "variedad" in question_lower and "tch" in question_lower:
                    return """
                    SELECT 
                        v.nombre_variedad,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
                    GROUP BY v.nombre_variedad
                    ORDER BY promedio_tch DESC
                    LIMIT 5
                    """
                elif "finca" in question_lower and ("produccion" in question_lower or "toneladas" in question_lower):
                    return """
                    SELECT 
                        f.nombre_finca,
                        SUM(h.toneladas_cana_molida) as total_produccion,
                        AVG(h.tch) as promedio_tch
                    FROM hechos_cosecha h
                    JOIN dimfinca f ON h.id_finca = f.finca_id
                    GROUP BY f.nombre_finca
                    ORDER BY total_produccion DESC
                    LIMIT 5
                    """
                elif "zona" in question_lower:
                    return """
                    SELECT 
                        z.nombre_zona,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimzona z ON h.codigo_zona = z.codigo_zona
                    GROUP BY z.nombre_zona
                    ORDER BY promedio_tch DESC
                    LIMIT 5
                    """
            
            elif "promedio" in question_lower or "promedio" in question_lower:
                if "brix" in question_lower:
                    return """
                    SELECT 
                        AVG(h.brix) as promedio_brix,
                        v.nombre_variedad
                    FROM hechos_cosecha h
                    JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
                    GROUP BY v.nombre_variedad
                    ORDER BY promedio_brix DESC
                    """
                elif "tch" in question_lower:
                    return """
                    SELECT 
                        AVG(h.tch) as promedio_tch,
                        f.nombre_finca
                    FROM hechos_cosecha h
                    JOIN dimfinca f ON h.id_finca = f.finca_id
                    GROUP BY f.nombre_finca
                    ORDER BY promedio_tch DESC
                    """
            
            elif "total" in question_lower or "suma" in question_lower:
                return """
                SELECT 
                    f.nombre_finca,
                    SUM(h.toneladas_cana_molida) as total_toneladas,
                    AVG(h.tch) as promedio_tch
                FROM hechos_cosecha h
                JOIN dimfinca f ON h.id_finca = f.finca_id
                GROUP BY f.nombre_finca
                ORDER BY total_toneladas DESC
                """
            
            # Consultas específicas con filtros de año y métricas específicas
            elif "finca" in question_lower and ("menos" in question_lower or "peor" in question_lower or "menor" in question_lower):
                import re
                year_match = re.search(r'20\d{2}', question_lower)
                year_filter = f"AND t.anio = {year_match.group()}" if year_match else ""
                
                # Detectar métrica específica
                if "sacarosa" in question_lower:
                    return f"""
                    SELECT 
                        f.nombre_finca,
                        AVG(h.sacarosa) as promedio_sacarosa,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimfinca f ON h.id_finca = f.finca_id
                    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
                    WHERE 1=1 {year_filter}
                    GROUP BY f.nombre_finca
                    ORDER BY promedio_tch ASC
                    LIMIT 10
                    """
                elif "brix" in question_lower:
                    return f"""
                    SELECT 
                        f.nombre_finca,
                        AVG(h.brix) as promedio_brix,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimfinca f ON h.id_finca = f.finca_id
                    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
                    WHERE 1=1 {year_filter}
                    GROUP BY f.nombre_finca
                    ORDER BY promedio_tch ASC
                    LIMIT 10
                    """
                else:
                    return f"""
                    SELECT 
                        f.nombre_finca,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimfinca f ON h.id_finca = f.finca_id
                    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
                    WHERE 1=1 {year_filter}
                    GROUP BY f.nombre_finca
                    ORDER BY promedio_tch ASC
                    LIMIT 10
                    """
            
            elif "tendencia" in question_lower or "tiempo" in question_lower or "año" in question_lower or "mes" in question_lower:
                # Detectar si se menciona un año específico
                import re
                year_match = re.search(r'20\d{2}', question_lower)
                year_filter = f"AND t.anio = {year_match.group()}" if year_match else ""
                
                # Detectar si se menciona TCH específicamente
                if "tch" in question_lower:
                    return f"""
                    SELECT 
                        t.anio,
                        t.mes,
                        AVG(h.tch) as promedio_tch,
                        SUM(h.toneladas_cana_molida) as total_toneladas
                    FROM hechos_cosecha h
                    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
                    WHERE 1=1 {year_filter}
                    GROUP BY t.anio, t.mes
                    ORDER BY promedio_tch DESC
                    LIMIT 10
                    """
                else:
                    return f"""
                    SELECT 
                        t.anio,
                        t.mes,
                        SUM(h.toneladas_cana_molida) as total_toneladas,
                        AVG(h.tch) as promedio_tch
                    FROM hechos_cosecha h
                    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
                    WHERE 1=1 {year_filter}
                    GROUP BY t.anio, t.mes
                    ORDER BY total_toneladas DESC
                    LIMIT 10
                    """
            
            # Consulta por defecto con JOINs completos
            return """
            SELECT 
                f.nombre_finca,
                v.nombre_variedad,
                z.nombre_zona,
                t.anio,
                t.mes,
                h.toneladas_cana_molida,
                h.tch,
                h.brix,
                h.sacarosa,
                h.rendimiento_teorico
            FROM hechos_cosecha h
            JOIN dimfinca f ON h.id_finca = f.finca_id
            JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
            JOIN dimzona z ON h.codigo_zona = z.codigo_zona
            JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
            ORDER BY h.toneladas_cana_molida DESC
            LIMIT 10
            """
            
        except Exception as e:
            print(f"Error generando query: {e}")
            return f"SELECT * FROM hechos_cosecha LIMIT 10; -- Error: {str(e)}"
    
    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Ejecuta una query SQL y retorna los resultados
        
        Args:
            sql_query: Query SQL a ejecutar
            
        Returns:
            Diccionario con los resultados y metadatos
        """
        try:
            # Ejecutar la query usando pandas
            result_df = pd.read_sql(sql_query, self.database_url)
            
            return {
                "success": True,
                "data": result_df.to_dict('records'),
                "columns": list(result_df.columns),
                "row_count": len(result_df),
                "sql_query": sql_query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql_query
            }
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Procesa una pregunta usando el analizador universal y retorna la respuesta completa
        
        Args:
            question: Pregunta en lenguaje natural
            
        Returns:
            Respuesta completa con datos y visualización
        """
        try:
            print(f"🤖 Procesando pregunta: {question}")
            
            # Analizar la consulta usando el analizador universal
            intent = self.query_analyzer.analyze_query(question)
            print(f"🎯 Intención detectada: {intent}")
            
            # Generar SQL usando el generador universal
            sql_query = self.sql_generator.generate_sql(intent)
            print(f"📝 SQL generado: {sql_query}")
            
            # Ejecutar consulta
            query_result = self.execute_query(sql_query)
            
            if not query_result["success"]:
                return {
                    "success": False,
                    "error": query_result["error"],
                    "sql": sql_query,
                    "natural_response": f"Lo siento, hubo un error al procesar tu consulta: {query_result['error']}"
                }
            
            # Generar configuración de visualización
            visualization = self.sql_generator.get_visualization_config(intent)
            
            # Generar respuesta natural
            natural_response = self._generate_natural_response(question, query_result)
            
            return {
                "success": True,
                "query": question,
                "intent": {
                    "type": "select",
                    "metrics": [m.value for m in intent.metrics],
                    "dimensions": [d.value for d in intent.dimensions],
                    "filters": intent.filters,
                    "limit": intent.limit
                },
                "sql": sql_query,
                "visualization": visualization,
                "data": query_result["data"],
                "raw_data": query_result["data"],  # Para compatibilidad con frontend
                "row_count": query_result["row_count"],
                "natural_response": natural_response
            }
            
        except Exception as e:
            print(f"❌ Error procesando pregunta: {e}")
            return {
                "success": False,
                "error": str(e),
                "natural_response": f"Lo siento, hubo un error inesperado: {str(e)}"
            }
    
    def _generate_natural_response(self, question: str, query_result: Dict[str, Any]) -> str:
        """Genera una respuesta natural basada en los resultados"""
        try:
            data = query_result["data"]
            row_count = query_result["row_count"]
            
            if row_count == 0:
                return "No se encontraron datos que coincidan con tu consulta."
            
            # Detectar el tipo de consulta basado en la pregunta
            question_lower = question.lower()
            
            # Detectar métricas mencionadas
            metrics_mentioned = []
            if "tch" in question_lower:
                metrics_mentioned.append("TCH")
            if "brix" in question_lower:
                metrics_mentioned.append("Brix")
            if "sacarosa" in question_lower:
                metrics_mentioned.append("Sacarosa")
            if "toneladas" in question_lower or "produccion" in question_lower:
                metrics_mentioned.append("Producción")
            
            # Detectar dimensiones mencionadas
            dimensions_mentioned = []
            if "finca" in question_lower:
                dimensions_mentioned.append("fincas")
            if "variedad" in question_lower:
                dimensions_mentioned.append("variedades")
            if "zona" in question_lower or "region" in question_lower:
                dimensions_mentioned.append("zonas")
            if "mes" in question_lower or "año" in question_lower or "tiempo" in question_lower:
                dimensions_mentioned.append("períodos")
            
            # Detectar tipo de gráfico
            chart_type = ""
            if "circular" in question_lower or "pastel" in question_lower or "pie" in question_lower:
                chart_type = "gráfico circular"
            elif "barras" in question_lower or "barra" in question_lower:
                chart_type = "gráfico de barras"
            elif "linea" in question_lower or "tendencia" in question_lower:
                chart_type = "gráfico de líneas"
            
            # Construir respuesta contextualizada
            response_parts = []
            
            # Saludo contextual
            if chart_type:
                response_parts.append(f"Aquí tienes el {chart_type} que solicitaste")
            else:
                response_parts.append("Aquí tienes los resultados de tu consulta")
            
            # Mencionar métricas y dimensiones
            if metrics_mentioned and dimensions_mentioned:
                response_parts.append(f"mostrando {', '.join(metrics_mentioned)} por {', '.join(dimensions_mentioned)}")
            elif metrics_mentioned:
                response_parts.append(f"mostrando {', '.join(metrics_mentioned)}")
            elif dimensions_mentioned:
                response_parts.append(f"agrupado por {', '.join(dimensions_mentioned)}")
            
            # Mencionar filtros temporales
            if "2024" in question_lower:
                response_parts.append("para el año 2024")
            elif "2023" in question_lower:
                response_parts.append("para el año 2023")
            elif "2022" in question_lower:
                response_parts.append("para el año 2022")
            
            # Mencionar cantidad de resultados
            if row_count == 1:
                response_parts.append("(1 resultado encontrado)")
            else:
                response_parts.append(f"({row_count} resultados encontrados)")
            
            # Agregar información específica para consultas de ranking
            if ("top" in question_lower or "mejor" in question_lower or "ranking" in question_lower) and data:
                top_items = data[:3]  # Mostrar solo los primeros 3
                top_list = []
                for i, item in enumerate(top_items):
                    # Obtener el primer valor del diccionario (nombre)
                    first_key = list(item.keys())[0]
                    first_value = item[first_key]
                    top_list.append(f"{i+1}. {first_value}")
                
                if top_list:
                    response_parts.append(f"\n\nLos principales son: {', '.join(top_list)}")
            
            return ". ".join(response_parts) + "."
                
        except Exception as e:
            return f"Se encontraron {query_result.get('row_count', 0)} registros que coinciden con tu consulta."
    
    def _format_top_result(self, record: Dict[str, Any]) -> str:
        """Formatea un resultado individual"""
        key_fields = ['nombre_finca', 'nombre_variedad', 'nombre_zona', 'anio', 'mes']
        values = []
        for field in key_fields:
            if field in record and record[field]:
                values.append(f"{field}: {record[field]}")
        return ", ".join(values)
    
    def _format_top_results(self, records: List[Dict[str, Any]]) -> str:
        """Formatea múltiples resultados"""
        formatted = []
        for i, record in enumerate(records, 1):
            formatted.append(f"{i}. {self._format_top_result(record)}")
        return "\n".join(formatted)
    
    def _format_average_result(self, data: List[Dict[str, Any]]) -> str:
        """Formatea resultado de promedio"""
        # Buscar campos que contengan "promedio" o "avg"
        numeric_fields = ['promedio_brix', 'promedio_tch', 'promedio_sacarosa', 'promedio_rendimiento', 
                         'avg_brix', 'avg_tch', 'avg_sacarosa', 'avg_rendimiento',
                         'toneladas_cana_molida', 'tch', 'brix', 'sacarosa', 'rendimiento_teorico']
        
        averages = {}
        for field in numeric_fields:
            values = []
            for record in data:
                if field in record and record[field] is not None:
                    try:
                        values.append(float(record[field]))
                    except (ValueError, TypeError):
                        continue
            if values:
                averages[field] = sum(values) / len(values)
        
        if averages:
            # Formatear solo los campos más relevantes
            relevant_fields = ['promedio_brix', 'promedio_tch', 'promedio_sacarosa', 'brix', 'tch', 'sacarosa']
            formatted = []
            for field in relevant_fields:
                if field in averages:
                    formatted.append(f"{field}: {averages[field]:.2f}")
            return ", ".join(formatted) if formatted else f"Promedio calculado: {len(data)} registros"
        
        # Si no encuentra campos numéricos, verificar si hay datos
        if data:
            return f"Se encontraron {len(data)} registros con promedios calculados"
        return "No hay datos numéricos para promediar"
    
    def _format_total_result(self, data: List[Dict[str, Any]]) -> str:
        """Formatea resultado de total"""
        # Buscar campos que contengan "total" o "sum"
        numeric_fields = ['total_produccion', 'total_toneladas', 'total_brix', 'total_tch',
                         'sum_toneladas', 'sum_brix', 'sum_tch',
                         'toneladas_cana_molida', 'tch', 'brix', 'sacarosa', 'rendimiento_teorico']
        
        totals = {}
        for field in numeric_fields:
            values = []
            for record in data:
                if field in record and record[field] is not None:
                    try:
                        values.append(float(record[field]))
                    except (ValueError, TypeError):
                        continue
            if values:
                totals[field] = sum(values)
        
        if totals:
            # Formatear solo los campos más relevantes
            relevant_fields = ['total_produccion', 'total_toneladas', 'toneladas_cana_molida', 'tch', 'brix']
            formatted = []
            for field in relevant_fields:
                if field in totals:
                    formatted.append(f"{field}: {totals[field]:.2f}")
            return ", ".join(formatted) if formatted else f"Total calculado: {len(data)} registros"
        
        # Si no encuentra campos numéricos, verificar si hay datos
        if data:
            return f"Se encontraron {len(data)} registros con totales calculados"
        return "No hay datos numéricos para sumar"
    
    def _determine_visualization_type(self, question: str, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determina el tipo de visualización apropiada"""
        question_lower = question.lower()
        data = query_result["data"]
        
        # Gráfico de barras para comparaciones
        if any(word in question_lower for word in ["top", "mejor", "peor", "comparar", "ranking"]):
            return {
                "type": "bar",
                "title": "Comparación de Resultados",
                "x_axis": "categoria",
                "y_axis": "valor"
            }
        
        # Gráfico de líneas para tendencias temporales
        elif any(word in question_lower for word in ["tendencia", "tiempo", "año", "mes", "evolución"]):
            return {
                "type": "line",
                "title": "Tendencia Temporal",
                "x_axis": "tiempo",
                "y_axis": "valor"
            }
        
        # Gráfico de pastel para distribuciones
        elif any(word in question_lower for word in ["distribución", "porcentaje", "proporción"]):
            return {
                "type": "pie",
                "title": "Distribución",
                "label": "categoria",
                "value": "cantidad"
            }
        
        # Tabla por defecto
        else:
            return {
                "type": "table",
                "title": "Resultados de la Consulta",
                "columns": query_result["columns"]
            }
    
    def _analyze_intent(self, question: str) -> Dict[str, Any]:
        """Analiza la intención de la pregunta"""
        question_lower = question.lower()
        
        # Detectar métricas
        metrics = []
        if "toneladas" in question_lower or "producción" in question_lower:
            metrics.append("toneladas_cana_molida")
        if "tch" in question_lower:
            metrics.append("tch")
        if "brix" in question_lower:
            metrics.append("brix")
        if "sacarosa" in question_lower:
            metrics.append("sacarosa")
        if "rendimiento" in question_lower:
            metrics.append("rendimiento_teorico")
        
        # Detectar dimensiones
        dimensions = []
        if "finca" in question_lower:
            dimensions.append("finca")
        if "variedad" in question_lower:
            dimensions.append("variedad")
        if "zona" in question_lower:
            dimensions.append("zona")
        if "tiempo" in question_lower or "año" in question_lower or "mes" in question_lower:
            dimensions.append("tiempo")
        
        # Detectar tipo de consulta
        query_type = "select"
        if "top" in question_lower or "mejor" in question_lower:
            query_type = "ranking"
        elif "promedio" in question_lower:
            query_type = "average"
        elif "total" in question_lower or "suma" in question_lower:
            query_type = "sum"
        
        return {
            "type": query_type,
            "metrics": metrics,
            "dimensions": dimensions,
            "filters": {},
            "limit": 10
        }
