# 🤖 SugarBI Chatbot Architecture

## 📋 Tabla de Contenidos
- [Visión General](#visión-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Filtros Inteligentes](#filtros-inteligentes)
- [Proceso del Chatbot](#proceso-del-chatbot)
- [Análisis OLAP](#análisis-olap)
- [Flujo de Datos](#flujo-de-datos)
- [Componentes Técnicos](#componentes-técnicos)
- [APIs y Endpoints](#apis-y-endpoints)

## 🎯 Visión General

SugarBI Chatbot es un sistema inteligente de análisis de datos agrícolas que combina procesamiento de lenguaje natural (NLP), filtros reactivos y análisis multidimensional (OLAP) para proporcionar insights sobre la producción de caña de azúcar.

### Características Principales:
- **Chatbot Inteligente**: Procesamiento de consultas en lenguaje natural
- **Filtros Reactivos**: Sistema de filtros que se adapta dinámicamente
- **Análisis OLAP**: Operaciones multidimensionales avanzadas
- **Visualizaciones Dinámicas**: Gráficos interactivos y exportación de datos

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        SUGARBI ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript)                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   Dashboard     │ │    Chatbot      │ │   OLAP Analytics│   │
│  │   - Filtros     │ │   - NLP Query   │ │   - 3D Cube     │   │
│  │   - Gráficos    │ │   - Visualiz.   │ │   - Wizard      │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Backend (Flask + Python)                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  Smart Filters  │ │  Chatbot Engine │ │   OLAP Engine   │   │
│  │  - Intersecciones│ │  - LangChain    │ │   - Drill-down  │   │
│  │  - Validación   │ │  - SQL Gen      │ │   - Aggregations│   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer (MySQL)                                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   Data Mart     │ │   Hechos        │ │   Dimensiones   │   │
│  │   - Cosechas    │ │   - Producción  │ │   - Fincas      │   │
│  │   - Calidad     │ │   - Toneladas   │ │   - Variedades  │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Filtros Inteligentes

### Concepto
Los Filtros Inteligentes son un sistema reactivo que calcula dinámicamente las opciones disponibles basándose en las selecciones previas, asegurando que solo se muestren combinaciones válidas de datos.

### Arquitectura de Filtros

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE FILTROS INTELIGENTES              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Usuario   │───▶│  Frontend   │───▶│  Backend    │         │
│  │  Selecciona │    │  Smart      │    │  Filter     │         │
│  │  Filtros    │    │  Filters    │    │  Manager    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Intersecciones│      │
│         │                   │            │ Calculator   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │   Base      │        │
│         │                   │            │   Data      │        │
│         │                   │            │   Loader    │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │   MySQL     │        │
│         │                   │            │  Database   │        │
│         │                   │            └─────────────┘        │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │ Opciones    │                            │
│         │            │ Filtradas   │                            │
│         │            │ Disponibles │                            │
│         │            └─────────────┘                            │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │  Dashboard  │                            │
│         │            │  Actualizado│                            │
│         │            └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Filtros Inteligentes

```
1. Usuario selecciona AÑO (ej: 2025)
   │
   ▼
2. Sistema calcula MESES disponibles para 2025
   │
   ▼
3. Usuario selecciona MES (ej: Enero)
   │
   ▼
4. Sistema calcula ZONAS disponibles para 2025/Enero
   │
   ▼
5. Usuario selecciona ZONA (ej: Zona 2)
   │
   ▼
6. Sistema calcula VARIEDADES disponibles para 2025/Enero/Zona2
   │
   ▼
7. Usuario selecciona VARIEDAD (ej: CC 11-600)
   │
   ▼
8. Sistema calcula FINCAS disponibles para la combinación completa
   │
   ▼
9. Dashboard se actualiza con datos filtrados
```

### Estados de Filtros

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESTADOS DE FILTROS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🟢 SELECCIONADO    - Filtro activo con valor específico       │
│  🟠 DISPONIBLE      - Opciones válidas para seleccionar        │
│  🔴 BLOQUEADO       - Opciones no disponibles (sin datos)      │
│                                                                 │
│  Ejemplo de Estados:                                           │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐           │
│  │  AÑO    │  MES    │  ZONA   │VARIEDAD │ FINCA   │           │
│  ├─────────┼─────────┼─────────┼─────────┼─────────┤           │
│  │ 🟢 2025 │ 🟢 Ene  │ 🟢 Z2   │ 🟢 CC11 │ 🟠 F050 │           │
│  │         │         │         │         │ 🟠 F139 │           │
│  │         │         │         │         │ 🟠 F177 │           │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🤖 Proceso del Chatbot

### Arquitectura del Chatbot

```
┌─────────────────────────────────────────────────────────────────┐
│                        CHATBOT ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Usuario   │───▶│  Frontend   │───▶│  Backend    │         │
│  │  Escribe    │    │  Chat UI    │    │  Chat API   │         │
│  │  Consulta   │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Query       │        │
│         │                   │            │ Parser      │        │
│         │                   │            │ (NLP)       │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ SQL         │        │
│         │                   │            │ Generator   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Database    │        │
│         │                   │            │ Query       │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Response    │        │
│         │                   │            │ Generator   │        │
│         │                   │            │ (LangChain) │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Natural     │        │
│         │                   │            │ Language    │        │
│         │                   │            │ Response    │        │
│         │                   │            └─────────────┘        │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │ Visualización│                           │
│         │            │ + Respuesta  │                           │
│         │            │ Textual      │                           │
│         │            └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Procesamiento del Chatbot

```
1. Usuario: "¿Cuál es la finca más productiva en enero 2025?"
   │
   ▼
2. Query Parser (NLP):
   - Detecta: QueryType.TOP_RANKING
   - Detecta: Metric.TONELADAS
   - Detecta: Dimension.FINCA
   - Detecta: Filters: {año: 2025, mes: 1}
   │
   ▼
3. SQL Generator:
   - Genera: SELECT f.nombre_finca, SUM(h.toneladas_cana_molida) as total
             FROM hechos_cosecha h
             JOIN dim_finca f ON h.id_finca = f.id_finca
             WHERE h.año = 2025 AND h.mes = 1
             GROUP BY f.id_finca, f.nombre_finca
             ORDER BY total DESC LIMIT 1
   │
   ▼
4. Database Query:
   - Ejecuta SQL en MySQL
   - Retorna: [{"nombre_finca": "Finca_050", "total": 2300.5}]
   │
   ▼
5. Response Generator:
   - Genera respuesta natural: "La finca más productiva en enero 2025 es Finca_050 con 2,300.5 toneladas"
   - Crea datos para gráfico: {labels: ["Finca_050"], data: [2300.5]}
   │
   ▼
6. Frontend:
   - Muestra respuesta textual en verde
   - Renderiza gráfico de barras
   - Destaca barra máxima en verde
```

### Tipos de Consultas Soportadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIPOS DE CONSULTAS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 TOP RANKING                                                 │
│  "¿Cuáles son las 5 mejores fincas por producción?"            │
│  "Top 10 variedades con mayor TCH"                             │
│                                                                 │
│  📈 TENDENCIAS                                                  │
│  "Muestra la producción por año"                               │
│  "Evolución de toneladas por mes en 2025"                      │
│                                                                 │
│  📋 ESTADÍSTICAS                                                │
│  "¿Cuál es el promedio de producción?"                         │
│  "Muestra el total de toneladas por zona"                      │
│                                                                 │
│  🔍 DISTRIBUCIÓN                                                │
│  "Distribución de producción por variedad"                     │
│  "Producción por zona en 2024"                                 │
│                                                                 │
│  🎯 COMPARACIONES                                               │
│  "Compara la producción entre 2024 y 2025"                     │
│  "Diferencias entre zonas 1 y 2"                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Análisis OLAP

### Concepto
El análisis OLAP (Online Analytical Processing) permite realizar operaciones multidimensionales sobre los datos, incluyendo drill-down, roll-up, slice, dice y pivot.

### Arquitectura OLAP

```
┌─────────────────────────────────────────────────────────────────┐
│                        OLAP ENGINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Usuario   │───▶│  Frontend   │───▶│  Backend    │         │
│  │  Configura  │    │  OLAP       │    │  OLAP       │         │
│  │  Análisis   │    │  Wizard     │    │  Engine     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Metric      │        │
│         │                   │            │ Selection   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Dimension   │        │
│         │                   │            │ Selection   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ Aggregation │        │
│         │                   │            │ Functions   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ SQL Query   │        │
│         │                   │            │ Generator   │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │ 3D Cube     │        │
│         │                   │            │ Visualization│       │
│         │                   │            └─────────────┘        │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │ Results     │                            │
│         │            │ Table +     │                            │
│         │            │ Export      │                            │
│         │            └─────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Wizard de Configuración OLAP

```
┌─────────────────────────────────────────────────────────────────┐
│                    OLAP CONFIGURATION WIZARD                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: SELECCIÓN DE MÉTRICAS                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🎯 Toneladas    📊 TCH        🍯 Brix                  │   │
│  │  🏭 Sacarosa     📏 Área       📈 Producción            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PASO 2: SELECCIÓN DE DIMENSIONES                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🏢 Fincas       🌱 Variedades  🌍 Zonas               │   │
│  │  📅 Tiempo       📊 Calidad     📈 Producción          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PASO 3: FUNCIONES DE AGREGACIÓN                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ➕ SUM          📊 AVG         🔢 COUNT                │   │
│  │  📈 MAX          📉 MIN         📊 STDDEV               │   │
│  │  📊 VARIANCE     📊 MEDIAN      🔄 PIVOT                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PASO 4: VISUALIZACIÓN 3D                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🧊 Cubo 3D Interactivo                               │   │
│  │  - Rotación con mouse                                 │   │
│  │  - Drill-down en caras                                │   │
│  │  - Slice & Dice                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Operaciones OLAP Soportadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPERACIONES OLAP                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍 DRILL-DOWN                                                   │
│  De Año → Mes → Día                                             │
│  De Zona → Finca → Variedad                                     │
│                                                                 │
│  📈 ROLL-UP                                                      │
│  De Día → Mes → Año                                             │
│  De Variedad → Finca → Zona                                     │
│                                                                 │
│  ✂️ SLICE                                                        │
│  Filtrar por una dimensión específica                           │
│  Ej: Solo datos de 2025                                         │
│                                                                 │
│  🎲 DICE                                                        │
│  Filtrar por múltiples dimensiones                              │
│  Ej: Zona 1 + Enero 2025                                       │
│                                                                 │
│  🔄 PIVOT                                                       │
│  Cambiar orientación de dimensiones                             │
│  Filas ↔ Columnas                                               │
│                                                                 │
│  📊 AGGREGATIONS                                                │
│  SUM, AVG, COUNT, MAX, MIN, STDDEV, VARIANCE, MEDIAN           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos

### Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS COMPLETO                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CARGA INICIAL                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Frontend  │───▶│   Backend   │───▶│  Database   │         │
│  │  Carga      │    │  Loads      │    │  Returns    │         │
│  │  Dashboard  │    │  Base Data  │    │  Raw Data   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Smart      │    │  Filter     │    │  Processed  │         │
│  │  Filters    │    │  Manager    │    │  Data       │         │
│  │  Ready      │    │  Initialized│    │  Cached     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                 │
│  2. INTERACCIÓN DEL USUARIO                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Usuario   │───▶│  Frontend   │───▶│  Backend    │         │
│  │  Interacts  │    │  Processes  │    │  Processes  │         │
│  │  (Filter/   │    │  Request    │    │  Request    │         │
│  │   Query)    │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │  Database   │        │
│         │                   │            │  Query      │        │
│         │                   │            └─────────────┘        │
│         │                   │                   │               │
│         │                   │                   ▼               │
│         │                   │            ┌─────────────┐        │
│         │                   │            │  Results    │        │
│         │                   │            │  Processing │        │
│         │                   │            └─────────────┘        │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │  Response   │                            │
│         │            │  Generation │                            │
│         │            └─────────────┘                            │
│         │                   │                                   │
│         │                   ▼                                   │
│         │            ┌─────────────┐                            │
│         │            │  Frontend   │                            │
│         │            │  Update     │                            │
│         │            └─────────────┘                            │
│                                                                 │
│  3. VISUALIZACIÓN                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Charts     │    │  Tables     │    │  Export     │         │
│  │  Generated  │    │  Populated  │    │  Options    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Componentes Técnicos

### Backend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND COMPONENTS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📁 chatbot/                                                    │
│  ├── langchain_chatbot.py      # Motor principal del chatbot   │
│  ├── query_parser.py           # Parser de consultas NLP       │
│  └── sql_generator.py          # Generador de consultas SQL    │
│                                                                 │
│  📁 filter_intersections.py                                    │
│  ├── FilterManager             # Gestor de filtros inteligentes│
│  ├── load_base_data()          # Carga datos base              │
│  ├── calculate_intersections() # Calcula intersecciones        │
│  └── get_filtered_data()       # Obtiene datos filtrados       │
│                                                                 │
│  📁 dashboard/                                                  │
│  ├── olap_engine.py            # Motor OLAP                    │
│  ├── visualization_engine.py   # Motor de visualizaciones      │
│  └── powerbi_connector.py      # Conector Power BI             │
│                                                                 │
│  📁 web/                                                        │
│  ├── app.py                    # Aplicación Flask principal    │
│  ├── routes.py                 # Rutas de la API               │
│  └── config.py                 # Configuración                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND COMPONENTS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📁 src/components/                                             │
│  ├── SmartFilters.tsx          # Filtros inteligentes          │
│  ├── Chart.tsx                 # Componente de gráficos        │
│  ├── ChatMessage.tsx           # Mensajes del chatbot          │
│  ├── ChatAvatar.tsx            # Avatar animado                │
│  └── ChartControls.tsx         # Controles de gráficos         │
│                                                                 │
│  📁 src/pages/                                                  │
│  ├── Dashboard.tsx             # Página principal              │
│  ├── Chatbot.tsx               # Interfaz del chatbot          │
│  └── OLAPAnalytics.tsx         # Análisis OLAP                 │
│                                                                 │
│  📁 src/hooks/                                                  │
│  ├── useSmartFilters.ts        # Hook de filtros               │
│  ├── useAuth.tsx               # Hook de autenticación         │
│  └── useReactiveFilters.ts     # Hook de filtros reactivos     │
│                                                                 │
│  📁 src/services/                                               │
│  ├── sugarbiService.ts         # Servicio de API               │
│  └── api.ts                    # Configuración de API          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🌐 APIs y Endpoints

### API Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                        API ENDPOINTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍 FILTROS INTELIGENTES                                        │
│  GET  /api/filter-options       # Opciones de filtros          │
│  GET  /api/cosecha-filtered     # Datos filtrados              │
│                                                                 │
│  🤖 CHATBOT                                                     │
│  POST /api/chat                 # Procesar consulta            │
│  POST /api/chat/langchain       # Consulta con LangChain       │
│                                                                 │
│  📊 DASHBOARD                                                   │
│  GET  /api/fincas               # Lista de fincas              │
│  GET  /api/variedades           # Lista de variedades          │
│  GET  /api/zonas                # Lista de zonas               │
│  GET  /api/tiempo               # Períodos de tiempo           │
│  GET  /api/estadisticas         # Estadísticas globales        │
│  GET  /api/top-cosechas         # Top cosechas                 │
│                                                                 │
│  📈 OLAP                                                        │
│  POST /api/olap/execute         # Ejecutar análisis OLAP       │
│  GET  /api/olap/dimensions      # Dimensiones disponibles      │
│  GET  /api/olap/metrics         # Métricas disponibles         │
│                                                                 │
│  🔐 AUTENTICACIÓN                                               │
│  POST /api/auth/login           # Iniciar sesión               │
│  POST /api/auth/register        # Registrarse                  │
│  GET  /api/auth/profile         # Perfil de usuario            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Ejemplo de Request/Response

```json
// Request: POST /api/chat
{
  "query": "¿Cuáles son las 5 mejores fincas por producción en 2025?"
}

// Response
{
  "success": true,
  "data": {
    "natural_response": "Las 5 mejores fincas por producción en 2025 son: Finca_050 con 15,230 toneladas, Finca_139 con 14,850 toneladas, Finca_177 con 13,420 toneladas, Finca_052 con 12,100 toneladas y Finca_004 con 11,500 toneladas.",
    "chart_data": {
      "labels": ["Finca_050", "Finca_139", "Finca_177", "Finca_052", "Finca_004"],
      "datasets": [{
        "label": "Toneladas",
        "data": [15230, 14850, 13420, 12100, 11500],
        "backgroundColor": ["#10b981", "#3b82f6", "#3b82f6", "#3b82f6", "#3b82f6"]
      }]
    },
    "sql_query": "SELECT f.nombre_finca, SUM(h.toneladas_cana_molida) as total FROM hechos_cosecha h JOIN dim_finca f ON h.id_finca = f.id_finca WHERE h.año = 2025 GROUP BY f.id_finca, f.nombre_finca ORDER BY total DESC LIMIT 5",
    "execution_time": 0.245
  }
}
```

## 🚀 Instalación y Configuración

### Requisitos del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    REQUISITOS DEL SISTEMA                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🖥️ BACKEND                                                      │
│  - Python 3.8+                                                  │
│  - Flask 2.0+                                                   │
│  - MySQL 8.0+                                                   │
│  - Pandas, SQLAlchemy, LangChain                               │
│                                                                 │
│  🌐 FRONTEND                                                     │
│  - Node.js 16+                                                  │
│  - React 18+                                                    │
│  - TypeScript 4.5+                                              │
│  - Chart.js, Three.js                                           │
│                                                                 │
│  🗄️ BASE DE DATOS                                               │
│  - MySQL 8.0+                                                   │
│  - Data Mart con esquema estrella                              │
│  - Índices optimizados                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comandos de Instalación

```bash
# Backend
cd SugarBI-backend
pip install -r requirements.txt
python web/app.py

# Frontend
cd sugarBI-fronted
npm install
npm run dev

# Base de datos
mysql -u root -p < sugarbi_database_export.sql
```

## 📈 Métricas y Rendimiento

### KPIs del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        MÉTRICAS DEL SISTEMA                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚡ RENDIMIENTO                                                  │
│  - Tiempo de respuesta API: < 500ms                            │
│  - Tiempo de carga dashboard: < 2s                             │
│  - Tiempo de procesamiento NLP: < 1s                           │
│                                                                 │
│  🎯 PRECISIÓN                                                    │
│  - Precisión de parsing NLP: > 95%                             │
│  - Precisión de filtros: 100%                                  │
│  - Precisión de visualizaciones: 100%                          │
│                                                                 │
│  📊 USABILIDAD                                                   │
│  - Tiempo de aprendizaje: < 5 min                              │
│  - Satisfacción del usuario: > 4.5/5                           │
│  - Tasa de error: < 1%                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Notas de Desarrollo

- **Versión**: 1.0.0
- **Última actualización**: Enero 2025
- **Mantenido por**: Equipo SugarBI
- **Licencia**: MIT

Para más información técnica, consultar la documentación completa en `/docs/`.
