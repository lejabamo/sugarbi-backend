"""
Analizador Universal de Consultas para SugarBI
Analiza consultas en lenguaje natural y genera SQL optimizado para cualquier consulta del datamart
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class MetricType(Enum):
    TCH = "tch"
    BRIX = "brix"
    SACAROSA = "sacarosa"
    TONELADAS = "toneladas"
    RENDIMIENTO = "rendimiento"

class DimensionType(Enum):
    FINCA = "finca"
    VARIEDAD = "variedad"
    ZONA = "zona"
    TIEMPO = "tiempo"

class ChartType(Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"

class AggregationType(Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MAX = "max"
    MIN = "min"

@dataclass
class QueryIntent:
    metrics: List[MetricType]
    dimensions: List[DimensionType]
    chart_type: ChartType
    aggregation: AggregationType
    filters: Dict[str, any]
    limit: int
    order_by: Optional[str] = None
    order_direction: str = "DESC"

class UniversalQueryAnalyzer:
    """Analizador universal de consultas para SugarBI"""
    
    def __init__(self):
        self.metric_patterns = {
            MetricType.TCH: [r'\btch\b', r'toneladas.*hectarea', r'productividad'],
            MetricType.BRIX: [r'\bbrix\b', r'contenido.*azucar', r'dulzor'],
            MetricType.SACAROSA: [r'\bsacarosa\b', r'azucar.*refinada', r'pureza'],
            MetricType.TONELADAS: [r'\btoneladas\b', r'produccion', r'volumen', r'cantidad'],
            MetricType.RENDIMIENTO: [r'\brendimiento\b', r'eficiencia', r'performance']
        }
        
        self.dimension_patterns = {
            DimensionType.FINCA: [r'\bfinca\b', r'\bplantacion\b', r'\bpredio\b'],
            DimensionType.VARIEDAD: [r'\bvariedad\b', r'\bclon\b', r'\bcultivar\b'],
            DimensionType.ZONA: [r'\bzona\b', r'\bregion\b', r'\barea\b', r'\bterritorio\b'],
            DimensionType.TIEMPO: [r'\baño\b', r'\bmes\b', r'\btiempo\b', r'\bfecha\b', r'\btemporal\b']
        }
        
        self.chart_patterns = {
            ChartType.PIE: [r'\bcircular\b', r'\bpastel\b', r'\bpie\b', r'\bdistribucion\b', r'\bproporcion\b'],
            ChartType.LINE: [r'\btendencia\b', r'\bevolucion\b', r'\btemporal\b', r'\blinea\b', r'\bgrafica.*linea\b'],
            ChartType.BAR: [r'\bbarras\b', r'\bcomparacion\b', r'\branking\b', r'\bgrafica.*barras\b']
        }
        
        self.aggregation_patterns = {
            AggregationType.SUM: [r'\btotal\b', r'\bsuma\b', r'\bacumulado\b', r'\bproduccion\b'],
            AggregationType.AVG: [r'\bpromedio\b', r'\bmedia\b', r'\bpromedio\b'],
            AggregationType.COUNT: [r'\bcontar\b', r'\bnumero\b', r'\bcantidad.*registros\b'],
            AggregationType.MAX: [r'\bmaximo\b', r'\bmayor\b', r'\bmejor\b', r'\btop\b'],
            AggregationType.MIN: [r'\bminimo\b', r'\bmenor\b', r'\bpeor\b', r'\bmenos\b']
        }
    
    def analyze_query(self, query: str) -> QueryIntent:
        """Analiza una consulta y determina la intención"""
        query_lower = query.lower()
        
        # Detectar métricas
        metrics = self._detect_metrics(query_lower)
        
        # Detectar dimensiones
        dimensions = self._detect_dimensions(query_lower)
        
        # Detectar tipo de gráfico
        chart_type = self._detect_chart_type(query_lower)
        
        # Detectar agregación
        aggregation = self._detect_aggregation(query_lower)
        
        # Detectar filtros
        filters = self._detect_filters(query_lower)
        
        # Detectar límite
        limit = self._detect_limit(query_lower)
        
        # Detectar ordenamiento
        order_by, order_direction = self._detect_ordering(query_lower, metrics, dimensions)
        
        return QueryIntent(
            metrics=metrics,
            dimensions=dimensions,
            chart_type=chart_type,
            aggregation=aggregation,
            filters=filters,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction
        )
    
    def _detect_metrics(self, query: str) -> List[MetricType]:
        """Detecta las métricas mencionadas en la consulta"""
        detected = []
        for metric, patterns in self.metric_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    detected.append(metric)
                    break
        return detected if detected else [MetricType.TONELADAS]  # Default
    
    def _detect_dimensions(self, query: str) -> List[DimensionType]:
        """Detecta las dimensiones mencionadas en la consulta"""
        detected = []
        for dimension, patterns in self.dimension_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    detected.append(dimension)
                    break
        return detected if detected else [DimensionType.FINCA]  # Default
    
    def _detect_chart_type(self, query: str) -> ChartType:
        """Detecta el tipo de gráfico solicitado"""
        for chart_type, patterns in self.chart_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return chart_type
        return ChartType.BAR  # Default
    
    def _detect_aggregation(self, query: str) -> AggregationType:
        """Detecta el tipo de agregación"""
        for agg_type, patterns in self.aggregation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return agg_type
        return AggregationType.AVG  # Default
    
    def _detect_filters(self, query: str) -> Dict[str, any]:
        """Detecta filtros en la consulta"""
        filters = {}
        
        # Detectar año
        year_match = re.search(r'20\d{2}', query)
        if year_match:
            filters['anio'] = int(year_match.group())
        
        # Detectar mes
        month_patterns = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        for month_name, month_num in month_patterns.items():
            if month_name in query:
                filters['mes'] = month_num
                break
        
        # Detectar trimestre
        quarter_match = re.search(r'trimestre\s*(\d)', query)
        if quarter_match:
            filters['trimestre'] = int(quarter_match.group(1))
        
        return filters
    
    def _detect_limit(self, query: str) -> int:
        """Detecta el límite de registros"""
        # Detectar "top N" o "primeros N"
        top_match = re.search(r'top\s*(\d+)', query)
        if top_match:
            return int(top_match.group(1))
        
        primeros_match = re.search(r'primeros?\s*(\d+)', query)
        if primeros_match:
            return int(primeros_match.group(1))
        
        # Detectar "mejores N" o "peores N"
        mejores_match = re.search(r'mejores?\s*(\d+)', query)
        if mejores_match:
            return int(mejores_match.group(1))
        
        peores_match = re.search(r'peores?\s*(\d+)', query)
        if peores_match:
            return int(peores_match.group(1))
        
        return 10  # Default
    
    def _detect_ordering(self, query: str, metrics: List[MetricType], dimensions: List[DimensionType]) -> Tuple[Optional[str], str]:
        """Detecta el ordenamiento"""
        query_lower = query.lower()
        
        # Detectar dirección
        if any(word in query_lower for word in ['menor', 'peor', 'menos', 'minimo']):
            direction = "ASC"
        else:
            direction = "DESC"
        
        # Detectar campo de ordenamiento
        if metrics:
            primary_metric = metrics[0]
            if primary_metric == MetricType.TCH:
                return "promedio_tch", direction
            elif primary_metric == MetricType.BRIX:
                # Para brix, usar el nombre correcto según la agregación
                if "total" in query_lower or "suma" in query_lower or "produccion" in query_lower:
                    return "total_brix", direction
                else:
                    return "promedio_brix", direction
            elif primary_metric == MetricType.SACAROSA:
                # Para sacarosa, usar el nombre correcto según la agregación
                if "total" in query_lower or "suma" in query_lower or "produccion" in query_lower:
                    return "total_sacarosa", direction
                else:
                    return "promedio_sacarosa", direction
            elif primary_metric == MetricType.TONELADAS:
                # Para toneladas, usar el nombre correcto según la agregación
                if "total" in query_lower or "suma" in query_lower or "produccion" in query_lower:
                    return "total_toneladas", direction
                else:
                    return "promedio_toneladas", direction
        
        return None, direction

class UniversalSQLGenerator:
    """Generador universal de SQL para SugarBI"""
    
    def __init__(self):
        self.metric_columns = {
            MetricType.TCH: "h.tch",
            MetricType.BRIX: "h.brix", 
            MetricType.SACAROSA: "h.sacarosa",
            MetricType.TONELADAS: "h.toneladas_cana_molida",
            MetricType.RENDIMIENTO: "h.rendimiento_teorico"
        }
        
        self.dimension_tables = {
            DimensionType.FINCA: ("dimfinca", "f", "f.finca_id = h.id_finca", "f.nombre_finca"),
            DimensionType.VARIEDAD: ("dimvariedad", "v", "v.variedad_id = h.codigo_variedad", "v.nombre_variedad"),
            DimensionType.ZONA: ("dimzona", "z", "z.codigo_zona = h.codigo_zona", "z.nombre_zona"),
            DimensionType.TIEMPO: ("dimtiempo", "t", "t.tiempo_id = h.codigo_tiempo", "t.anio, t.mes")
        }
        
        self.aggregation_functions = {
            AggregationType.SUM: "SUM",
            AggregationType.AVG: "AVG",
            AggregationType.COUNT: "COUNT",
            AggregationType.MAX: "MAX",
            AggregationType.MIN: "MIN"
        }
    
    def generate_sql(self, intent: QueryIntent) -> str:
        """Genera SQL basado en la intención de la consulta"""
        
        # Construir SELECT
        select_parts = []
        group_by_parts = []
        
        # Agregar dimensiones
        for dimension in intent.dimensions:
            table_info = self.dimension_tables[dimension]
            if dimension == DimensionType.TIEMPO:
                select_parts.append(table_info[3])  # t.anio, t.mes
                group_by_parts.append(table_info[3])
            else:
                select_parts.append(f"{table_info[1]}.{table_info[3].split('.')[1]}")
                group_by_parts.append(f"{table_info[1]}.{table_info[3].split('.')[1]}")
        
        # Agregar métricas con agregación
        for metric in intent.metrics:
            column = self.metric_columns[metric]
            agg_func = self.aggregation_functions[intent.aggregation]
            if intent.aggregation == AggregationType.AVG:
                metric_name = f"promedio_{metric.value}"
            elif intent.aggregation == AggregationType.SUM:
                metric_name = f"total_{metric.value}"
            else:
                metric_name = f"{intent.aggregation.value}_{metric.value}"
            select_parts.append(f"{agg_func}({column}) as {metric_name}")
        
        # Construir WHERE y asegurar dimensiones necesarias
        where_conditions = []
        for key, value in intent.filters.items():
            if key == 'anio':
                # Asegurar que se incluya la tabla dimtiempo si se filtra por año
                if DimensionType.TIEMPO not in intent.dimensions:
                    intent.dimensions.append(DimensionType.TIEMPO)
                where_conditions.append(f"t.anio = {value}")
            elif key == 'mes':
                if DimensionType.TIEMPO not in intent.dimensions:
                    intent.dimensions.append(DimensionType.TIEMPO)
                where_conditions.append(f"t.mes = {value}")
            elif key == 'trimestre':
                if DimensionType.TIEMPO not in intent.dimensions:
                    intent.dimensions.append(DimensionType.TIEMPO)
                where_conditions.append(f"t.trimestre = {value}")
        
        # Construir FROM y JOINs (después de asegurar todas las dimensiones)
        from_clause = "FROM hechos_cosecha h"
        join_clauses = []
        
        for dimension in intent.dimensions:
            table_info = self.dimension_tables[dimension]
            join_clauses.append(f"JOIN {table_info[0]} {table_info[1]} ON {table_info[2]}")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Construir GROUP BY
        group_by_clause = f"GROUP BY {', '.join(group_by_parts)}" if group_by_parts else ""
        
        # Construir ORDER BY
        order_by_clause = ""
        if intent.order_by:
            order_by_clause = f"ORDER BY {intent.order_by} {intent.order_direction}"
        
        # Construir LIMIT
        limit_clause = f"LIMIT {intent.limit}" if intent.limit else ""
        
        # Ensamblar SQL
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *join_clauses,
            where_clause,
            group_by_clause,
            order_by_clause,
            limit_clause
        ]
        
        return "\n".join(filter(None, sql_parts)) + ";"
    
    def get_visualization_config(self, intent: QueryIntent) -> Dict[str, any]:
        """Genera configuración de visualización basada en la intención"""
        
        chart_type = intent.chart_type.value
        
        # Determinar columnas para labels y datos
        if intent.dimensions:
            primary_dimension = intent.dimensions[0]
            if primary_dimension == DimensionType.TIEMPO:
                label_column = "anio"
            else:
                label_column = f"nombre_{primary_dimension.value}"
        else:
            label_column = "categoria"
        
        if intent.metrics:
            primary_metric = intent.metrics[0]
            if intent.aggregation == AggregationType.AVG:
                data_column = f"promedio_{primary_metric.value}"
            else:
                data_column = f"total_{primary_metric.value}"
        else:
            data_column = "valor"
        
        return {
            "type": chart_type,
            "title": f"Análisis de {primary_metric.value if intent.metrics else 'Datos'}",
            "x_axis": label_column,
            "y_axis": data_column,
            "columns": [label_column, data_column]
        }
