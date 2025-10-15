"""
Motor de visualizaciones para SugarBI
Genera gráficos y visualizaciones basadas en datos de consultas
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ChartType(Enum):
    """Tipos de gráficos disponibles"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    TABLE = "table"
    HEATMAP = "heatmap"

@dataclass
class ChartConfig:
    """Configuración para un gráfico"""
    chart_type: ChartType
    title: str
    x_axis: str
    y_axis: str
    data: List[Dict[str, Any]]
    colors: Optional[List[str]] = None
    width: int = 800
    height: int = 400
    show_legend: bool = True
    show_grid: bool = True

class VisualizationEngine:
    """Motor principal para generar visualizaciones"""
    
    def __init__(self):
        self.chart_templates = {
            ChartType.BAR: self._create_bar_chart,
            ChartType.LINE: self._create_line_chart,
            ChartType.PIE: self._create_pie_chart,
            ChartType.TABLE: self._create_table,
            ChartType.AREA: self._create_area_chart
        }
        
        # Colores por defecto
        self.default_colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]

    def create_visualization(self, config: ChartConfig) -> Dict[str, Any]:
        """
        Crea una visualización basada en la configuración
        
        Args:
            config: Configuración del gráfico
            
        Returns:
            Dict con la configuración del gráfico para Chart.js
        """
        if config.chart_type in self.chart_templates:
            return self.chart_templates[config.chart_type](config)
        else:
            raise ValueError(f"Tipo de gráfico no soportado: {config.chart_type}")

    def _create_bar_chart(self, config: ChartConfig) -> Dict[str, Any]:
        """Crea configuración para gráfico de barras"""
        if not config.data:
            return {"type": "bar", "data": {"labels": [], "datasets": []}}
        
        # Obtener las columnas reales de los datos
        available_columns = list(config.data[0].keys())
        
        # Encontrar columna X (etiquetas)
        x_column = self._find_column(available_columns, config.x_axis, ['nombre', 'finca', 'variedad', 'zona'])
        if not x_column:
            x_column = available_columns[0]
        
        # Encontrar columna Y (valores)
        y_column = self._find_column(available_columns, config.y_axis, ['total', 'promedio', 'sum', 'avg'])
        if not y_column:
            y_column = available_columns[1] if len(available_columns) > 1 else available_columns[0]
        
        labels = [str(item[x_column]) for item in config.data]
        values = [item[y_column] for item in config.data]
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": y_column.replace('_', ' ').title(),
                    "data": values,
                    "backgroundColor": config.colors or self.default_colors[:len(values)],
                    "borderColor": config.colors or self.default_colors[:len(values)],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": config.title
                    },
                    "legend": {
                        "display": config.show_legend
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "grid": {
                            "display": config.show_grid
                        }
                    },
                    "x": {
                        "grid": {
                            "display": config.show_grid
                        }
                    }
                }
            }
        }

    def _create_line_chart(self, config: ChartConfig) -> Dict[str, Any]:
        """Crea configuración para gráfico de líneas"""
        labels = [str(item[config.x_axis]) for item in config.data]
        values = [item[config.y_axis] for item in config.data]
        
        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": config.y_axis.replace('_', ' ').title(),
                    "data": values,
                    "borderColor": config.colors[0] if config.colors else self.default_colors[0],
                    "backgroundColor": (config.colors[0] if config.colors else self.default_colors[0]) + "20",
                    "fill": False,
                    "tension": 0.1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": config.title
                    },
                    "legend": {
                        "display": config.show_legend
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "grid": {
                            "display": config.show_grid
                        }
                    },
                    "x": {
                        "grid": {
                            "display": config.show_grid
                        }
                    }
                }
            }
        }

    def _create_pie_chart(self, config: ChartConfig) -> Dict[str, Any]:
        """Crea configuración para gráfico de pastel"""
        if not config.data:
            return {"type": "pie", "data": {"labels": [], "datasets": []}}
        
        # Obtener las columnas reales de los datos
        available_columns = list(config.data[0].keys())
        
        # Encontrar columna X (etiquetas)
        x_column = self._find_column(available_columns, config.x_axis, ['nombre', 'finca', 'variedad', 'zona'])
        if not x_column:
            x_column = available_columns[0]
        
        # Encontrar columna Y (valores)
        y_column = self._find_column(available_columns, config.y_axis, ['total', 'promedio', 'sum', 'avg'])
        if not y_column:
            y_column = available_columns[1] if len(available_columns) > 1 else available_columns[0]
        
        labels = [str(item[x_column]) for item in config.data]
        values = [item[y_column] for item in config.data]
        
        return {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": config.colors or self.default_colors[:len(values)],
                    "borderColor": "#fff",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": config.title
                    },
                    "legend": {
                        "display": config.show_legend,
                        "position": "right"
                    }
                }
            }
        }

    def _create_area_chart(self, config: ChartConfig) -> Dict[str, Any]:
        """Crea configuración para gráfico de área"""
        labels = [str(item[config.x_axis]) for item in config.data]
        values = [item[config.y_axis] for item in config.data]
        
        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": config.y_axis.replace('_', ' ').title(),
                    "data": values,
                    "borderColor": config.colors[0] if config.colors else self.default_colors[0],
                    "backgroundColor": (config.colors[0] if config.colors else self.default_colors[0]) + "40",
                    "fill": True,
                    "tension": 0.1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": config.title
                    },
                    "legend": {
                        "display": config.show_legend
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "grid": {
                            "display": config.show_grid
                        }
                    },
                    "x": {
                        "grid": {
                            "display": config.show_grid
                        }
                    }
                }
            }
        }

    def _create_table(self, config: ChartConfig) -> Dict[str, Any]:
        """Crea configuración para tabla de datos"""
        return {
            "type": "table",
            "title": config.title,
            "data": config.data,
            "columns": list(config.data[0].keys()) if config.data else []
        }

    def suggest_chart_type(self, data: List[Dict[str, Any]], x_axis: str, y_axis: str) -> ChartType:
        """
        Sugiere el tipo de gráfico más apropiado basado en los datos
        
        Args:
            data: Datos a visualizar
            x_axis: Columna del eje X (puede ser el nombre de la dimensión)
            y_axis: Columna del eje Y (puede ser el nombre de la métrica)
            
        Returns:
            ChartType sugerido
        """
        if not data:
            return ChartType.TABLE
        
        # Obtener las columnas reales de los datos
        available_columns = list(data[0].keys()) if data else []
        
        # Encontrar la columna X apropiada
        x_column = None
        for col in available_columns:
            if x_axis.lower() in col.lower() or any(keyword in col.lower() for keyword in ['nombre', 'finca', 'variedad', 'zona']):
                x_column = col
                break
        
        # Si no se encuentra, usar la primera columna que no sea numérica
        if not x_column:
            for col in available_columns:
                if not any(keyword in col.lower() for keyword in ['total', 'promedio', 'sum', 'avg', 'count']):
                    x_column = col
                    break
        
        # Si el eje X parece ser temporal, usar línea
        if x_column and any(keyword in x_column.lower() for keyword in ['año', 'mes', 'fecha', 'tiempo']):
            return ChartType.LINE
        
        # Si hay pocos elementos, usar gráfico de pastel
        if len(data) <= 5:
            return ChartType.PIE
        
        # Si hay muchos elementos, usar barras
        if len(data) > 10:
            return ChartType.BAR
        
        # Por defecto, usar barras
        return ChartType.BAR

    def _find_column(self, available_columns: List[str], target_name: str, keywords: List[str]) -> Optional[str]:
        """
        Encuentra la columna más apropiada basada en el nombre objetivo y palabras clave
        
        Args:
            available_columns: Lista de columnas disponibles
            target_name: Nombre objetivo a buscar
            keywords: Palabras clave adicionales
            
        Returns:
            Nombre de la columna encontrada o None
        """
        # Buscar coincidencia exacta o parcial
        for col in available_columns:
            if target_name.lower() in col.lower():
                return col
        
        # Buscar por palabras clave
        for col in available_columns:
            if any(keyword in col.lower() for keyword in keywords):
                return col
        
        return None

    def create_dashboard_layout(self, visualizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un layout de dashboard con múltiples visualizaciones
        
        Args:
            visualizations: Lista de configuraciones de gráficos
            
        Returns:
            Dict con el layout del dashboard
        """
        return {
            "layout": "grid",
            "columns": 2,
            "visualizations": visualizations,
            "title": "Dashboard SugarBI",
            "timestamp": "2025-09-06"
        }

# Ejemplo de uso
if __name__ == "__main__":
    engine = VisualizationEngine()
    
    # Datos de ejemplo
    sample_data = [
        {"finca": "Finca A", "toneladas": 1500},
        {"finca": "Finca B", "toneladas": 1200},
        {"finca": "Finca C", "toneladas": 900},
        {"finca": "Finca D", "toneladas": 800}
    ]
    
    # Configuración del gráfico
    config = ChartConfig(
        chart_type=ChartType.BAR,
        title="Top Fincas por Producción",
        x_axis="finca",
        y_axis="toneladas",
        data=sample_data
    )
    
    # Crear visualización
    chart_config = engine.create_visualization(config)
    print("Configuración del gráfico:")
    print(json.dumps(chart_config, indent=2, ensure_ascii=False))
