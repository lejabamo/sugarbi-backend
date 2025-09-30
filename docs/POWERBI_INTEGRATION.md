# 🚀 Integración SugarBI con Power BI

## 📋 Descripción

Esta integración permite exportar datos de SugarBI directamente a Power BI para análisis avanzados, manteniendo la estructura OLAP y las relaciones entre tablas.

## 🎯 Características

### ✅ **Funcionalidades Implementadas**

- **Exportación de Datos**: Tablas de hechos y dimensiones en formatos CSV y JSON
- **Esquema OLAP**: Estructura completa del cubo multidimensional
- **Relaciones Predefinidas**: Conexiones entre tablas para modelo de datos perfecto
- **Medidas DAX**: Medidas calculadas predefinidas para análisis
- **Filtros Avanzados**: Por fecha, zona, variedad y finca
- **API REST**: Endpoints específicos para integración

### 🔧 **APIs Disponibles**

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/powerbi/schema` | GET | Obtener esquema del cubo OLAP |
| `/api/powerbi/fact-table` | GET | Exportar tabla de hechos |
| `/api/powerbi/dimensions` | GET | Exportar tablas de dimensiones |
| `/api/powerbi/dataset` | GET | Crear dataset completo |
| `/api/powerbi/analysis` | POST | Análisis OLAP específico |
| `/api/powerbi/export/csv` | GET | Exportar CSV para Power BI |
| `/api/powerbi/export/json` | GET | Exportar JSON para Power BI |

## 🚀 Guía de Uso

### 1. **Acceder a la Interfaz**

```
http://localhost:5001/powerbi
```

### 2. **Obtener Esquema del Cubo**

```bash
curl http://localhost:5001/api/powerbi/schema
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "cube_name": "SugarBI_Cosecha_Cube",
    "description": "Cubo OLAP para análisis de cosecha de caña de azúcar",
    "dimensions": {
      "tiempo": ["year", "quarter", "month", "date"],
      "geografia": ["zone", "farm"],
      "producto": ["variety"]
    },
    "measures": ["toneladas", "tch", "brix", "sacarosa", "area", "rendimiento"],
    "aggregations": ["sum", "avg", "max", "min", "count", "std"]
  }
}
```

### 3. **Exportar Datos con Filtros**

```bash
# Exportar datos de 2024
curl "http://localhost:5001/api/powerbi/fact-table?start_date=2024-01-01&end_date=2024-12-31"

# Exportar datos de zonas específicas
curl "http://localhost:5001/api/powerbi/fact-table?zones=ZONA1,ZONA2"

# Exportar datos de variedades específicas
curl "http://localhost:5001/api/powerbi/fact-table?varieties=VAR1,VAR2"
```

### 4. **Descargar Archivos**

```bash
# Descargar CSV
curl -O "http://localhost:5001/api/powerbi/export/csv"

# Descargar JSON
curl -O "http://localhost:5001/api/powerbi/export/json"
```

## 📊 Estructura de Datos

### **Tabla de Hechos (Fact_Cosecha)**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| fact_id | Int64 | ID único del hecho |
| toneladas | Decimal | Toneladas de caña cosechada |
| tch | Decimal | Toneladas de caña por hectárea |
| brix | Decimal | Grados Brix |
| sacarosa | Decimal | Porcentaje de sacarosa |
| area | Decimal | Área cosechada en hectáreas |
| rendimiento | Decimal | Rendimiento por hectárea |
| fecha_cosecha | DateTime | Fecha de cosecha |
| anio | Int64 | Año |
| trimestre | Int64 | Trimestre |
| mes | Int64 | Mes |
| fecha | DateTime | Fecha completa |
| nombre_finca | String | Nombre de la finca |
| codigo_finca | String | Código de la finca |
| area_finca | Decimal | Área total de la finca |
| nombre_zona | String | Nombre de la zona |
| codigo_zona | String | Código de la zona |
| nombre_variedad | String | Nombre de la variedad |
| codigo_variedad | String | Código de la variedad |
| tipo_cana | String | Tipo de caña |

### **Tablas de Dimensiones**

#### **Dim_Tiempo**
- id, anio, trimestre, mes, fecha, nombre_mes, nombre_trimestre, es_fin_semana, es_feriado

#### **Dim_Finca**
- id, nombre_finca, codigo_finca, area_finca, ubicacion, responsable, telefono, email, nombre_zona, codigo_zona

#### **Dim_Variedad**
- id, nombre_variedad, codigo_variedad, tipo_cana, descripcion, rendimiento_promedio, brix_promedio

#### **Dim_Zona**
- id, nombre_zona, codigo_zona, descripcion, area_total

## 🔗 Relaciones

```sql
Fact_Cosecha[anio] -> Dim_Tiempo[anio]
Fact_Cosecha[codigo_finca] -> Dim_Finca[codigo_finca]
Fact_Cosecha[codigo_variedad] -> Dim_Variedad[codigo_variedad]
Fact_Cosecha[codigo_zona] -> Dim_Zona[codigo_zona]
```

## 📈 Medidas DAX Predefinidas

```dax
Total_Toneladas = SUM(Fact_Cosecha[toneladas])
Promedio_TCH = AVERAGE(Fact_Cosecha[tch])
Promedio_Brix = AVERAGE(Fact_Cosecha[brix])
Total_Area = SUM(Fact_Cosecha[area])
Rendimiento_Promedio = AVERAGE(Fact_Cosecha[rendimiento])
Total_Cosechas = COUNTROWS(Fact_Cosecha)
Max_TCH = MAX(Fact_Cosecha[tch])
Min_TCH = MIN(Fact_Cosecha[tch])
```

## 🎨 Templates de Power BI

### **Dashboard Template**

1. **Resumen Ejecutivo**
   - Cards con métricas principales
   - KPIs de rendimiento

2. **Análisis Temporal**
   - Gráficos de línea por fecha
   - Columnas por año

3. **Análisis Geográfico**
   - Mapas por zona
   - Gráficos de barras por finca

4. **Análisis de Variedades**
   - Gráficos de pastel
   - Scatter plots TCH vs Brix

## 🔧 Configuración Avanzada

### **Variables de Entorno (Opcional)**

```bash
# Para integración con Power BI Service
export POWERBI_TENANT_ID="your-tenant-id"
export POWERBI_CLIENT_ID="your-client-id"
export POWERBI_CLIENT_SECRET="your-client-secret"
export POWERBI_WORKSPACE_ID="your-workspace-id"
```

### **Configuración de Cache**

```python
# En config/powerbi_config.py
CACHE_SETTINGS = {
    "enabled": True,
    "ttl_seconds": 3600,  # 1 hora
    "max_size_mb": 100
}
```

## 📝 Ejemplos de Uso

### **JavaScript/Frontend**

```javascript
// Obtener esquema
async function getSchema() {
    const response = await fetch('/api/powerbi/schema');
    const data = await response.json();
    console.log(data);
}

// Exportar datos con filtros
async function exportData() {
    const params = new URLSearchParams({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        zones: 'ZONA1,ZONA2'
    });
    
    const response = await fetch(`/api/powerbi/fact-table?${params}`);
    const data = await response.json();
    console.log(data);
}

// Descargar CSV
function downloadCSV() {
    window.open('/api/powerbi/export/csv', '_blank');
}
```

### **Python**

```python
import requests
import pandas as pd

# Obtener datos
response = requests.get('http://localhost:5001/api/powerbi/fact-table')
data = response.json()

# Convertir a DataFrame
df = pd.DataFrame(data['data']['data'])

# Análisis básico
print(df.describe())
print(df.groupby('nombre_zona')['toneladas'].sum())
```

## 🚨 Consideraciones Importantes

### **Rendimiento**
- Los datos se exportan en tiempo real
- Para datasets grandes, considera usar filtros de fecha
- El cache está habilitado por defecto (1 hora)

### **Seguridad**
- Requiere autenticación para acceder a los endpoints
- Los datos se filtran según los permisos del usuario
- Se registran todas las exportaciones en logs de auditoría

### **Limitaciones**
- Máximo 1,000,000 filas por exportación
- Los archivos CSV/JSON se generan en memoria
- Para datasets muy grandes, considera usar la API de análisis específico

## 🔄 Actualizaciones Automáticas

### **Power BI Service (Futuro)**

```python
# Configuración para actualizaciones automáticas
POWERBI_SERVICE_CONFIG = {
    "auto_refresh": True,
    "refresh_interval": "1 hour",
    "notify_on_failure": True
}
```

### **Power BI Desktop**

1. Conecta a la API de SugarBI
2. Configura actualización automática
3. Programa refrescos cada hora/día

## 📞 Soporte

- **Documentación**: Este archivo
- **API Reference**: `/api/powerbi/schema`
- **Ejemplos**: Interfaz web en `/powerbi`
- **Logs**: Revisar logs de la aplicación para errores

---

**¡Disfruta analizando tus datos de cosecha con Power BI! 🚀📊**
