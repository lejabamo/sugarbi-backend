"""
Motor OLAP avanzado para SugarBI
Implementa operaciones multidimensionales: drill-down, roll-up, slice, dice, pivot
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import json

class OLAPOperation(Enum):
    """Operaciones OLAP disponibles"""
    AGGREGATE = "aggregate"
    DRILL_DOWN = "drill_down"
    ROLL_UP = "roll_up"
    SLICE = "slice"
    DICE = "dice"
    PIVOT = "pivot"

class AggregationFunction(Enum):
    """Funciones de agregación disponibles"""
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    COUNT = "count"
    STD = "std"
    MEDIAN = "median"
    VARIANCE = "variance"

class DimensionLevel(Enum):
    """Niveles de dimensión disponibles"""
    # Tiempo
    YEAR = "year"
    QUARTER = "quarter"
    MONTH = "month"
    DATE = "date"
    
    # Geografía
    ZONE = "zone"
    FARM = "farm"
    
    # Producto
    VARIETY = "variety"

@dataclass
class OLAPQuery:
    """Estructura para consultas OLAP"""
    operation: OLAPOperation
    measures: List[str]
    dimensions: List[str]
    dimension_levels: Dict[str, DimensionLevel]
    filters: Dict[str, Any]
    aggregation_functions: List[AggregationFunction]
    limit: int = 100
    sort_by: Optional[str] = None
    pivot_dimension: Optional[str] = None

@dataclass
class OLAPResult:
    """Resultado de una consulta OLAP"""
    success: bool
    data: List[Dict[str, Any]]
    record_count: int
    execution_time: float
    operation: str
    sql_query: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

class OLAEEngine:
    """Motor OLAP para operaciones multidimensionales"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.dimension_mappings = self._initialize_dimension_mappings()
        self.measure_mappings = self._initialize_measure_mappings()
        
    def _initialize_dimension_mappings(self) -> Dict[str, Dict[str, str]]:
        """Inicializa mapeos de dimensiones a tablas y columnas"""
        return {
            "tiempo": {
                "table": "dimtiempo",
                "levels": {
                    DimensionLevel.YEAR: "año",
                    DimensionLevel.QUARTER: "trimestre", 
                    DimensionLevel.MONTH: "mes",
                    DimensionLevel.DATE: "fecha"
                },
                "join_key": "codigo_tiempo"
            },
            "geografia": {
                "table": "dimfinca",
                "levels": {
                    DimensionLevel.ZONE: "zona",
                    DimensionLevel.FARM: "nombre_finca"
                },
                "join_key": "id_finca"
            },
            "producto": {
                "table": "dimvariedad",
                "levels": {
                    DimensionLevel.VARIETY: "nombre_variedad"
                },
                "join_key": "codigo_variedad"
            }
        }
    
    def _initialize_measure_mappings(self) -> Dict[str, str]:
        """Inicializa mapeos de medidas a columnas"""
        return {
            "toneladas": "toneladas_cana_molida",
            "tch": "tch",
            "brix": "brix",
            "sacarosa": "sacarosa",
            "area": "area_cosechada",
            "rendimiento": "rendimiento_teorico"
        }
    
    def execute_olap_query(self, query: OLAPQuery) -> OLAPResult:
        """Ejecuta una consulta OLAP"""
        start_time = time.time()
        
        try:
            # Generar SQL basado en la operación
            if query.operation == OLAPOperation.AGGREGATE:
                sql_query = self._generate_aggregate_query(query)
            elif query.operation == OLAPOperation.DRILL_DOWN:
                sql_query = self._generate_drill_down_query(query)
            elif query.operation == OLAPOperation.ROLL_UP:
                sql_query = self._generate_roll_up_query(query)
            elif query.operation == OLAPOperation.SLICE:
                sql_query = self._generate_slice_query(query)
            elif query.operation == OLAPOperation.DICE:
                sql_query = self._generate_dice_query(query)
            elif query.operation == OLAPOperation.PIVOT:
                sql_query = self._generate_pivot_query(query)
            else:
                raise ValueError(f"Operación OLAP no soportada: {query.operation}")
            
            # Ejecutar consulta
            df = pd.read_sql(sql_query, self.engine)
            
            # Convertir a formato de diccionarios
            data = df.to_dict('records')
            
            # Convertir tipos numpy a nativos de Python
            for record in data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (np.integer, np.int64)):
                        record[key] = int(value)
                    elif isinstance(value, (np.floating, np.float64)):
                        record[key] = float(value)
            
            execution_time = time.time() - start_time
            
            return OLAPResult(
                success=True,
                data=data,
                record_count=len(data),
                execution_time=execution_time,
                operation=query.operation.value,
                sql_query=sql_query,
                metadata={
                    "dimensions": query.dimensions,
                    "measures": query.measures,
                    "aggregation_functions": [f.value for f in query.aggregation_functions],
                    "filters": query.filters
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return OLAPResult(
                success=False,
                data=[],
                record_count=0,
                execution_time=execution_time,
                operation=query.operation.value,
                sql_query="",
                metadata={},
                error=str(e)
            )
    
    def _generate_aggregate_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para operación de agregación"""
        # Construir SELECT con dimensiones y medidas
        select_parts = []
        
        # Agregar dimensiones
        for dimension in query.dimensions:
            if dimension in self.dimension_mappings:
                level = query.dimension_levels.get(dimension, DimensionLevel.YEAR)
                column = self.dimension_mappings[dimension]["levels"][level]
                
                # Usar alias consistente
                if dimension == "tiempo":
                    table_alias = "t"
                elif dimension == "geografia":
                    table_alias = "f"
                elif dimension == "producto":
                    table_alias = "v"
                else:
                    table_alias = dimension[0]
                    
                select_parts.append(f"{table_alias}.{column} as {dimension}_{level.value}")
        
        # Agregar medidas con funciones de agregación
        for measure in query.measures:
            if measure in self.measure_mappings:
                column = self.measure_mappings[measure]
                for agg_func in query.aggregation_functions:
                    if agg_func == AggregationFunction.SUM:
                        select_parts.append(f"SUM(h.{column}) as {measure}_sum")
                    elif agg_func == AggregationFunction.AVG:
                        select_parts.append(f"AVG(h.{column}) as {measure}_avg")
                    elif agg_func == AggregationFunction.MAX:
                        select_parts.append(f"MAX(h.{column}) as {measure}_max")
                    elif agg_func == AggregationFunction.MIN:
                        select_parts.append(f"MIN(h.{column}) as {measure}_min")
                    elif agg_func == AggregationFunction.COUNT:
                        select_parts.append(f"COUNT(h.{column}) as {measure}_count")
                    elif agg_func == AggregationFunction.STD:
                        select_parts.append(f"STDDEV(h.{column}) as {measure}_std")
        
        # Construir FROM y JOINs
        from_clause = "FROM hechos_cosecha h"
        join_clauses = []
        used_aliases = set()
        
        for dimension in query.dimensions:
            if dimension in self.dimension_mappings:
                table = self.dimension_mappings[dimension]["table"]
                join_key = self.dimension_mappings[dimension]["join_key"]
                
                # Crear alias único para cada tabla
                if table == "dimtiempo":
                    table_alias = "t"
                elif table == "dimfinca":
                    table_alias = "f"
                elif table == "dimvariedad":
                    table_alias = "v"
                elif table == "dimzona":
                    table_alias = "z"
                else:
                    table_alias = dimension[0]
                
                # Evitar JOINs duplicados
                if table_alias not in used_aliases:
                    if dimension == "tiempo":
                        join_clauses.append(f"JOIN {table} {table_alias} ON h.codigo_tiempo = {table_alias}.tiempo_id")
                    elif dimension == "geografia":
                        join_clauses.append(f"JOIN {table} {table_alias} ON h.id_finca = {table_alias}.finca_id")
                    elif dimension == "producto":
                        join_clauses.append(f"JOIN {table} {table_alias} ON h.codigo_variedad = {table_alias}.variedad_id")
                    used_aliases.add(table_alias)
        
        # Construir WHERE con filtros
        where_clauses = []
        for key, value in query.filters.items():
            if key == "año":
                # Solo agregar filtro de año si la tabla de tiempo está incluida
                if "t" in used_aliases:
                    where_clauses.append(f"t.año = {value}")
            elif key == "mes":
                # Solo agregar filtro de mes si la tabla de tiempo está incluida
                if "t" in used_aliases:
                    where_clauses.append(f"t.mes = {value}")
            elif key == "zona":
                # Solo agregar filtro de zona si la tabla de finca está incluida
                if "f" in used_aliases:
                    where_clauses.append(f"f.nombre_zona = '{value}'")
            elif key == "finca":
                # Solo agregar filtro de finca si la tabla de finca está incluida
                if "f" in used_aliases:
                    where_clauses.append(f"f.nombre_finca = '{value}'")
            elif key == "variedad":
                # Solo agregar filtro de variedad si la tabla de variedad está incluida
                if "v" in used_aliases:
                    where_clauses.append(f"v.nombre_variedad = '{value}'")
        
        # Construir GROUP BY
        group_by_parts = []
        for dimension in query.dimensions:
            if dimension in self.dimension_mappings:
                level = query.dimension_levels.get(dimension, DimensionLevel.YEAR)
                column = self.dimension_mappings[dimension]["levels"][level]
                
                # Usar alias consistente
                if dimension == "tiempo":
                    table_alias = "t"
                elif dimension == "geografia":
                    table_alias = "f"
                elif dimension == "producto":
                    table_alias = "v"
                else:
                    table_alias = dimension[0]
                    
                group_by_parts.append(f"{table_alias}.{column}")
        
        # Construir ORDER BY
        order_by = ""
        if query.sort_by:
            order_by = f"ORDER BY {query.sort_by} DESC"
        
        # Construir consulta completa
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *join_clauses
        ]
        
        if where_clauses:
            sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        if group_by_parts:
            sql_parts.append(f"GROUP BY {', '.join(group_by_parts)}")
        
        if order_by:
            sql_parts.append(order_by)
        
        sql_parts.append(f"LIMIT {query.limit}")
        
        return " ".join(sql_parts)
    
    def _generate_drill_down_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para drill-down (mayor detalle)"""
        # Para drill-down, agregamos más dimensiones o bajamos de nivel
        # Por ejemplo, de año a mes, o de zona a finca
        return self._generate_aggregate_query(query)
    
    def _generate_roll_up_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para roll-up (menor detalle)"""
        # Para roll-up, removemos dimensiones o subimos de nivel
        # Por ejemplo, de mes a año, o de finca a zona
        return self._generate_aggregate_query(query)
    
    def _generate_slice_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para slice (corte en una dimensión)"""
        # Para slice, fijamos una dimensión específica
        return self._generate_aggregate_query(query)
    
    def _generate_dice_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para dice (corte en múltiples dimensiones)"""
        # Para dice, aplicamos filtros en múltiples dimensiones
        return self._generate_aggregate_query(query)
    
    def _generate_pivot_query(self, query: OLAPQuery) -> str:
        """Genera consulta SQL para pivot (rotación de dimensiones)"""
        # Para pivot, rotamos las dimensiones (filas se convierten en columnas)
        # Esto requiere lógica más compleja, por ahora usamos agregación
        return self._generate_aggregate_query(query)
    
    def get_available_dimensions(self) -> Dict[str, List[str]]:
        """Retorna dimensiones disponibles"""
        return {
            "dimensions": list(self.dimension_mappings.keys()),
            "levels": {
                dim: [level.value for level in mapping["levels"].keys()]
                for dim, mapping in self.dimension_mappings.items()
            }
        }
    
    def get_available_measures(self) -> List[str]:
        """Retorna medidas disponibles"""
        return list(self.measure_mappings.keys())
    
    def get_available_aggregations(self) -> List[str]:
        """Retorna funciones de agregación disponibles"""
        return [func.value for func in AggregationFunction]
    
    def get_dimension_values(self, dimension: str, level: DimensionLevel) -> List[Dict[str, Any]]:
        """Retorna valores únicos para una dimensión y nivel específicos"""
        try:
            if dimension not in self.dimension_mappings:
                return []
            
            mapping = self.dimension_mappings[dimension]
            table = mapping["table"]
            column = mapping["levels"][level]
            
            query = f"SELECT DISTINCT {column} as value FROM {table} ORDER BY {column}"
            df = pd.read_sql(query, self.engine)
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Error obteniendo valores de dimensión: {e}")
            return []
    
    def create_pivot_table(self, data: List[Dict[str, Any]], 
                          row_dimension: str, 
                          col_dimension: str, 
                          measure: str) -> Dict[str, Any]:
        """Crea tabla dinámica a partir de datos"""
        try:
            df = pd.DataFrame(data)
            
            # Crear tabla dinámica
            pivot_table = df.pivot_table(
                index=row_dimension,
                columns=col_dimension,
                values=measure,
                aggfunc='sum',
                fill_value=0
            )
            
            # Convertir a formato JSON
            result = {
                "rows": pivot_table.index.tolist(),
                "columns": pivot_table.columns.tolist(),
                "data": pivot_table.values.tolist(),
                "total_rows": len(pivot_table.index),
                "total_columns": len(pivot_table.columns)
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_olap_examples(self) -> List[Dict[str, Any]]:
        """Retorna ejemplos de consultas OLAP"""
        return [
            {
                "name": "Producción por Año",
                "description": "Muestra la producción total de caña por año",
                "operation": "aggregate",
                "dimensions": ["tiempo"],
                "dimension_levels": {"tiempo": "year"},
                "measures": ["toneladas"],
                "aggregation_functions": ["sum"],
                "filters": {}
            },
            {
                "name": "Top Fincas por TCH",
                "description": "Las mejores fincas por TCH promedio",
                "operation": "aggregate",
                "dimensions": ["geografia"],
                "dimension_levels": {"geografia": "farm"},
                "measures": ["tch"],
                "aggregation_functions": ["avg"],
                "filters": {"año": 2025}
            },
            {
                "name": "Análisis por Zona y Variedad",
                "description": "Producción desglosada por zona y variedad",
                "operation": "dice",
                "dimensions": ["geografia", "producto"],
                "dimension_levels": {"geografia": "zone", "producto": "variety"},
                "measures": ["toneladas", "brix"],
                "aggregation_functions": ["sum", "avg"],
                "filters": {"año": 2025}
            },
            {
                "name": "Tendencia Mensual",
                "description": "Evolución de la producción por mes",
                "operation": "drill_down",
                "dimensions": ["tiempo"],
                "dimension_levels": {"tiempo": "month"},
                "measures": ["toneladas"],
                "aggregation_functions": ["sum"],
                "filters": {"año": 2025}
            },
            {
                "name": "Comparación de Calidad",
                "description": "Comparación de Brix y Sacarosa por variedad",
                "operation": "slice",
                "dimensions": ["producto"],
                "dimension_levels": {"producto": "variety"},
                "measures": ["brix", "sacarosa"],
                "aggregation_functions": ["avg", "max", "min"],
                "filters": {"año": 2025}
            }
        ]

# Ejemplo de uso
if __name__ == "__main__":
    # Configuración de ejemplo
    database_url = "mysql+pymysql://user:password@localhost:3306/sugarbi"
    
    # Crear motor OLAP
    olap_engine = OLAEEngine(database_url)
    
    # Ejemplo de consulta
    query = OLAPQuery(
        operation=OLAPOperation.AGGREGATE,
        measures=["toneladas", "tch"],
        dimensions=["tiempo"],
        dimension_levels={"tiempo": DimensionLevel.YEAR},
        filters={"año": 2025},
        aggregation_functions=[AggregationFunction.SUM, AggregationFunction.AVG],
        limit=10
    )
    
    # Ejecutar consulta
    result = olap_engine.execute_olap_query(query)
    
    if result.success:
        print(f"Consulta exitosa: {result.record_count} registros")
        print(f"Tiempo de ejecución: {result.execution_time:.3f}s")
        print("Datos:", result.data[:3])
    else:
        print(f"Error: {result.error}")
