"""
Parser de consultas en lenguaje natural para SugarBI
Convierte consultas en español a estructuras de datos estructuradas
"""

import re
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class QueryType(Enum):
    """Tipos de consultas soportadas"""
    TOP_RANKING = "top_ranking"
    STATISTICS = "statistics"
    COMPARISON = "comparison"
    TREND = "trend"
    BASIC = "basic"

class MetricType(Enum):
    """Métricas disponibles en el data mart"""
    TONELADAS = "toneladas"
    TCH = "tch"
    BRIX = "brix"
    SACAROSA = "sacarosa"
    AREA = "area"
    RENDIMIENTO = "rendimiento"

class DimensionType(Enum):
    """Dimensiones disponibles en el data mart"""
    FINCA = "finca"
    VARIEDAD = "variedad"
    ZONA = "zona"
    TIEMPO = "tiempo"

@dataclass
class QueryIntent:
    """Representa la intención parseada de una consulta"""
    query_type: QueryType
    metric: MetricType
    dimension: DimensionType
    filters: Dict[str, Any]
    limit: Optional[int]
    time_period: Optional[str] = None

class QueryParser:
    """Parser de consultas en lenguaje natural"""
    
    def __init__(self):
        # Patrones para identificar métricas
        self.metric_patterns = {
            MetricType.TONELADAS: [
                r'toneladas?', r'producci[oó]n', r'cantidad', r'volumen',
                r'caña\s+producida', r'caña\s+molida', r'kg', r'kilogramos?'
            ],
            MetricType.TCH: [
                r'tch', r'toneladas?\s+por\s+hect[áa]rea', r'toneladas?\s+por\s+ha',
                r'productividad', r'eficiencia'
            ],
            MetricType.BRIX: [
                r'brix', r'contenido\s+de\s+az[úu]car', r'dulzor'
            ],
            MetricType.SACAROSA: [
                r'sacarosa', r'sacarosa\s+porcentaje', r'az[úu]car\s+refinada'
            ],
            MetricType.AREA: [
                r'[áa]rea', r'hect[áa]reas?', r'ha', r'superficie', r'terreno'
            ],
            MetricType.RENDIMIENTO: [
                r'rendimiento', r'eficiencia\s+de\s+cosecha', r'productividad\s+por\s+[áa]rea'
            ]
        }
        
        # Patrones para identificar dimensiones
        self.dimension_patterns = {
            DimensionType.FINCA: [
                r'fincas?', r'predios?', r'plantaciones?', r'campos?'
            ],
            DimensionType.VARIEDAD: [
                r'variedades?', r'tipos?\s+de\s+caña', r'cultivares?', r'especies?'
            ],
            DimensionType.ZONA: [
                r'zonas?', r'regiones?', r'[áa]reas?', r'sectores?'
            ],
            DimensionType.TIEMPO: [
                r'tiempo', r'fecha', r'a[ñn]o', r'mes', r'per[ií]odo', r'tendencia'
            ]
        }
        
        # Patrones para identificar tipos de consulta
        self.query_type_patterns = {
            QueryType.TOP_RANKING: [
                r'top\s+\d+', r'mejores?\s+\d+', r'primeros?\s+\d+', r'principales?\s+\d+',
                r'ranking', r'clasificaci[oó]n', r'ordenar\s+por', r'orden\s+descendente'
            ],
            QueryType.STATISTICS: [
                r'promedio', r'media', r'estad[ií]sticas?', r'resumen', r'total',
                r'suma', r'cantidad\s+total', r'cu[áa]ntos?', r'cu[áa]ntas?'
            ],
            QueryType.COMPARISON: [
                r'comparar', r'comparaci[oó]n', r'vs', r'versus', r'diferencia',
                r'contraste', r'relaci[oó]n\s+entre'
            ],
            QueryType.TREND: [
                r'tendencia', r'evoluci[oó]n', r'progresi[oó]n', r'cambio\s+en\s+el\s+tiempo',
                r'hist[oó]rico', r'serie\s+temporal', r'por\s+mes', r'por\s+a[ñn]o'
            ]
        }
        
        # Patrones para filtros temporales
        self.time_patterns = {
            r'a[ñn]o\s+(\d{4})': 'año',
            r'mes\s+(\d{1,2})': 'mes',
            r'(\d{4})': 'año',
            r'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre': 'mes_nombre'
        }
        
        # Mapeo de nombres de meses a números
        self.month_mapping = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

    def parse(self, query: str) -> QueryIntent:
        """
        Parsea una consulta en lenguaje natural y retorna un QueryIntent
        
        Args:
            query: Consulta en español
            
        Returns:
            QueryIntent: Intención parseada
        """
        query_lower = query.lower().strip()
        
        # Detectar tipo de consulta
        query_type = self._detect_query_type(query_lower)
        
        # Detectar métrica
        metric = self._detect_metric(query_lower)
        
        # Detectar dimensión
        dimension = self._detect_dimension(query_lower)
        
        # Extraer filtros
        filters = self._extract_filters(query_lower)
        
        # Extraer límite
        limit = self._extract_limit(query_lower)
        
        # Detectar período temporal
        time_period = self._detect_time_period(query_lower)
        
        return QueryIntent(
            query_type=query_type,
            metric=metric,
            dimension=dimension,
            filters=filters,
            limit=limit,
            time_period=time_period
        )

    def _detect_query_type(self, query: str) -> QueryType:
        """Detecta el tipo de consulta"""
        for query_type, patterns in self.query_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return query_type
        
        # Si no se detecta un tipo específico, determinar por contexto
        if any(word in query for word in ['top', 'mejores', 'primeros', 'principales']):
            return QueryType.TOP_RANKING
        elif any(word in query for word in ['promedio', 'total', 'suma', 'estadísticas']):
            return QueryType.STATISTICS
        elif any(word in query for word in ['tendencia', 'evolución', 'por mes', 'por año']):
            return QueryType.TREND
        else:
            return QueryType.BASIC

    def _detect_metric(self, query: str) -> MetricType:
        """Detecta la métrica principal de la consulta"""
        for metric, patterns in self.metric_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return metric
        
        # Métrica por defecto
        return MetricType.TONELADAS

    def _detect_dimension(self, query: str) -> DimensionType:
        """Detecta la dimensión principal de la consulta"""
        for dimension, patterns in self.dimension_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return dimension
        
        # Dimensión por defecto
        return DimensionType.FINCA

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extrae filtros de la consulta"""
        filters = {}
        
        # Filtros temporales
        for pattern, filter_type in self.time_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                if filter_type == 'año':
                    filters['año'] = int(matches[0])
                elif filter_type == 'mes':
                    filters['mes'] = int(matches[0])
                elif filter_type == 'mes_nombre':
                    month_name = matches[0].lower()
                    if month_name in self.month_mapping:
                        filters['mes'] = self.month_mapping[month_name]
        
        return filters

    def _extract_limit(self, query: str) -> Optional[int]:
        """Extrae el límite de resultados de la consulta"""
        # Buscar patrones como "top 10", "primeros 5", etc.
        patterns = [
            r'top\s+(\d+)',
            r'primeros?\s+(\d+)',
            r'mejores?\s+(\d+)',
            r'principales?\s+(\d+)',
            r'(\d+)\s+mejores?',
            r'(\d+)\s+primeros?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None

    def _detect_time_period(self, query: str) -> Optional[str]:
        """Detecta el período temporal de la consulta"""
        if re.search(r'por\s+mes', query, re.IGNORECASE):
            return 'monthly'
        elif re.search(r'por\s+a[ñn]o', query, re.IGNORECASE):
            return 'yearly'
        elif re.search(r'tendencia|evoluci[oó]n', query, re.IGNORECASE):
            return 'trend'
        
        return None

# Ejemplo de uso
if __name__ == "__main__":
    parser = QueryParser()
    
    # Ejemplos de consultas
    test_queries = [
        "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025",
        "¿cuáles son las 5 mejores variedades por TCH?",
        "muestra la producción por zona en 2024",
        "¿cuál es el promedio de brix por finca?",
        "muestra la tendencia de producción por mes en 2025"
    ]
    
    for query in test_queries:
        print(f"\nConsulta: {query}")
        intent = parser.parse(query)
        print(f"Tipo: {intent.query_type.value}")
        print(f"Métrica: {intent.metric.value}")
        print(f"Dimensión: {intent.dimension.value}")
        print(f"Filtros: {intent.filters}")
        print(f"Límite: {intent.limit}")
        print(f"Período: {intent.time_period}")
