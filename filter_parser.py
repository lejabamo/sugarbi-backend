"""
Parser de Filtros Inteligente para SugarBI
Analiza las relaciones entre datos y determina qué filtros son posibles
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FilterParser:
    def __init__(self, engine):
        self.engine = engine
        
    def get_filter_combinations(self, base_filters: Dict[str, Any] = None) -> Dict[str, List[Dict]]:
        """
        Obtiene todas las combinaciones posibles de filtros basándose en los datos existentes
        """
        try:
            if base_filters is None:
                base_filters = {}
            
            # Construir la consulta base
            query = self._build_base_query(base_filters)
            
            # Ejecutar consulta para obtener combinaciones
            result = pd.read_sql(query, self.engine)
            
            # Procesar resultados
            filter_options = self._process_filter_combinations(result)
            
            logger.info(f"Filtros disponibles: {len(filter_options.get('fincas', []))} fincas, "
                       f"{len(filter_options.get('variedades', []))} variedades, "
                       f"{len(filter_options.get('zonas', []))} zonas, "
                       f"{len(filter_options.get('años', []))} años")
            
            return filter_options
            
        except Exception as e:
            logger.error(f"Error en get_filter_combinations: {e}")
            return self._get_fallback_options()
    
    def _build_base_query(self, base_filters: Dict[str, Any]) -> str:
        """
        Construye la consulta SQL base para obtener combinaciones de filtros
        """
        # Consulta que une todas las dimensiones con los hechos
        query = """
        SELECT DISTINCT
            f.finca_id,
            f.codigo_finca,
            f.nombre_finca,
            v.variedad_id,
            v.nombre_variedad,
            z.codigo_zona,
            z.nombre_zona,
            t.tiempo_id,
            t.fecha,
            t.año,
            t.mes,
            t.nombre_mes,
            t.trimestre,
            h.toneladas_cana_molida,
            h.toneladas_azucar_producida,
            h.rendimiento_por_hectarea
        FROM hechos_cosecha h
        INNER JOIN dimfinca f ON h.finca_id = f.finca_id
        INNER JOIN dimvariedad v ON h.variedad_id = v.variedad_id
        INNER JOIN dimzona z ON h.zona_id = z.codigo_zona
        INNER JOIN dimtiempo t ON h.tiempo_id = t.tiempo_id
        WHERE 1=1
        """
        
        # Aplicar filtros base
        if base_filters.get('finca_id'):
            query += f" AND f.finca_id = {base_filters['finca_id']}"
        
        if base_filters.get('variedad_id'):
            query += f" AND v.variedad_id = {base_filters['variedad_id']}"
        
        if base_filters.get('zona_id'):
            query += f" AND z.codigo_zona = '{base_filters['zona_id']}'"
        
        if base_filters.get('año'):
            query += f" AND t.año = {base_filters['año']}"
        
        if base_filters.get('mes'):
            query += f" AND t.mes = {base_filters['mes']}"
        
        query += " ORDER BY f.nombre_finca, v.nombre_variedad, z.nombre_zona, t.año DESC, t.mes ASC"
        
        return query
    
    def _process_filter_combinations(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Procesa los resultados de la consulta para crear opciones de filtros
        """
        filter_options = {
            'fincas': [],
            'variedades': [],
            'zonas': [],
            'años': [],
            'meses': []
        }
        
        if df.empty:
            return filter_options
        
        # Procesar fincas
        fincas = df[['finca_id', 'codigo_finca', 'nombre_finca']].drop_duplicates()
        for _, row in fincas.iterrows():
            filter_options['fincas'].append({
                'finca_id': int(row['finca_id']),
                'codigo_finca': str(row['codigo_finca']),
                'nombre_finca': str(row['nombre_finca']),
                'count': len(df[df['finca_id'] == row['finca_id']])
            })
        
        # Procesar variedades
        variedades = df[['variedad_id', 'nombre_variedad']].drop_duplicates()
        for _, row in variedades.iterrows():
            filter_options['variedades'].append({
                'variedad_id': int(row['variedad_id']),
                'nombre_variedad': str(row['nombre_variedad']),
                'count': len(df[df['variedad_id'] == row['variedad_id']])
            })
        
        # Procesar zonas
        zonas = df[['codigo_zona', 'nombre_zona']].drop_duplicates()
        for _, row in zonas.iterrows():
            filter_options['zonas'].append({
                'codigo_zona': str(row['codigo_zona']),
                'nombre_zona': str(row['nombre_zona']),
                'count': len(df[df['codigo_zona'] == row['codigo_zona']])
            })
        
        # Procesar años
        años = df[['año']].drop_duplicates().sort_values('año', ascending=False)
        for _, row in años.iterrows():
            filter_options['años'].append({
                'año': int(row['año']),
                'count': len(df[df['año'] == row['año']])
            })
        
        # Procesar meses
        meses = df[['mes', 'nombre_mes']].drop_duplicates().sort_values('mes')
        for _, row in meses.iterrows():
            filter_options['meses'].append({
                'mes': int(row['mes']),
                'nombre_mes': str(row['nombre_mes']),
                'count': len(df[df['mes'] == row['mes']])
            })
        
        return filter_options
    
    def _get_fallback_options(self) -> Dict[str, List[Dict]]:
        """
        Opciones de respaldo si hay error en la consulta principal
        """
        return {
            'fincas': [],
            'variedades': [],
            'zonas': [],
            'años': [],
            'meses': []
        }
    
    def get_filtered_data(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
        """
        Obtiene los datos filtrados basándose en los filtros aplicados
        """
        try:
            query = self._build_data_query(filters, limit)
            result = pd.read_sql(query, self.engine)
            
            # Convertir a lista de diccionarios
            data = []
            for _, row in result.iterrows():
                data.append({
                    'finca_id': int(row['finca_id']),
                    'codigo_finca': str(row['codigo_finca']),
                    'nombre_finca': str(row['nombre_finca']),
                    'variedad_id': int(row['variedad_id']),
                    'nombre_variedad': str(row['nombre_variedad']),
                    'zona_id': str(row['codigo_zona']),
                    'nombre_zona': str(row['nombre_zona']),
                    'tiempo_id': int(row['tiempo_id']),
                    'fecha': str(row['fecha']),
                    'año': int(row['año']),
                    'mes': int(row['mes']),
                    'nombre_mes': str(row['nombre_mes']),
                    'trimestre': int(row['trimestre']),
                    'toneladas_cana_molida': float(row['toneladas_cana_molida']),
                    'toneladas_azucar_producida': float(row['toneladas_azucar_producida']),
                    'rendimiento_por_hectarea': float(row['rendimiento_por_hectarea'])
                })
            
            logger.info(f"Datos filtrados obtenidos: {len(data)} registros")
            return data
            
        except Exception as e:
            logger.error(f"Error en get_filtered_data: {e}")
            return []
    
    def _build_data_query(self, filters: Dict[str, Any], limit: int) -> str:
        """
        Construye la consulta SQL para obtener datos filtrados
        """
        query = """
        SELECT 
            f.finca_id,
            f.codigo_finca,
            f.nombre_finca,
            v.variedad_id,
            v.nombre_variedad,
            z.codigo_zona,
            z.nombre_zona,
            t.tiempo_id,
            t.fecha,
            t.año,
            t.mes,
            t.nombre_mes,
            t.trimestre,
            h.toneladas_cana_molida,
            h.toneladas_azucar_producida,
            h.rendimiento_por_hectarea
        FROM hechos_cosecha h
        INNER JOIN dimfinca f ON h.finca_id = f.finca_id
        INNER JOIN dimvariedad v ON h.variedad_id = v.variedad_id
        INNER JOIN dimzona z ON h.zona_id = z.codigo_zona
        INNER JOIN dimtiempo t ON h.tiempo_id = t.tiempo_id
        WHERE 1=1
        """
        
        # Aplicar filtros
        if filters.get('finca_id'):
            query += f" AND f.finca_id = {filters['finca_id']}"
        
        if filters.get('variedad_id'):
            query += f" AND v.variedad_id = {filters['variedad_id']}"
        
        if filters.get('zona_id'):
            query += f" AND z.codigo_zona = '{filters['zona_id']}'"
        
        if filters.get('año'):
            query += f" AND t.año = {filters['año']}"
        
        if filters.get('mes'):
            query += f" AND t.mes = {filters['mes']}"
        
        query += f" ORDER BY h.toneladas_cana_molida DESC LIMIT {limit}"
        
        return query



