"""
Configuración específica para integración con Power BI
"""

import os
from pathlib import Path

class PowerBIConfig:
    """Configuración para Power BI"""
    
    # Configuración de exportación
    EXPORT_FORMATS = ['csv', 'json', 'xlsx']
    MAX_ROWS_PER_EXPORT = 1000000
    DEFAULT_DATE_FORMAT = '%Y-%m-%d'
    
    # Configuración de columnas para Power BI
    POWERBI_COLUMN_TYPES = {
        'Int64': 'Whole Number',
        'Decimal': 'Decimal Number',
        'String': 'Text',
        'DateTime': 'Date/Time',
        'Boolean': 'True/False'
    }
    
    # Medidas calculadas predefinidas
    DEFAULT_MEASURES = [
        {
            "name": "Total_Toneladas",
            "expression": "SUM(Fact_Cosecha[toneladas])",
            "description": "Suma total de toneladas de caña cosechada",
            "format": "0.00"
        },
        {
            "name": "Promedio_TCH",
            "expression": "AVERAGE(Fact_Cosecha[tch])",
            "description": "Promedio de toneladas de caña por hectárea",
            "format": "0.00"
        },
        {
            "name": "Promedio_Brix",
            "expression": "AVERAGE(Fact_Cosecha[brix])",
            "description": "Promedio de grados Brix",
            "format": "0.00"
        },
        {
            "name": "Total_Area",
            "expression": "SUM(Fact_Cosecha[area])",
            "description": "Suma total de área cosechada",
            "format": "0.00"
        },
        {
            "name": "Rendimiento_Promedio",
            "expression": "AVERAGE(Fact_Cosecha[rendimiento])",
            "description": "Rendimiento promedio por hectárea",
            "format": "0.00"
        },
        {
            "name": "Total_Cosechas",
            "expression": "COUNTROWS(Fact_Cosecha)",
            "description": "Número total de cosechas",
            "format": "0"
        },
        {
            "name": "Max_TCH",
            "expression": "MAX(Fact_Cosecha[tch])",
            "description": "Máximo TCH registrado",
            "format": "0.00"
        },
        {
            "name": "Min_TCH",
            "expression": "MIN(Fact_Cosecha[tch])",
            "description": "Mínimo TCH registrado",
            "format": "0.00"
        }
    ]
    
    # Relaciones predefinidas
    DEFAULT_RELATIONSHIPS = [
        {
            "from_table": "Fact_Cosecha",
            "from_column": "anio",
            "to_table": "Dim_Tiempo",
            "to_column": "anio",
            "type": "ManyToOne",
            "description": "Relación entre hechos y dimensión de tiempo por año"
        },
        {
            "from_table": "Fact_Cosecha",
            "from_column": "codigo_finca",
            "to_table": "Dim_Finca",
            "to_column": "codigo_finca",
            "type": "ManyToOne",
            "description": "Relación entre hechos y dimensión de finca"
        },
        {
            "from_table": "Fact_Cosecha",
            "from_column": "codigo_variedad",
            "to_table": "Dim_Variedad",
            "to_column": "codigo_variedad",
            "type": "ManyToOne",
            "description": "Relación entre hechos y dimensión de variedad"
        },
        {
            "from_table": "Fact_Cosecha",
            "from_column": "codigo_zona",
            "to_table": "Dim_Zona",
            "to_column": "codigo_zona",
            "type": "ManyToOne",
            "description": "Relación entre hechos y dimensión de zona"
        }
    ]
    
    # Configuración de filtros por defecto
    DEFAULT_FILTERS = {
        "date_range": {
            "start_date": "2020-01-01",
            "end_date": "2025-12-31"
        },
        "zones": [],  # Todas las zonas
        "varieties": [],  # Todas las variedades
        "farms": []  # Todas las fincas
    }
    
    # Configuración de exportación
    EXPORT_SETTINGS = {
        "csv": {
            "delimiter": ",",
            "encoding": "utf-8",
            "include_headers": True
        },
        "json": {
            "indent": 2,
            "ensure_ascii": False
        },
        "xlsx": {
            "sheet_name": "SugarBI_Data",
            "include_headers": True
        }
    }
    
    # Configuración de cache
    CACHE_SETTINGS = {
        "enabled": True,
        "ttl_seconds": 3600,  # 1 hora
        "max_size_mb": 100
    }
    
    @classmethod
    def get_export_path(cls):
        """Obtener ruta para archivos de exportación"""
        export_dir = Path(__file__).parent.parent / "exports"
        export_dir.mkdir(exist_ok=True)
        return export_dir
    
    @classmethod
    def get_cache_path(cls):
        """Obtener ruta para archivos de cache"""
        cache_dir = Path(__file__).parent.parent / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

# Configuración de Power BI Service (si se usa Power BI Service)
class PowerBIServiceConfig:
    """Configuración para Power BI Service"""
    
    # Estas configuraciones se usarían si se integra con Power BI Service
    TENANT_ID = os.getenv('POWERBI_TENANT_ID', '')
    CLIENT_ID = os.getenv('POWERBI_CLIENT_ID', '')
    CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET', '')
    WORKSPACE_ID = os.getenv('POWERBI_WORKSPACE_ID', '')
    
    # URLs de Power BI Service
    POWERBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"
    AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    @classmethod
    def is_configured(cls):
        """Verificar si Power BI Service está configurado"""
        return all([
            cls.TENANT_ID,
            cls.CLIENT_ID,
            cls.CLIENT_SECRET,
            cls.WORKSPACE_ID
        ])

# Configuración de templates para Power BI
POWERBI_TEMPLATES = {
    "dashboard_template": {
        "name": "SugarBI Dashboard Template",
        "description": "Template base para dashboard de SugarBI",
        "pages": [
            {
                "name": "Resumen Ejecutivo",
                "visuals": [
                    {"type": "card", "measure": "Total_Toneladas"},
                    {"type": "card", "measure": "Promedio_TCH"},
                    {"type": "card", "measure": "Promedio_Brix"},
                    {"type": "card", "measure": "Total_Cosechas"}
                ]
            },
            {
                "name": "Análisis Temporal",
                "visuals": [
                    {"type": "line_chart", "x_axis": "fecha", "y_axis": "toneladas"},
                    {"type": "column_chart", "x_axis": "anio", "y_axis": "Total_Toneladas"}
                ]
            },
            {
                "name": "Análisis Geográfico",
                "visuals": [
                    {"type": "map", "location": "nombre_zona", "size": "Total_Toneladas"},
                    {"type": "bar_chart", "x_axis": "nombre_zona", "y_axis": "Promedio_TCH"}
                ]
            },
            {
                "name": "Análisis de Variedades",
                "visuals": [
                    {"type": "pie_chart", "legend": "nombre_variedad", "values": "Total_Toneladas"},
                    {"type": "scatter_chart", "x_axis": "Promedio_TCH", "y_axis": "Promedio_Brix", "legend": "nombre_variedad"}
                ]
            }
        ]
    }
}
