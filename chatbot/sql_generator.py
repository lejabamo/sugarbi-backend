"""
Generador de consultas SQL basado en intenciones parseadas
Convierte QueryIntent a consultas SQL válidas
"""

from typing import Dict, List, Optional
try:
    from .query_parser import QueryIntent, QueryType, MetricType, DimensionType
except ImportError:
    from query_parser import QueryIntent, QueryType, MetricType, DimensionType

class SQLGenerator:
    """Genera consultas SQL a partir de intenciones parseadas"""
    
    def __init__(self):
        # Mapeo de métricas a columnas de la base de datos
        self.metric_columns = {
            MetricType.TONELADAS: "h.toneladas_cana_molida",
            MetricType.TCH: "h.tch",
            MetricType.BRIX: "h.brix",
            MetricType.SACAROSA: "h.sacarosa",
            MetricType.AREA: "h.area_cosechada",
            MetricType.RENDIMIENTO: "h.rendimiento_teorico"
        }
        
        # Mapeo de dimensiones a tablas y columnas
        self.dimension_mappings = {
            DimensionType.FINCA: {
                "table": "dimfinca",
                "alias": "f",
                "join_key": "h.id_finca = f.finca_id",
                "name_column": "f.nombre_finca",
                "id_column": "f.finca_id"
            },
            DimensionType.VARIEDAD: {
                "table": "dimvariedad",
                "alias": "v",
                "join_key": "h.codigo_variedad = v.variedad_id",
                "name_column": "v.nombre_variedad",
                "id_column": "v.variedad_id"
            },
            DimensionType.ZONA: {
                "table": "dimzona",
                "alias": "z",
                "join_key": "h.codigo_zona = z.codigo_zona",
                "name_column": "z.nombre_zona",
                "id_column": "z.codigo_zona"
            },
            DimensionType.TIEMPO: {
                "table": "dimtiempo",
                "alias": "t",
                "join_key": "h.codigo_tiempo = t.tiempo_id",
                "name_column": "CONCAT(t.año, '-', t.nombre_mes)",
                "id_column": "t.tiempo_id"
            }
        }

    def generate_sql(self, intent: QueryIntent) -> str:
        """
        Genera una consulta SQL basada en la intención parseada
        
        Args:
            intent: QueryIntent parseada
            
        Returns:
            str: Consulta SQL generada
        """
        if intent.query_type == QueryType.TOP_RANKING:
            return self._generate_top_ranking_sql(intent)
        elif intent.query_type == QueryType.STATISTICS:
            return self._generate_statistics_sql(intent)
        elif intent.query_type == QueryType.COMPARISON:
            return self._generate_comparison_sql(intent)
        elif intent.query_type == QueryType.TREND:
            return self._generate_trend_sql(intent)
        else:
            return self._generate_basic_sql(intent)

    def _generate_top_ranking_sql(self, intent: QueryIntent) -> str:
        """Genera SQL para consultas de ranking (top N)"""
        try:
            dimension = self.dimension_mappings[intent.dimension]
            metric_column = self.metric_columns[intent.metric]
        except KeyError as e:
            raise ValueError(f"Error en mapeo de dimensiones/métricas: {e}")
        
        # Construir SELECT
        select_parts = [
            dimension["name_column"],
            f"SUM({metric_column}) as total_{intent.metric.value}",
            f"AVG({metric_column}) as promedio_{intent.metric.value}",
            "COUNT(*) as total_registros"
        ]
        
        # Agregar columnas adicionales según la dimensión
        if intent.dimension == DimensionType.FINCA:
            select_parts.extend([
                "f.codigo_finca",
                "z.nombre_zona as zona"
            ])
        elif intent.dimension == DimensionType.VARIEDAD:
            select_parts.extend([
                "v.variedad_id",
                "f.nombre_finca as finca_principal"
            ])
        
        # Construir FROM y JOINs
        from_clause = "FROM hechos_cosecha h"
        joins = [
            f"JOIN {dimension['table']} {dimension['alias']} ON {dimension['join_key']}",
            "JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id"
        ]
        
        # Agregar JOINs adicionales según la dimensión
        if intent.dimension == DimensionType.FINCA:
            joins.append("JOIN dimzona z ON h.codigo_zona = z.codigo_zona")
        elif intent.dimension == DimensionType.VARIEDAD:
            joins.append("JOIN dimfinca f ON h.id_finca = f.finca_id")
        
        # Construir WHERE
        where_conditions = []
        if intent.filters:
            if 'año' in intent.filters:
                where_conditions.append(f"t.año = {intent.filters['año']}")
            if 'mes' in intent.filters:
                where_conditions.append(f"t.mes = {intent.filters['mes']}")
        
        # Construir GROUP BY
        group_by = f"GROUP BY {dimension['name_column']}"
        if intent.dimension == DimensionType.FINCA:
            group_by += ", f.codigo_finca, z.nombre_zona"
        elif intent.dimension == DimensionType.VARIEDAD:
            group_by += ", v.variedad_id, f.nombre_finca"
        
        # Construir ORDER BY
        order_by = f"ORDER BY total_{intent.metric.value} DESC"
        
        # Construir LIMIT
        limit_clause = f"LIMIT {intent.limit}" if intent.limit else "LIMIT 10"
        
        # Ensamblar la consulta
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *joins
        ]
        
        if where_conditions:
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        sql_parts.extend([
            group_by,
            order_by,
            limit_clause
        ])
        
        return "\n".join(sql_parts)

    def _generate_statistics_sql(self, intent: QueryIntent) -> str:
        """Genera SQL para consultas estadísticas"""
        metric_column = self.metric_columns[intent.metric]
        
        select_parts = [
            f"COUNT(*) as total_registros",
            f"SUM({metric_column}) as total_{intent.metric.value}",
            f"AVG({metric_column}) as promedio_{intent.metric.value}",
            f"MIN({metric_column}) as minimo_{intent.metric.value}",
            f"MAX({metric_column}) as maximo_{intent.metric.value}",
            f"STDDEV({metric_column}) as desviacion_{intent.metric.value}"
        ]
        
        from_clause = "FROM hechos_cosecha h"
        joins = ["JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id"]
        
        where_conditions = []
        if intent.filters:
            if 'año' in intent.filters:
                where_conditions.append(f"t.año = {intent.filters['año']}")
            if 'mes' in intent.filters:
                where_conditions.append(f"t.mes = {intent.filters['mes']}")
        
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *joins
        ]
        
        if where_conditions:
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        return "\n".join(sql_parts)

    def _generate_comparison_sql(self, intent: QueryIntent) -> str:
        """Genera SQL para consultas de comparación"""
        # Por ahora, implementación básica
        return self._generate_basic_sql(intent)

    def _generate_trend_sql(self, intent: QueryIntent) -> str:
        """Genera SQL para consultas de tendencias temporales"""
        metric_column = self.metric_columns[intent.metric]
        
        select_parts = [
            "t.año",
            "t.mes",
            "t.nombre_mes",
            f"SUM({metric_column}) as total_{intent.metric.value}",
            f"AVG({metric_column}) as promedio_{intent.metric.value}"
        ]
        
        from_clause = "FROM hechos_cosecha h"
        joins = ["JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id"]
        
        where_conditions = []
        if intent.filters:
            if 'año' in intent.filters:
                where_conditions.append(f"t.año = {intent.filters['año']}")
        
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *joins
        ]
        
        if where_conditions:
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        sql_parts.extend([
            "GROUP BY t.año, t.mes, t.nombre_mes",
            "ORDER BY t.año, t.mes"
        ])
        
        return "\n".join(sql_parts)

    def _generate_basic_sql(self, intent: QueryIntent) -> str:
        """Genera SQL básico para consultas simples"""
        metric_column = self.metric_columns[intent.metric]
        dimension = self.dimension_mappings[intent.dimension]
        
        select_parts = [
            dimension["name_column"],
            metric_column
        ]
        
        from_clause = "FROM hechos_cosecha h"
        joins = [
            f"JOIN {dimension['table']} {dimension['alias']} ON {dimension['join_key']}",
            "JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id"
        ]
        
        where_conditions = []
        if intent.filters:
            if 'año' in intent.filters:
                where_conditions.append(f"t.año = {intent.filters['año']}")
            if 'mes' in intent.filters:
                where_conditions.append(f"t.mes = {intent.filters['mes']}")
        
        sql_parts = [
            f"SELECT {', '.join(select_parts)}",
            from_clause,
            *joins
        ]
        
        if where_conditions:
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        sql_parts.append(f"ORDER BY {metric_column} DESC")
        
        if intent.limit:
            sql_parts.append(f"LIMIT {intent.limit}")
        
        return "\n".join(sql_parts)

# Ejemplo de uso
if __name__ == "__main__":
    try:
        from .query_parser import QueryParser
    except ImportError:
        from query_parser import QueryParser
    
    parser = QueryParser()
    generator = SQLGenerator()
    
    # Ejemplo de consulta
    query = "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025"
    intent = parser.parse(query)
    sql = generator.generate_sql(intent)
    
    print("Consulta original:", query)
    print("\nSQL generado:")
    print(sql)
