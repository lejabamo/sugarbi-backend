"""
Sistema de Intersecciones de Filtros - "Ajedrez de Filtros"
Anticipa todas las jugadas posibles y calcula intersecciones válidas
"""

import pandas as pd
from typing import Dict, List, Any, Set, Tuple
from sqlalchemy import create_engine
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FilterIntersections:
    def __init__(self, engine):
        self.engine = engine
        self.base_data = None
        
    def load_base_data(self):
        """Carga todos los datos base para calcular intersecciones"""
        try:
            logger.info("Cargando datos base para intersecciones...")
            
            query = """
            SELECT 
                h.id_finca,
                f.codigo_finca,
                f.nombre_finca,
                h.codigo_variedad,
                v.nombre_variedad,
                h.codigo_zona,
                z.nombre_zona,
                h.codigo_tiempo,
                t.fecha,
                t.año,
                t.mes,
                t.nombre_mes,
                h.toneladas_cana_molida,
                h.tch,
                h.brix,
                h.sacarosa
            FROM hechos_cosecha h
            LEFT JOIN dimfinca f ON h.id_finca = f.finca_id
            LEFT JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
            LEFT JOIN dimzona z ON h.codigo_zona = z.codigo_zona
            LEFT JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
            ORDER BY f.nombre_finca, v.nombre_variedad, z.nombre_zona, t.año DESC, t.mes ASC
            """
            
            self.base_data = pd.read_sql(query, self.engine)
            logger.info(f"Datos base cargados: {len(self.base_data)} registros")
            
            # Log de datos disponibles
            if not self.base_data.empty:
                logger.info(f"Años disponibles: {sorted(self.base_data['año'].dropna().unique())}")
                logger.info(f"Meses disponibles: {sorted(self.base_data['mes'].dropna().unique())}")
                logger.info(f"Zonas disponibles: {sorted(self.base_data['codigo_zona'].dropna().unique())}")
                logger.info(f"Variedades disponibles: {len(self.base_data['codigo_variedad'].dropna().unique())}")
                logger.info(f"Fincas disponibles: {len(self.base_data['id_finca'].dropna().unique())}")
            
        except Exception as e:
            logger.error(f"Error cargando datos base: {e}")
            self.base_data = pd.DataFrame()
    
    def get_available_options(self, current_filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Retorna opciones de filtros disponibles basadas en las selecciones actuales.
        Esta es la anticipación tipo 'ajedrez'.
        """
        if self.base_data is None or self.base_data.empty:
            logger.warning("No hay datos base cargados")
            return {
                'años': [],
                'meses': [],
                'zonas': [],
                'variedades': [],
                'fincas': []
            }
        
        # Aplicar filtros actuales para reducir los datos
        filtered_data = self.base_data.copy()
        
        if current_filters.get('año'):
            filtered_data = filtered_data[filtered_data['año'] == current_filters['año']]
            logger.info(f"Filtrado por año {current_filters['año']}: {len(filtered_data)} registros")
        
        if current_filters.get('mes'):
            filtered_data = filtered_data[filtered_data['mes'] == current_filters['mes']]
            logger.info(f"Filtrado por mes {current_filters['mes']}: {len(filtered_data)} registros")
        
        if current_filters.get('zona_id'):
            filtered_data = filtered_data[filtered_data['codigo_zona'] == current_filters['zona_id']]
            logger.info(f"Filtrado por zona {current_filters['zona_id']}: {len(filtered_data)} registros")
        
        if current_filters.get('variedad_id'):
            filtered_data = filtered_data[filtered_data['codigo_variedad'] == current_filters['variedad_id']]
            logger.info(f"Filtrado por variedad {current_filters['variedad_id']}: {len(filtered_data)} registros")
        
        if current_filters.get('finca_id'):
            filtered_data = filtered_data[filtered_data['id_finca'] == current_filters['finca_id']]
            logger.info(f"Filtrado por finca {current_filters['finca_id']}: {len(filtered_data)} registros")
        
        # Calcular opciones disponibles
        options = {
            'años': [],
            'meses': [],
            'zonas': [],
            'variedades': [],
            'fincas': []
        }
        
        # Años disponibles (siempre mostrar todos los años disponibles)
        if 'año' in filtered_data.columns:
            años_disponibles = filtered_data['año'].dropna().unique()
            for año in sorted(años_disponibles, reverse=True):
                count = len(filtered_data[filtered_data['año'] == año])
                options['años'].append({
                    'año': int(año) if pd.notna(año) else None,
                    'count': int(count)
                })
        
        # Meses disponibles (solo si hay un año seleccionado)
        if 'mes' in filtered_data.columns and 'nombre_mes' in filtered_data.columns:
            meses_disponibles = filtered_data[['mes', 'nombre_mes']].drop_duplicates().sort_values('mes')
            for _, mes in meses_disponibles.iterrows():
                count = len(filtered_data[filtered_data['mes'] == mes['mes']])
                options['meses'].append({
                    'mes': int(mes['mes']) if pd.notna(mes['mes']) else None,
                    'nombre_mes': str(mes['nombre_mes']) if pd.notna(mes['nombre_mes']) else 'N/A',
                    'count': int(count)
                })
        
        # Zonas disponibles
        if 'codigo_zona' in filtered_data.columns and 'nombre_zona' in filtered_data.columns:
            zonas_disponibles = filtered_data[['codigo_zona', 'nombre_zona']].drop_duplicates()
            for _, zona in zonas_disponibles.iterrows():
                count = len(filtered_data[filtered_data['codigo_zona'] == zona['codigo_zona']])
                options['zonas'].append({
                    'zona_id': int(zona['codigo_zona']) if pd.notna(zona['codigo_zona']) else None,
                    'codigo_zona': int(zona['codigo_zona']) if pd.notna(zona['codigo_zona']) else None,
                    'nombre_zona': str(zona['nombre_zona']) if pd.notna(zona['nombre_zona']) else 'N/A',
                    'count': int(count)
                })
        
        # Variedades disponibles
        if 'codigo_variedad' in filtered_data.columns and 'nombre_variedad' in filtered_data.columns:
            variedades_disponibles = filtered_data[['codigo_variedad', 'nombre_variedad']].drop_duplicates()
            for _, variedad in variedades_disponibles.iterrows():
                count = len(filtered_data[filtered_data['codigo_variedad'] == variedad['codigo_variedad']])
                options['variedades'].append({
                    'variedad_id': int(variedad['codigo_variedad']) if pd.notna(variedad['codigo_variedad']) else None,
                    'nombre_variedad': str(variedad['nombre_variedad']) if pd.notna(variedad['nombre_variedad']) else 'N/A',
                    'count': int(count)
                })
        
        # Fincas disponibles (con ranking)
        if 'id_finca' in filtered_data.columns and 'nombre_finca' in filtered_data.columns and 'toneladas_cana_molida' in filtered_data.columns:
            fincas_disponibles = filtered_data.groupby(['id_finca', 'nombre_finca'])['toneladas_cana_molida'].sum().reset_index()
            fincas_disponibles = fincas_disponibles.sort_values('toneladas_cana_molida', ascending=False)
            
            for _, finca in fincas_disponibles.iterrows():
                count = len(filtered_data[filtered_data['id_finca'] == finca['id_finca']])
                options['fincas'].append({
                    'finca_id': int(finca['id_finca']) if pd.notna(finca['id_finca']) else None,
                    'nombre_finca': str(finca['nombre_finca']) if pd.notna(finca['nombre_finca']) else 'N/A',
                    'total_toneladas': float(finca['toneladas_cana_molida']) if pd.notna(finca['toneladas_cana_molida']) else 0.0,
                    'count': int(count)
                })
        
        logger.info(f"Opciones calculadas: {len(options['años'])} años, {len(options['meses'])} meses, {len(options['zonas'])} zonas, {len(options['variedades'])} variedades, {len(options['fincas'])} fincas")
        
        return options
    
    def get_filtered_data(self, filters: Dict[str, Any], limit: int = 1000, group_by_finca: bool = True) -> List[Dict]:
        """Obtiene los datos filtrados, opcionalmente agrupados por finca"""
        if self.base_data is None or self.base_data.empty:
            return []
        
        filtered_data = self.base_data.copy()
        
        if filters.get('año'):
            filtered_data = filtered_data[filtered_data['año'] == filters['año']]
        
        if filters.get('mes'):
            filtered_data = filtered_data[filtered_data['mes'] == filters['mes']]
        
        if filters.get('zona_id'):
            filtered_data = filtered_data[filtered_data['codigo_zona'] == filters['zona_id']]
        
        if filters.get('variedad_id'):
            filtered_data = filtered_data[filtered_data['codigo_variedad'] == filters['variedad_id']]
        
        if filters.get('finca_id'):
            filtered_data = filtered_data[filtered_data['id_finca'] == filters['finca_id']]
        
        # Handle top_fincas filter
        if filters.get('top_fincas'):
            top_n = filters['top_fincas']
            top_fincas_ids = filtered_data.groupby('id_finca')['toneladas_cana_molida'].sum().nlargest(top_n).index
            filtered_data = filtered_data[filtered_data['id_finca'].isin(top_fincas_ids)]
        
        # Agrupar por finca si se solicita (para evitar duplicados en gráficos)
        if group_by_finca and 'id_finca' in filtered_data.columns and 'nombre_finca' in filtered_data.columns:
            # Agrupar por finca y sumar toneladas, promediar otras métricas
            grouped_data = filtered_data.groupby(['id_finca', 'nombre_finca']).agg({
                'toneladas_cana_molida': 'sum',
                'tch': 'mean',
                'brix': 'mean', 
                'sacarosa': 'mean',
                'año': 'first',
                'mes': 'first',
                'nombre_mes': 'first',
                'codigo_zona': 'first',
                'nombre_zona': 'first',
                'codigo_variedad': 'first',
                'nombre_variedad': 'first'
            }).reset_index()
            
            # Crear etiqueta única para la finca
            grouped_data['finca_label'] = grouped_data['nombre_finca'] + ' (' + grouped_data['año'].astype(str) + '/' + grouped_data['mes'].astype(str) + ')'
            
            # Sort and limit
            grouped_data = grouped_data.sort_values('toneladas_cana_molida', ascending=False).head(limit)
            
            return grouped_data.to_dict(orient='records')
        else:
            # Mantener registros individuales (para análisis detallado)
            filtered_data = filtered_data.sort_values('toneladas_cana_molida', ascending=False).head(limit)
            return filtered_data.to_dict(orient='records')