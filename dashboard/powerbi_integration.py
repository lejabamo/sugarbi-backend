"""
Integración con Power BI para SugarBI
Proporciona endpoints y funcionalidades específicas para análisis OLAP en Power BI
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import configparser
from pathlib import Path
import logging

# Importar el motor OLAP existente
from .olap_engine import OLAEEngine, OLAPQuery, OLAPOperation, AggregationFunction, DimensionLevel

logger = logging.getLogger(__name__)

@dataclass
class PowerBIDataset:
    """Estructura de datos para Power BI"""
    name: str
    description: str
    tables: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    measures: List[Dict[str, Any]]
    created_at: datetime

@dataclass
class PowerBITable:
    """Estructura de tabla para Power BI"""
    name: str
    columns: List[Dict[str, Any]]
    data: List[Dict[str, Any]]
    row_count: int

class PowerBIIntegration:
    """Clase principal para integración con Power BI"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.engine = create_engine(db_connection_string)
        self.olap_engine = OLAEEngine(db_connection_string)
        
    def get_cube_schema(self) -> Dict[str, Any]:
        """Obtener esquema del cubo OLAP para Power BI"""
        try:
            # Obtener dimensiones
            dimensions = self.olap_engine.get_available_dimensions()
            
            # Obtener medidas
            measures = self.olap_engine.get_available_measures()
            
            # Obtener agregaciones
            aggregations = self.olap_engine.get_available_aggregations()
            
            return {
                "success": True,
                "data": {
                    "cube_name": "SugarBI_Cosecha_Cube",
                    "description": "Cubo OLAP para análisis de cosecha de caña de azúcar",
                    "dimensions": dimensions,
                    "measures": measures,
                    "aggregations": aggregations,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo esquema del cubo: {str(e)}")
            return {
                "success": False,
                "error": f"Error obteniendo esquema: {str(e)}"
            }
    
    def export_fact_table(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Exportar tabla de hechos para Power BI"""
        try:
            # Query base para tabla de hechos
            base_query = """
            SELECT 
                hc.id as fact_id,
                hc.toneladas,
                hc.tch,
                hc.brix,
                hc.sacarosa,
                hc.area,
                hc.rendimiento,
                hc.fecha_cosecha,
                
                -- Dimensiones de tiempo
                dt.anio,
                dt.trimestre,
                dt.mes,
                dt.fecha,
                
                -- Dimensiones geográficas
                df.nombre_finca,
                df.codigo_finca,
                df.area_finca,
                dz.nombre_zona,
                dz.codigo_zona,
                
                -- Dimensiones de producto
                dv.nombre_variedad,
                dv.codigo_variedad,
                dv.tipo_cana,
                
                -- Metadatos
                hc.created_at,
                hc.updated_at
                
            FROM hechos_cosecha hc
            JOIN dimtiempo dt ON hc.tiempo_id = dt.id
            JOIN dimfinca df ON hc.finca_id = df.id
            JOIN dimzona dz ON df.zona_id = dz.id
            JOIN dimvariedad dv ON hc.variedad_id = dv.id
            """
            
            # Aplicar filtros si existen
            where_conditions = []
            params = {}
            
            if filters:
                if 'start_date' in filters:
                    where_conditions.append("dt.fecha >= :start_date")
                    params['start_date'] = filters['start_date']
                
                if 'end_date' in filters:
                    where_conditions.append("dt.fecha <= :end_date")
                    params['end_date'] = filters['end_date']
                
                if 'zones' in filters:
                    where_conditions.append("dz.codigo_zona IN :zones")
                    params['zones'] = tuple(filters['zones'])
                
                if 'varieties' in filters:
                    where_conditions.append("dv.codigo_variedad IN :varieties")
                    params['varieties'] = tuple(filters['varieties'])
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            # Ejecutar query
            with self.engine.connect() as conn:
                df = pd.read_sql(text(base_query), conn, params=params)
            
            # Convertir a formato Power BI
            data = df.to_dict('records')
            
            # Definir columnas con tipos para Power BI
            columns = [
                {"name": "fact_id", "type": "Int64", "description": "ID único del hecho"},
                {"name": "toneladas", "type": "Decimal", "description": "Toneladas de caña cosechada"},
                {"name": "tch", "type": "Decimal", "description": "Toneladas de caña por hectárea"},
                {"name": "brix", "type": "Decimal", "description": "Grados Brix"},
                {"name": "sacarosa", "type": "Decimal", "description": "Porcentaje de sacarosa"},
                {"name": "area", "type": "Decimal", "description": "Área cosechada en hectáreas"},
                {"name": "rendimiento", "type": "Decimal", "description": "Rendimiento por hectárea"},
                {"name": "fecha_cosecha", "type": "DateTime", "description": "Fecha de cosecha"},
                {"name": "anio", "type": "Int64", "description": "Año"},
                {"name": "trimestre", "type": "Int64", "description": "Trimestre"},
                {"name": "mes", "type": "Int64", "description": "Mes"},
                {"name": "fecha", "type": "DateTime", "description": "Fecha completa"},
                {"name": "nombre_finca", "type": "String", "description": "Nombre de la finca"},
                {"name": "codigo_finca", "type": "String", "description": "Código de la finca"},
                {"name": "area_finca", "type": "Decimal", "description": "Área total de la finca"},
                {"name": "nombre_zona", "type": "String", "description": "Nombre de la zona"},
                {"name": "codigo_zona", "type": "String", "description": "Código de la zona"},
                {"name": "nombre_variedad", "type": "String", "description": "Nombre de la variedad"},
                {"name": "codigo_variedad", "type": "String", "description": "Código de la variedad"},
                {"name": "tipo_cana", "type": "String", "description": "Tipo de caña"},
                {"name": "created_at", "type": "DateTime", "description": "Fecha de creación"},
                {"name": "updated_at", "type": "DateTime", "description": "Fecha de actualización"}
            ]
            
            return {
                "success": True,
                "data": {
                    "table_name": "Fact_Cosecha",
                    "description": "Tabla de hechos de cosecha para análisis OLAP",
                    "columns": columns,
                    "data": data,
                    "row_count": len(data),
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error exportando tabla de hechos: {str(e)}")
            return {
                "success": False,
                "error": f"Error exportando datos: {str(e)}"
            }
    
    def export_dimension_tables(self) -> Dict[str, Any]:
        """Exportar tablas de dimensiones para Power BI"""
        try:
            dimensions_data = {}
            
            # Tabla de tiempo
            with self.engine.connect() as conn:
                tiempo_df = pd.read_sql("""
                    SELECT 
                        id,
                        anio,
                        trimestre,
                        mes,
                        fecha,
                        nombre_mes,
                        nombre_trimestre,
                        es_fin_semana,
                        es_feriado,
                        created_at
                    FROM dimtiempo
                    ORDER BY fecha
                """, conn)
                
                finca_df = pd.read_sql("""
                    SELECT 
                        df.id,
                        df.nombre_finca,
                        df.codigo_finca,
                        df.area_finca,
                        df.ubicacion,
                        df.responsable,
                        df.telefono,
                        df.email,
                        dz.nombre_zona,
                        dz.codigo_zona,
                        df.created_at
                    FROM dimfinca df
                    JOIN dimzona dz ON df.zona_id = dz.id
                    ORDER BY df.nombre_finca
                """, conn)
                
                variedad_df = pd.read_sql("""
                    SELECT 
                        id,
                        nombre_variedad,
                        codigo_variedad,
                        tipo_cana,
                        descripcion,
                        rendimiento_promedio,
                        brix_promedio,
                        created_at
                    FROM dimvariedad
                    ORDER BY nombre_variedad
                """, conn)
                
                zona_df = pd.read_sql("""
                    SELECT 
                        id,
                        nombre_zona,
                        codigo_zona,
                        descripcion,
                        area_total,
                        created_at
                    FROM dimzona
                    ORDER BY nombre_zona
                """, conn)
            
            dimensions_data = {
                "Dim_Tiempo": {
                    "columns": [
                        {"name": "id", "type": "Int64", "description": "ID único"},
                        {"name": "anio", "type": "Int64", "description": "Año"},
                        {"name": "trimestre", "type": "Int64", "description": "Trimestre"},
                        {"name": "mes", "type": "Int64", "description": "Mes"},
                        {"name": "fecha", "type": "DateTime", "description": "Fecha"},
                        {"name": "nombre_mes", "type": "String", "description": "Nombre del mes"},
                        {"name": "nombre_trimestre", "type": "String", "description": "Nombre del trimestre"},
                        {"name": "es_fin_semana", "type": "Boolean", "description": "Es fin de semana"},
                        {"name": "es_feriado", "type": "Boolean", "description": "Es feriado"},
                        {"name": "created_at", "type": "DateTime", "description": "Fecha de creación"}
                    ],
                    "data": tiempo_df.to_dict('records'),
                    "row_count": len(tiempo_df)
                },
                "Dim_Finca": {
                    "columns": [
                        {"name": "id", "type": "Int64", "description": "ID único"},
                        {"name": "nombre_finca", "type": "String", "description": "Nombre de la finca"},
                        {"name": "codigo_finca", "type": "String", "description": "Código de la finca"},
                        {"name": "area_finca", "type": "Decimal", "description": "Área de la finca"},
                        {"name": "ubicacion", "type": "String", "description": "Ubicación"},
                        {"name": "responsable", "type": "String", "description": "Responsable"},
                        {"name": "telefono", "type": "String", "description": "Teléfono"},
                        {"name": "email", "type": "String", "description": "Email"},
                        {"name": "nombre_zona", "type": "String", "description": "Nombre de la zona"},
                        {"name": "codigo_zona", "type": "String", "description": "Código de la zona"},
                        {"name": "created_at", "type": "DateTime", "description": "Fecha de creación"}
                    ],
                    "data": finca_df.to_dict('records'),
                    "row_count": len(finca_df)
                },
                "Dim_Variedad": {
                    "columns": [
                        {"name": "id", "type": "Int64", "description": "ID único"},
                        {"name": "nombre_variedad", "type": "String", "description": "Nombre de la variedad"},
                        {"name": "codigo_variedad", "type": "String", "description": "Código de la variedad"},
                        {"name": "tipo_cana", "type": "String", "description": "Tipo de caña"},
                        {"name": "descripcion", "type": "String", "description": "Descripción"},
                        {"name": "rendimiento_promedio", "type": "Decimal", "description": "Rendimiento promedio"},
                        {"name": "brix_promedio", "type": "Decimal", "description": "Brix promedio"},
                        {"name": "created_at", "type": "DateTime", "description": "Fecha de creación"}
                    ],
                    "data": variedad_df.to_dict('records'),
                    "row_count": len(variedad_df)
                },
                "Dim_Zona": {
                    "columns": [
                        {"name": "id", "type": "Int64", "description": "ID único"},
                        {"name": "nombre_zona", "type": "String", "description": "Nombre de la zona"},
                        {"name": "codigo_zona", "type": "String", "description": "Código de la zona"},
                        {"name": "descripcion", "type": "String", "description": "Descripción"},
                        {"name": "area_total", "type": "Decimal", "description": "Área total"},
                        {"name": "created_at", "type": "DateTime", "description": "Fecha de creación"}
                    ],
                    "data": zona_df.to_dict('records'),
                    "row_count": len(zona_df)
                }
            }
            
            return {
                "success": True,
                "data": {
                    "tables": dimensions_data,
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error exportando tablas de dimensiones: {str(e)}")
            return {
                "success": False,
                "error": f"Error exportando dimensiones: {str(e)}"
            }
    
    def create_powerbi_dataset(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Crear dataset completo para Power BI"""
        try:
            # Obtener tabla de hechos
            fact_result = self.export_fact_table(filters)
            if not fact_result["success"]:
                return fact_result
            
            # Obtener tablas de dimensiones
            dim_result = self.export_dimension_tables()
            if not dim_result["success"]:
                return dim_result
            
            # Crear relaciones
            relationships = [
                {
                    "from_table": "Fact_Cosecha",
                    "from_column": "anio",
                    "to_table": "Dim_Tiempo",
                    "to_column": "anio",
                    "type": "ManyToOne"
                },
                {
                    "from_table": "Fact_Cosecha",
                    "from_column": "codigo_finca",
                    "to_table": "Dim_Finca",
                    "to_column": "codigo_finca",
                    "type": "ManyToOne"
                },
                {
                    "from_table": "Fact_Cosecha",
                    "from_column": "codigo_variedad",
                    "to_table": "Dim_Variedad",
                    "to_column": "codigo_variedad",
                    "type": "ManyToOne"
                },
                {
                    "from_table": "Fact_Cosecha",
                    "from_column": "codigo_zona",
                    "to_table": "Dim_Zona",
                    "to_column": "codigo_zona",
                    "type": "ManyToOne"
                }
            ]
            
            # Crear medidas calculadas
            measures = [
                {
                    "name": "Total_Toneladas",
                    "expression": "SUM(Fact_Cosecha[toneladas])",
                    "description": "Suma total de toneladas"
                },
                {
                    "name": "Promedio_TCH",
                    "expression": "AVERAGE(Fact_Cosecha[tch])",
                    "description": "Promedio de TCH"
                },
                {
                    "name": "Promedio_Brix",
                    "expression": "AVERAGE(Fact_Cosecha[brix])",
                    "description": "Promedio de Brix"
                },
                {
                    "name": "Total_Area",
                    "expression": "SUM(Fact_Cosecha[area])",
                    "description": "Suma total de área"
                },
                {
                    "name": "Rendimiento_Promedio",
                    "expression": "AVERAGE(Fact_Cosecha[rendimiento])",
                    "description": "Rendimiento promedio"
                }
            ]
            
            dataset = PowerBIDataset(
                name="SugarBI_Cosecha_Dataset",
                description="Dataset completo para análisis de cosecha en Power BI",
                tables={
                    "Fact_Cosecha": fact_result["data"],
                    **dim_result["data"]["tables"]
                },
                relationships=relationships,
                measures=measures,
                created_at=datetime.utcnow()
            )
            
            return {
                "success": True,
                "data": asdict(dataset)
            }
            
        except Exception as e:
            logger.error(f"Error creando dataset de Power BI: {str(e)}")
            return {
                "success": False,
                "error": f"Error creando dataset: {str(e)}"
            }
    
    def get_olap_analysis_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener datos para análisis OLAP específico"""
        try:
            # Crear consulta OLAP
            operation = OLAPOperation(query_params.get('operation', 'aggregate'))
            measures = query_params.get('measures', ['toneladas'])
            dimensions = query_params.get('dimensions', ['tiempo'])
            dimension_levels = query_params.get('dimension_levels', {'tiempo': 'year'})
            aggregation_functions = query_params.get('aggregation_functions', ['sum'])
            filters = query_params.get('filters', {})
            
            query = OLAPQuery(
                operation=operation,
                measures=measures,
                dimensions=dimensions,
                dimension_levels=dimension_levels,
                aggregation_functions=aggregation_functions,
                filters=filters
            )
            
            # Ejecutar consulta
            result = self.olap_engine.execute_olap_query(query)
            
            # Formatear para Power BI
            if result["success"]:
                data = result["data"]
                
                # Convertir a formato Power BI
                powerbi_data = []
                for row in data:
                    powerbi_row = {}
                    for key, value in row.items():
                        # Convertir tipos de datos
                        if isinstance(value, (int, float)):
                            powerbi_row[key] = value
                        elif isinstance(value, str):
                            powerbi_row[key] = value
                        elif hasattr(value, 'isoformat'):  # datetime
                            powerbi_row[key] = value.isoformat()
                        else:
                            powerbi_row[key] = str(value)
                    powerbi_data.append(powerbi_row)
                
                return {
                    "success": True,
                    "data": {
                        "analysis_type": operation.value,
                        "measures": measures,
                        "dimensions": dimensions,
                        "data": powerbi_data,
                        "row_count": len(powerbi_data),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error en análisis OLAP: {str(e)}")
            return {
                "success": False,
                "error": f"Error en análisis: {str(e)}"
            }

def get_powerbi_integration():
    """Crear instancia de integración con Power BI"""
    try:
        # Configuración de base de datos
        ruta_base = Path(__file__).parent.parent
        config = configparser.ConfigParser()
        config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
        db_config = config['mysql']
        
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        return PowerBIIntegration(connection_string)
        
    except Exception as e:
        logger.error(f"Error creando integración Power BI: {str(e)}")
        return None
