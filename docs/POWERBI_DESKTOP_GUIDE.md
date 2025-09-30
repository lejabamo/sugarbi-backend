# 🚀 Guía de Conexión Power BI Desktop con SugarBI

## 📋 Descripción

Esta guía te permite conectar **Power BI Desktop de Microsoft** directamente al datamart de SugarBI para aprovechar toda la potencia de análisis OLAP y visualizaciones avanzadas.

## 🎯 **3 Métodos de Conexión**

### **MÉTODO 1: Conexión Directa MySQL (Recomendado)**

#### **Paso 1: Abrir Power BI Desktop**
1. Abre Power BI Desktop
2. Ve a **Home** > **Get Data** > **Database** > **MySQL database**

#### **Paso 2: Configurar Conexión**
```
Server: localhost
Port: 3306
Database: sugarbi
Username: root
Password: toor
```

#### **Paso 3: Seleccionar Tablas**
Selecciona estas tablas:
- ✅ **hechos_cosecha** (Tabla de hechos principal)
- ✅ **dimtiempo** (Dimensión de tiempo)
- ✅ **dimfinca** (Dimensión de fincas)
- ✅ **dimvariedad** (Dimensión de variedades)
- ✅ **dimzona** (Dimensión de zonas)

#### **Paso 4: Configurar Relaciones**
Power BI detectará automáticamente las relaciones, pero verifica:
```
hechos_cosecha[tiempo_id] -> dimtiempo[id]
hechos_cosecha[finca_id] -> dimfinca[id]
hechos_cosecha[variedad_id] -> dimvariedad[id]
dimfinca[zona_id] -> dimzona[id]
```

---

### **MÉTODO 2: Conexión vía API REST**

#### **Paso 1: Obtener Información de Conexión**
```bash
curl http://localhost:5001/api/powerbi-desktop/connection-info
```

#### **Paso 2: Configurar en Power BI Desktop**
1. **Get Data** > **Web** > **Advanced**
2. **URL**: `http://localhost:5001/api/powerbi-desktop/table/hechos_cosecha`
3. **Headers**: 
   ```json
   {
     "Content-Type": "application/json"
   }
   ```

#### **Paso 3: Repetir para Dimensiones**
- `http://localhost:5001/api/powerbi-desktop/table/dimtiempo`
- `http://localhost:5001/api/powerbi-desktop/table/dimfinca`
- `http://localhost:5001/api/powerbi-desktop/table/dimvariedad`
- `http://localhost:5001/api/powerbi-desktop/table/dimzona`

---

### **MÉTODO 3: Importar Archivos CSV**

#### **Paso 1: Descargar Datos**
```bash
# Descargar tabla de hechos
curl -O "http://localhost:5001/api/powerbi-desktop/export/csv"

# O con filtros específicos
curl -O "http://localhost:5001/api/powerbi-desktop/export/csv?start_date=2024-01-01&end_date=2024-12-31"
```

#### **Paso 2: Importar en Power BI Desktop**
1. **Get Data** > **Text/CSV**
2. Selecciona el archivo descargado
3. Configura tipos de datos automáticamente

---

## 📊 **Configuración del Modelo de Datos**

### **1. Crear Medidas DAX**

```dax
// Medidas básicas
Total_Toneladas = SUM(hechos_cosecha[toneladas])
Promedio_TCH = AVERAGE(hechos_cosecha[tch])
Promedio_Brix = AVERAGE(hechos_cosecha[brix])
Total_Area = SUM(hechos_cosecha[area])
Total_Cosechas = COUNTROWS(hechos_cosecha)

// Medidas avanzadas
Rendimiento_Promedio = AVERAGE(hechos_cosecha[rendimiento])
Max_TCH = MAX(hechos_cosecha[tch])
Min_TCH = MIN(hechos_cosecha[tch])
Desviacion_TCH = STDEV.P(hechos_cosecha[tch])

// Medidas calculadas
Toneladas_por_Zona = 
CALCULATE(
    [Total_Toneladas],
    ALL(dimfinca),
    VALUES(dimzona[nombre_zona])
)

TCH_Promedio_Anual = 
CALCULATE(
    [Promedio_TCH],
    ALL(dimtiempo),
    VALUES(dimtiempo[anio])
)

// Medidas de comparación
TCH_vs_Promedio = 
[Promedio_TCH] - [TCH_Promedio_Anual]

Porcentaje_TCH = 
DIVIDE([Promedio_TCH], [TCH_Promedio_Anual], 0) - 1
```

### **2. Crear Columnas Calculadas**

```dax
// En tabla hechos_cosecha
Trimestre_Texto = 
dimtiempo[nombre_trimestre] & " " & dimtiempo[anio]

Mes_Texto = 
dimtiempo[nombre_mes] & " " & dimtiempo[anio]

Zona_Finca = 
dimfinca[nombre_finca] & " - " & dimzona[nombre_zona]

Variedad_Tipo = 
dimvariedad[nombre_variedad] & " (" & dimvariedad[tipo_cana] & ")"

// Clasificación de rendimiento
Clasificacion_TCH = 
IF(
    hechos_cosecha[tch] >= 120, "Alto",
    IF(
        hechos_cosecha[tch] >= 100, "Medio",
        "Bajo"
    )
)

// Clasificación de Brix
Clasificacion_Brix = 
IF(
    hechos_cosecha[brix] >= 20, "Excelente",
    IF(
        hechos_cosecha[brix] >= 18, "Bueno",
        IF(
            hechos_cosecha[brix] >= 16, "Regular",
            "Bajo"
        )
    )
)
```

### **3. Configurar Jerarquías**

#### **Jerarquía de Tiempo**
```
Tiempo
├── Año
├── Trimestre
└── Mes
```

#### **Jerarquía Geográfica**
```
Geografia
├── Zona
└── Finca
```

#### **Jerarquía de Producto**
```
Producto
├── Tipo de Caña
└── Variedad
```

---

## 🎨 **Crear Visualizaciones**

### **1. Dashboard Ejecutivo**

#### **KPIs Principales**
- **Card**: Total_Toneladas
- **Card**: Promedio_TCH
- **Card**: Promedio_Brix
- **Card**: Total_Cosechas

#### **Gráficos de Tendencias**
- **Line Chart**: TCH por Mes (Eje X: fecha, Eje Y: Promedio_TCH)
- **Column Chart**: Toneladas por Año (Eje X: anio, Eje Y: Total_Toneladas)

### **2. Análisis Geográfico**

#### **Mapas y Distribución**
- **Map**: Toneladas por Zona (Location: nombre_zona, Size: Total_Toneladas)
- **Bar Chart**: Top 10 Fincas por TCH (Eje X: nombre_finca, Eje Y: Promedio_TCH)
- **Pie Chart**: Distribución por Zona (Legend: nombre_zona, Values: Total_Toneladas)

### **3. Análisis de Variedades**

#### **Comparación de Variedades**
- **Scatter Chart**: TCH vs Brix (Eje X: Promedio_TCH, Eje Y: Promedio_Brix, Legend: nombre_variedad)
- **Bar Chart**: Rendimiento por Variedad (Eje X: nombre_variedad, Eje Y: Promedio_TCH)
- **Table**: Ranking de Variedades (Columnas: nombre_variedad, Promedio_TCH, Promedio_Brix, Total_Toneladas)

### **4. Análisis Temporal Avanzado**

#### **Tendencias y Estacionalidad**
- **Line Chart**: TCH por Trimestre (Eje X: trimestre, Eje Y: Promedio_TCH, Legend: anio)
- **Area Chart**: Toneladas Acumuladas (Eje X: fecha, Eje Y: Total_Toneladas)
- **Heatmap**: TCH por Mes y Zona (Eje X: nombre_mes, Eje Y: nombre_zona, Values: Promedio_TCH)

---

## 🔧 **Configuración Avanzada**

### **1. Filtros Interactivos**

#### **Filtros de Página**
- **Slicer**: Año (dimtiempo[anio])
- **Slicer**: Zona (dimzona[nombre_zona])
- **Slicer**: Variedad (dimvariedad[nombre_variedad])
- **Slicer**: Tipo de Caña (dimvariedad[tipo_cana])

#### **Filtros de Visual**
- **Top N**: Top 10 fincas por TCH
- **Relative Date**: Últimos 12 meses
- **Advanced**: Filtros personalizados por rango

### **2. Botones y Navegación**

#### **Botones de Navegación**
- **Button**: "Dashboard Ejecutivo"
- **Button**: "Análisis Geográfico"
- **Button**: "Análisis de Variedades"
- **Button**: "Análisis Temporal"

### **3. Tooltips Avanzados**

#### **Tooltip Personalizado**
```dax
// Medida para tooltip
Tooltip_Info = 
"Finca: " & dimfinca[nombre_finca] & 
"\nZona: " & dimzona[nombre_zona] & 
"\nVariedad: " & dimvariedad[nombre_variedad] & 
"\nTCH: " & FORMAT([Promedio_TCH], "0.00") & 
"\nBrix: " & FORMAT([Promedio_Brix], "0.00")
```

---

## 📈 **Análisis OLAP Avanzado**

### **1. Operaciones Drill-Down**

#### **Drill-Down Geográfico**
```
Zona → Finca → Detalle de Cosecha
```

#### **Drill-Down Temporal**
```
Año → Trimestre → Mes → Fecha
```

#### **Drill-Down de Producto**
```
Tipo de Caña → Variedad → Características
```

### **2. Análisis de Segmentación**

#### **Segmentación por Rendimiento**
```dax
Segmento_Rendimiento = 
IF(
    [Promedio_TCH] >= 120, "Alto Rendimiento",
    IF(
        [Promedio_TCH] >= 100, "Rendimiento Medio",
        "Bajo Rendimiento"
    )
)
```

#### **Segmentación por Calidad**
```dax
Segmento_Calidad = 
IF(
    [Promedio_Brix] >= 20, "Alta Calidad",
    IF(
        [Promedio_Brix] >= 18, "Calidad Media",
        "Calidad Baja"
    )
)
```

### **3. Análisis de Correlación**

#### **Correlación TCH vs Brix**
```dax
Correlacion_TCH_Brix = 
CORREL(hechos_cosecha[tch], hechos_cosecha[brix])
```

---

## 🚀 **Automatización y Actualización**

### **1. Configurar Actualización Automática**

#### **En Power BI Desktop**
1. **File** > **Options and Settings** > **Data Source Settings**
2. Selecciona tu fuente de datos
3. **Edit Permissions** > **Use my current credentials**
4. Configura **Refresh** automático

#### **En Power BI Service (Opcional)**
1. Publica tu reporte en Power BI Service
2. Configura **Scheduled Refresh**
3. Establece frecuencia: Cada hora/día

### **2. Configurar Gateway (Para Producción)**

#### **Power BI Gateway**
1. Instala **On-premises data gateway**
2. Configura conexión a tu servidor MySQL
3. Conecta Power BI Service con tu gateway

---

## 📊 **Ejemplos de Consultas Avanzadas**

### **1. Análisis de Tendencias**

```dax
// TCH con tendencia
TCH_Tendencia = 
VAR CurrentTCH = [Promedio_TCH]
VAR PreviousTCH = 
    CALCULATE(
        [Promedio_TCH],
        DATEADD(dimtiempo[fecha], -1, MONTH)
    )
RETURN
    CurrentTCH - PreviousTCH
```

### **2. Análisis de Estacionalidad**

```dax
// TCH promedio por mes
TCH_Promedio_Mensual = 
CALCULATE(
    [Promedio_TCH],
    ALL(dimtiempo),
    VALUES(dimtiempo[mes])
)

// Desviación del promedio mensual
Desviacion_Mensual = 
[Promedio_TCH] - [TCH_Promedio_Mensual]
```

### **3. Análisis de Performance**

```dax
// Ranking de fincas
Ranking_Fincas = 
RANKX(
    ALL(dimfinca[nombre_finca]),
    [Promedio_TCH],
    ,
    DESC
)

// Percentil de TCH
Percentil_TCH = 
PERCENTILE.INC(
    hechos_cosecha[tch],
    0.5
)
```

---

## 🔍 **Troubleshooting**

### **Problemas Comunes**

#### **1. Error de Conexión**
- Verifica que MySQL esté ejecutándose
- Confirma credenciales de acceso
- Revisa firewall y puertos

#### **2. Datos No Actualizados**
- Refresca la conexión en Power BI
- Verifica que los datos estén en la base de datos
- Revisa filtros aplicados

#### **3. Rendimiento Lento**
- Usa filtros de fecha para limitar datos
- Optimiza consultas DAX
- Considera usar tablas calculadas

### **Logs y Debugging**

#### **Verificar Conexión**
```bash
# Probar conexión a la API
curl http://localhost:5001/api/powerbi-desktop/connection-info

# Verificar datos
curl http://localhost:5001/api/powerbi-desktop/table/hechos_cosecha
```

---

## 🎯 **Próximos Pasos**

1. **Conecta Power BI Desktop** usando el Método 1 (MySQL directo)
2. **Configura el modelo de datos** con las relaciones
3. **Crea las medidas DAX** básicas
4. **Desarrolla visualizaciones** paso a paso
5. **Configura filtros** y navegación
6. **Optimiza rendimiento** según necesidades

---

**¡Disfruta analizando tus datos de cosecha con toda la potencia de Power BI! 🚀📊**
