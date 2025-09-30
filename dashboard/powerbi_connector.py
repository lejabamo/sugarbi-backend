"""
Conector específico para Power BI Desktop
Proporciona endpoints optimizados para conexión directa desde Power BI
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import configparser
from pathlib import Path
import logging
from flask import Response, request, jsonify
import io
import csv

logger = logging.getLogger(__name__)

class PowerBIConnector:
    """Conector optimizado para Power BI Desktop"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.engine = create_engine(db_connection_string)
        
    def get_connection_info(self) -> Dict[str, Any]:
        """Información de conexión para Power BI Desktop"""
        return {
            "server": "localhost",
            "port": 3306,
            "database": "sugarbi",
            "username": "root",
            "password": "toor",
            "connection_string": "mysql+pymysql://root:toor@localhost:3306/sugarbi",
            "tables": {
                "fact_table": "hechos_cosecha",
                "dimensions": {
                    "tiempo": "dimtiempo",
                    "finca": "dimfinca", 
                    "variedad": "dimvariedad",
                    "zona": "dimzona"
                }
            },
            "relationships": [
                {
                    "from_table": "hechos_cosecha",
                    "from_column": "tiempo_id",
                    "to_table": "dimtiempo",
                    "to_column": "id"
                },
                {
                    "from_table": "hechos_cosecha",
                    "from_column": "finca_id",
                    "to_table": "dimfinca",
                    "to_column": "id"
                },
                {
                    "from_table": "hechos_cosecha",
                    "from_column": "variedad_id",
                    "to_table": "dimvariedad",
                    "to_column": "id"
                },
                {
                    "from_table": "dimfinca",
                    "from_column": "zona_id",
                    "to_table": "dimzona",
                    "to_column": "id"
                }
            ]
        }
    
    def get_powerbi_ready_data(self, table_name: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Obtener datos listos para Power BI con formato optimizado"""
        try:
            # Queries optimizadas para Power BI
            queries = {
                "hechos_cosecha": """
                    SELECT 
                        hc.id as fact_id,
                        hc.toneladas,
                        hc.tch,
                        hc.brix,
                        hc.sacarosa,
                        hc.area,
                        hc.rendimiento,
                        hc.fecha_cosecha,
                        hc.tiempo_id,
                        hc.finca_id,
                        hc.variedad_id,
                        
                        -- Dimensiones de tiempo
                        dt.anio,
                        dt.trimestre,
                        dt.mes,
                        dt.fecha,
                        dt.nombre_mes,
                        dt.nombre_trimestre,
                        
                        -- Dimensiones geográficas
                        df.nombre_finca,
                        df.codigo_finca,
                        df.area_finca,
                        df.ubicacion,
                        df.responsable,
                        dz.nombre_zona,
                        dz.codigo_zona,
                        dz.descripcion as descripcion_zona,
                        
                        -- Dimensiones de producto
                        dv.nombre_variedad,
                        dv.codigo_variedad,
                        dv.tipo_cana,
                        dv.descripcion as descripcion_variedad,
                        dv.rendimiento_promedio,
                        dv.brix_promedio
                        
                    FROM hechos_cosecha hc
                    JOIN dimtiempo dt ON hc.tiempo_id = dt.id
                    JOIN dimfinca df ON hc.finca_id = df.id
                    JOIN dimzona dz ON df.zona_id = dz.id
                    JOIN dimvariedad dv ON hc.variedad_id = dv.id
                """,
                
                "dimtiempo": """
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
                """,
                
                "dimfinca": """
                    SELECT 
                        df.id,
                        df.nombre_finca,
                        df.codigo_finca,
                        df.area_finca,
                        df.ubicacion,
                        df.responsable,
                        df.telefono,
                        df.email,
                        df.zona_id,
                        dz.nombre_zona,
                        dz.codigo_zona,
                        df.created_at
                    FROM dimfinca df
                    JOIN dimzona dz ON df.zona_id = dz.id
                    ORDER BY df.nombre_finca
                """,
                
                "dimvariedad": """
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
                """,
                
                "dimzona": """
                    SELECT 
                        id,
                        nombre_zona,
                        codigo_zona,
                        descripcion,
                        area_total,
                        created_at
                    FROM dimzona
                    ORDER BY nombre_zona
                """
            }
            
            if table_name not in queries:
                return {
                    "success": False,
                    "error": f"Tabla '{table_name}' no encontrada"
                }
            
            query = queries[table_name]
            
            # Aplicar filtros si existen
            if filters and table_name == "hechos_cosecha":
                where_conditions = []
                params = {}
                
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
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Ejecutar query
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params if 'params' in locals() else {})
            
            # Optimizar tipos de datos para Power BI
            df = self._optimize_data_types(df)
            
            # Convertir a formato Power BI
            data = df.to_dict('records')
            
            return {
                "success": True,
                "data": {
                    "table_name": table_name,
                    "columns": self._get_column_info(df),
                    "data": data,
                    "row_count": len(data),
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para Power BI: {str(e)}")
            return {
                "success": False,
                "error": f"Error obteniendo datos: {str(e)}"
            }
    
    def _optimize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimizar tipos de datos para Power BI"""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Intentar convertir a datetime
                if 'fecha' in col.lower() or 'date' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
                # Intentar convertir a numérico
                elif df[col].str.contains(r'^\d+\.?\d*$', na=False).any():
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
        
        return df
    
    def _get_column_info(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Obtener información de columnas para Power BI"""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Mapear tipos de pandas a Power BI
            if 'int' in dtype:
                powerbi_type = "Whole Number"
            elif 'float' in dtype:
                powerbi_type = "Decimal Number"
            elif 'datetime' in dtype:
                powerbi_type = "Date/Time"
            elif 'bool' in dtype:
                powerbi_type = "True/False"
            else:
                powerbi_type = "Text"
            
            columns.append({
                "name": col,
                "type": powerbi_type,
                "description": f"Columna {col} de tipo {powerbi_type}"
            })
        
        return columns
    
    def export_for_powerbi_desktop(self, format_type: str = "csv") -> Response:
        """Exportar datos optimizados para Power BI Desktop"""
        try:
            # Obtener datos de la tabla de hechos
            result = self.get_powerbi_ready_data("hechos_cosecha")
            
            if not result["success"]:
                return jsonify(result), 500
            
            data = result["data"]["data"]
            
            if format_type == "csv":
                # Crear CSV optimizado para Power BI
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                
                csv_content = output.getvalue()
                output.close()
                
                return Response(
                    csv_content,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=sugarbi_datamart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        'Content-Type': 'text/csv; charset=utf-8'
                    }
                )
            
            elif format_type == "json":
                # Crear JSON optimizado para Power BI
                return Response(
                    json.dumps(result["data"], indent=2, ensure_ascii=False, default=str),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename=sugarbi_datamart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                        'Content-Type': 'application/json; charset=utf-8'
                    }
                )
            
            else:
                return jsonify({
                    "success": False,
                    "error": "Formato no soportado. Use 'csv' o 'json'"
                }), 400
                
        except Exception as e:
            logger.error(f"Error exportando para Power BI Desktop: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Error exportando: {str(e)}"
            }), 500

def get_powerbi_connector():
    """Crear instancia del conector Power BI"""
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
        
        return PowerBIConnector(connection_string)
        
    except Exception as e:
        logger.error(f"Error creando conector Power BI: {str(e)}")
        return None
