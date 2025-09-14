# 🏗️ SugarBI - Documentación de Arquitectura y Diagramas

## 📋 Índice
1. [Arquitectura General del Sistema](#arquitectura-general)
2. [Diagramas de Clases](#diagramas-de-clases)
3. [Arquitectura MVC](#arquitectura-mvc)
4. [Flujo de Proceso ETL](#flujo-etl)
5. [Diagramas de Secuencia](#diagramas-de-secuencia)
6. [Modelo de Datos Dimensional](#modelo-de-datos)

---

## 🏛️ Arquitectura General del Sistema {#arquitectura-general}

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                SISTEMA SUGARBI                                 │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   PRESENTACIÓN  │    │    LÓGICA DE    │    │   PERSISTENCIA  │            │
│  │     (VIEW)      │    │   NEGOCIO       │    │   (MODEL)       │            │
│  │                 │    │   (CONTROLLER)  │    │                 │            │
│  │ • Dashboard     │◄──►│ • Chatbot       │◄──►│ • MySQL         │            │
│  │ • Chatbot UI    │    │ • NLP Parser    │    │ • Data Mart     │            │
│  │ • Visualizaciones│   │ • SQL Generator │    │ • Star Schema   │            │
│  │ • OLAP Interface│    │ • Viz Engine    │    │ • ETL Process   │            │
│  │ • Auth System   │    │ • OLAP Engine   │    │ • Raw Data      │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              COMPONENTES DEL SISTEMA                           │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   FRONTEND      │    │    BACKEND      │    │   DATABASE      │            │
│  │                 │    │                 │    │                 │            │
│  │ • HTML5/CSS3    │    │ • Python 3.13   │    │ • MySQL 8.0     │            │
│  │ • JavaScript    │    │ • Flask 3.1.2   │    │ • Data Mart     │            │
│  │ • Bootstrap 5   │    │ • SQLAlchemy    │    │ • Dimensional   │            │
│  │ • Chart.js      │    │ • Pandas        │    │ • Star Schema   │            │
│  │ • Font Awesome  │    │ • NumPy         │    │ • ETL Scripts   │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Diagramas de Clases {#diagramas-de-clases}

### 1. Clases Principales del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DIAGRAMA DE CLASES PRINCIPALES                    │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   QueryParser   │    │  SQLGenerator   │    │ VisualizationEngine│          │
│  │                 │    │                 │    │                 │            │
│  │ + parse(text)   │    │ + generate_sql()│    │ + create_chart() │            │
│  │ + extract_intent│    │ + build_query() │    │ + get_chart_type│            │
│  │ + identify_type │    │ + optimize_sql()│    │ + format_data()  │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   OLAEEngine    │    │   Flask App     │    │   Auth System   │            │
│  │                 │    │                 │    │                 │            │
│  │ + execute_olap()│    │ + route()       │    │ + authenticate()│            │
│  │ + drill_down()  │    │ + process_chat()│    │ + authorize()   │            │
│  │ + roll_up()     │    │ + serve_static()│    │ + audit_log()   │            │
│  │ + slice_dice()  │    │ + handle_error()│    │ + manage_session│            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Jerarquía de Clases del Chatbot

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            JERARQUÍA DE CLASES - CHATBOT                       │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              QueryParser                                   ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   QueryType     │  │   MetricType    │  │  DimensionType  │            ││
│  │  │   (Enum)        │  │   (Enum)        │  │   (Enum)        │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • TOP_RANKING   │  │ • TONELADAS     │  │ • FINCA         │            ││
│  │  │ • STATISTICS    │  │ • TCH           │  │ • VARIEDAD      │            ││
│  │  │ • COMPARISON    │  │ • BRIX          │  │ • ZONA          │            ││
│  │  │ • TREND         │  │ • SACAROSA      │  │ • TIEMPO        │            ││
│  │  │ • BASIC         │  │ • AREA          │  │                 │            ││
│  │  │                 │  │ • RENDIMIENTO   │  │                 │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              QueryIntent                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ @dataclass                                                             │││
│  │  │ class QueryIntent:                                                     │││
│  │  │     query_type: QueryType                                              │││
│  │  │     metric: MetricType                                                 │││
│  │  │     dimension: DimensionType                                           │││
│  │  │     filters: Dict[str, Any]                                            │││
│  │  │     limit: Optional[int]                                               │││
│  │  │     time_period: Optional[str]                                         │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Clases del Motor OLAP

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DIAGRAMA DE CLASES - OLAP                         │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              OLAEEngine                                    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │ OLAPOperation   │  │AggregationFunction│  │ DimensionLevel │            ││
│  │  │   (Enum)        │  │   (Enum)        │  │   (Enum)        │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • AGGREGATE     │  │ • SUM           │  │ • YEAR          │            ││
│  │  │ • DRILL_DOWN    │  │ • AVG           │  │ • QUARTER       │            ││
│  │  │ • ROLL_UP       │  │ • MAX           │  │ • MONTH         │            ││
│  │  │ • SLICE         │  │ • MIN           │  │ • DATE          │            ││
│  │  │ • DICE          │  │ • COUNT         │  │ • ZONE          │            ││
│  │  │ • PIVOT         │  │ • STD           │  │ • FARM          │            ││
│  │  │                 │  │ • MEDIAN        │  │ • VARIETY       │            ││
│  │  │                 │  │ • VARIANCE      │  │                 │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              OLAPQuery                                     ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ @dataclass                                                             │││
│  │  │ class OLAPQuery:                                                       │││
│  │  │     operation: OLAPOperation                                           │││
│  │  │     measures: List[str]                                                │││
│  │  │     dimensions: List[str]                                              │││
│  │  │     dimension_levels: Dict[str, DimensionLevel]                        │││
│  │  │     aggregation_functions: List[AggregationFunction]                   │││
│  │  │     filters: Dict[str, Any]                                            │││
│  │  │     limit: Optional[int]                                               │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Arquitectura MVC {#arquitectura-mvc}

### 1. Estructura MVC de Flask

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITECTURA MVC - FLASK                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                                MODEL (M)                                   ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   SQLAlchemy    │  │   Data Models   │  │   ETL Scripts   │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • User          │  │ • DimFinca      │  │ • cargar_datos  │            ││
│  │  │ • Role          │  │ • DimVariedad   │  │ • crear_tablas  │            ││
│  │  │ • SessionToken  │  │ • DimZona       │  │ • verificar_*   │            ││
│  │  │ • AuditLog      │  │ • DimTiempo     │  │ • limpiar_bd    │            ││
│  │  │                 │  │ • HechosCosecha │  │                 │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              VIEW (V)                                      ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   Templates     │  │   Static Files  │  │   JavaScript    │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • base.html     │  │ • CSS           │  │ • Chart.js      │            ││
│  │  │ • index.html    │  │ • Images        │  │ • AJAX calls    │            ││
│  │  │ • chatbot.html  │  │ • Fonts         │  │ • DOM manip     │            ││
│  │  │ • dashboard.html│  │ • Icons         │  │ • Event handlers│            ││
│  │  │ • olap_*.html   │  │                 │  │                 │            ││
│  │  │ • auth/*.html   │  │                 │  │                 │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CONTROLLER (C)                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   Flask Routes  │  │   API Endpoints │  │   Business Logic│            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • @app.route()  │  │ • /api/chat     │  │ • QueryParser   │            ││
│  │  │ • render_template│  │ • /api/olap/*  │  │ • SQLGenerator  │            ││
│  │  │ • request       │  │ • /api/stats    │  │ • VizEngine     │            ││
│  │  │ • jsonify       │  │ • /api/examples │  │ • OLAEEngine    │            ││
│  │  │ • redirect      │  │                 │  │ • AuthManager   │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Flujo de Datos MVC

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE DATOS MVC                                │
│                                                                                 │
│  Usuario                                                                        │
│    │                                                                           │
│    │ 1. Request HTTP                                                           │
│    ▼                                                                           │
│  ┌─────────────────┐                                                           │
│  │   CONTROLLER    │                                                           │
│  │   (Flask App)   │                                                           │
│  │                 │                                                           │
│  │ • Recibe request│                                                           │
│  │ • Valida datos  │                                                           │
│  │ • Procesa lógica│                                                           │
│  │ • Llama Model   │                                                           │
│  └─────────────────┘                                                           │
│    │                                                                           │
│    │ 2. Query/Update                                                           │
│    ▼                                                                           │
│  ┌─────────────────┐                                                           │
│  │     MODEL       │                                                           │
│  │   (SQLAlchemy)  │                                                           │
│  │                 │                                                           │
│  │ • Accede BD     │                                                           │
│  │ • Ejecuta SQL   │                                                           │
│  │ • Retorna datos │                                                           │
│  └─────────────────┘                                                           │
│    │                                                                           │
│    │ 3. Data Response                                                          │
│    ▼                                                                           │
│  ┌─────────────────┐                                                           │
│  │     VIEW        │                                                           │
│  │   (Templates)   │                                                           │
│  │                 │                                                           │
│  │ • Renderiza HTML│                                                           │
│  │ • Formatea JSON │                                                           │
│  │ • Envía response│                                                           │
│  └─────────────────┘                                                           │
│    │                                                                           │
│    │ 4. HTTP Response                                                          │
│    ▼                                                                           │
│  Usuario                                                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Proceso ETL {#flujo-etl}

### 1. Diagrama de Flujo ETL General

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PROCESO ETL - SUGARBI                             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   EXTRACT       │    │   TRANSFORM     │    │     LOAD        │            │
│  │                 │    │                 │    │                 │            │
│  │ • Excel Files   │───►│ • Data Cleaning │───►│ • MySQL Tables  │            │
│  │ • Raw Data      │    │ • Data Mapping  │    │ • Data Mart     │            │
│  │ • CSV Files     │    │ • Data Validation│   │ • Star Schema   │            │
│  │ • XLS Files     │    │ • Data Enrichment│   │ • Indexes       │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Flujo Detallado del ETL

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DETALLADO ETL                               │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                                EXTRACT                                     ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   data.xlsx     │  │ Cronologico_*   │  │   Labores_*     │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Datos principales│ • Datos temporales│ • Datos de labores│            ││
│  │  │ • Fincas        │  │ • Fechas        │  │ • Actividades   │            ││
│  │  │ • Variedades    │  │ • Períodos      │  │ • Rendimientos  │            ││
│  │  │ • Producción    │  │ • Cronología    │  │ • Métricas      │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  │  ┌─────────────────┐  ┌─────────────────┐                                 ││
│  │  │   Lluvias_*     │  │   Historico_*   │                                 ││
│  │  │                 │  │                 │                                 ││
│  │  │ • Datos climáticos│ • Datos históricos│                                 ││
│  │  │ • Precipitación │  │ • Series temporales│                               ││
│  │  │ • Períodos      │  │ • Tendencias    │                                 ││
│  │  └─────────────────┘  └─────────────────┘                                 ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                               TRANSFORM                                    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │  Data Cleaning  │  │  Data Mapping   │  │ Data Validation │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Remove nulls  │  │ • Column mapping│  │ • Type checking │            ││
│  │  │ • Fix encoding  │  │ • Key generation│  │ • Range validation│           ││
│  │  │ • Standardize   │  │ • Relationship  │  │ • Business rules│            ││
│  │  │ • Deduplicate   │  │ • Foreign keys  │  │ • Data quality  │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                                 LOAD                                       ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │  Dimensiones    │  │  Tabla Hechos   │  │   Verificación  │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • DimFinca      │  │ • HechosCosecha │  │ • Count records │            ││
│  │  │ • DimVariedad   │  │ • Métricas      │  │ • Data integrity│            ││
│  │  │ • DimZona       │  │ • Foreign keys  │  │ • Performance   │            ││
│  │  │ • DimTiempo     │  │ • Aggregations  │  │ • Indexes       │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Scripts ETL y su Orden de Ejecución

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SCRIPTS ETL - ORDEN DE EJECUCIÓN                  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                               FASE 1                                       ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │ limpiar_bd.py   │  │ crear_tablas.py │  │ verificar_*.py  │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Limpia BD     │  │ • Crea esquema  │  │ • Verifica BD   │            ││
│  │  │ • Reset IDs     │  │ • Estructura    │  │ • Valida datos  │            ││
│  │  │ • Foreign keys  │  │ • Constraints   │  │ • Reporta errores│           ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                               FASE 2                                       ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │ cargar_datos.py │  │ debug_merge.py  │  │ consulta_ejemplo│            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Carga datos   │  │ • Debug merge   │  │ • Prueba queries│            ││
│  │  │ • ETL completo  │  │ • Troubleshoot  │  │ • Valida resultados│         ││
│  │  │ • Transform     │  │ • Data issues   │  │ • Performance   │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                               FASE 3                                       ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │verificar_todas_ │  │verificar_hechos │  │verificar_fincas │            ││
│  │  │   tablas.py     │  │      .py        │  │      .py        │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Verifica todo │  │ • Verifica hechos│  │ • Verifica fincas│          ││
│  │  │ • Reporte final │  │ • Métricas      │  │ • Dimensiones   │            ││
│  │  │ • Data quality  │  │ • Agregaciones  │  │ • Relaciones    │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Diagramas de Secuencia {#diagramas-de-secuencia}

### 1. Flujo de Consulta del Chatbot

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE CONSULTA CHATBOT                         │
│                                                                                 │
│  Usuario    Frontend    Controller    QueryParser    SQLGenerator    Database   │
│    │           │           │             │              │              │        │
│    │ 1. Pregunta│           │             │              │              │        │
│    │──────────►│           │             │              │              │        │
│    │           │ 2. POST   │             │              │              │        │
│    │           │/api/chat  │             │              │              │        │
│    │           │──────────►│             │              │              │        │
│    │           │           │ 3. parse()  │              │              │        │
│    │           │           │────────────►│              │              │        │
│    │           │           │             │ 4. Intent    │              │        │
│    │           │           │             │◄─────────────│              │        │
│    │           │           │ 5. generate │              │              │        │
│    │           │           │─────────────┼─────────────►│              │        │
│    │           │           │             │              │ 6. SQL Query │        │
│    │           │           │             │              │◄─────────────│        │
│    │           │           │ 7. execute  │              │              │        │
│    │           │           │─────────────┼──────────────┼─────────────►│        │
│    │           │           │             │              │              │ 8. Data│
│    │           │           │             │              │              │◄───────│
│    │           │           │ 9. Response │              │              │        │
│    │           │           │◄────────────┼──────────────┼──────────────┼        │
│    │           │ 10. JSON  │             │              │              │        │
│    │           │◄──────────│             │              │              │        │
│    │ 11. Result│           │             │              │              │        │
│    │◄──────────│           │             │              │              │        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE AUTENTICACIÓN                            │
│                                                                                 │
│  Usuario    Frontend    AuthController    SecurityManager    Database          │
│    │           │             │                │                │               │
│    │ 1. Login  │             │                │                │               │
│    │──────────►│             │                │                │               │
│    │           │ 2. POST     │                │                │               │
│    │           │/auth/login  │                │                │               │
│    │           │────────────►│                │                │               │
│    │           │             │ 3. validate    │                │               │
│    │           │             │───────────────►│                │               │
│    │           │             │                │ 4. check user  │               │
│    │           │             │                │───────────────►│               │
│    │           │             │                │                │ 5. User data  │
│    │           │             │                │                │◄──────────────│
│    │           │             │                │ 6. generate    │               │
│    │           │             │                │    token       │               │
│    │           │             │ 7. session     │                │               │
│    │           │             │◄───────────────│                │               │
│    │           │ 8. redirect │                │                │               │
│    │           │◄────────────│                │                │               │
│    │ 9. Dashboard│           │                │                │               │
│    │◄──────────│             │                │                │               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Modelo de Datos Dimensional {#modelo-de-datos}

### 1. Esquema Estrella (Star Schema)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ESQUEMA ESTRELLA - SUGARBI                        │
│                                                                                 │
│                                    ┌─────────────────┐                         │
│                                    │  HECHOS_COSECHA │                         │
│                                    │   (Fact Table)  │                         │
│                                    │                 │                         │
│                                    │ • toneladas_cana│                         │
│                                    │ • tch           │                         │
│                                    │ • area_cosechada│                         │
│                                    │ • brix          │                         │
│                                    │ • sacarosa      │                         │
│                                    │ • rendimiento   │                         │
│                                    └─────────────────┘                         │
│                                           │                                    │
│                    ┌──────────────────────┼──────────────────────┐            │
│                    │                      │                      │            │
│        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │
│        │   DIMFINCA      │    │  DIMVARIEDAD    │    │    DIMZONA      │    │
│        │ (Dimension)     │    │ (Dimension)     │    │ (Dimension)     │    │
│        │                 │    │                 │    │                 │    │
│        │ • finca_id (PK) │    │ • variedad_id   │    │ • codigo_zona   │    │
│        │ • codigo_finca  │    │ • nombre_variedad│   │ • nombre_zona   │    │
│        │ • nombre_finca  │    │ • descripcion   │    │ • region        │    │
│        │ • ubicacion     │    │ • caracteristicas│   │ • clima         │    │
│        │ • area_total    │    │ • rendimiento   │    │ • altitud       │    │
│        └─────────────────┘    └─────────────────┘    └─────────────────┘    │
│                    │                      │                      │            │
│                    └──────────────────────┼──────────────────────┘            │
│                                           │                                    │
│                                    ┌─────────────────┐                         │
│                                    │   DIMTIEMPO     │                         │
│                                    │ (Dimension)     │                         │
│                                    │                 │                         │
│                                    │ • tiempo_id (PK)│                         │
│                                    │ • año           │                         │
│                                    │ • mes           │                         │
│                                    │ • trimestre     │                         │
│                                    │ • semestre      │                         │
│                                    │ • fecha         │                         │
│                                    │ • dia_semana    │                         │
│                                    │ • es_festivo    │                         │
│                                    └─────────────────┘                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Relaciones entre Tablas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RELACIONES ENTRE TABLAS                            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CLAVES FORÁNEAS                                  ││
│  │                                                                             ││
│  │  HECHOS_COSECHA                                                             ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ • codigo_tiempo  ──────┐                                                │││
│  │  │ • codigo_zona    ──────┼─────┐                                          │││
│  │  │ • codigo_variedad ─────┼─────┼─────┐                                    │││
│  │  │ • id_finca       ──────┼─────┼─────┼─────┐                              │││
│  │  │ • toneladas_cana_molida│     │     │     │                              │││
│  │  │ • tch                  │     │     │     │                              │││
│  │  │ • area_cosechada       │     │     │     │                              │││
│  │  │ • brix                 │     │     │     │                              │││
│  │  │ • sacarosa             │     │     │     │                              │││
│  │  │ • rendimiento_teorico  │     │     │     │                              │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │    │           │           │           │                                    ││
│  │    │           │           │           │                                    ││
│  │    ▼           ▼           ▼           ▼                                    ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                            ││
│  │  │DIMTIEMPO│ │ DIMZONA │ │DIMVARIED│ │DIMFINCA │                            ││
│  │  │         │ │         │ │   AD    │ │         │                            ││
│  │  │tiempo_id│ │codigo_  │ │variedad_│ │finca_id │                            ││
│  │  │(PK)     │ │zona(PK) │ │id(PK)   │ │(PK)     │                            ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Resumen de Arquitectura

### Componentes Clave del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESUMEN ARQUITECTURA                               │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CAPA DE PRESENTACIÓN                             ││
│  │  • Dashboard Web (HTML/CSS/JS)                                              ││
│  │  • Chatbot Interface                                                        ││
│  │  • OLAP Analytics Interface                                                 ││
│  │  • Authentication System                                                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CAPA DE APLICACIÓN                               ││
│  │  • Flask Web Framework                                                      ││
│  │  • REST API Endpoints                                                       ││
│  │  • Business Logic Controllers                                               ││
│  │  • Authentication & Authorization                                           ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CAPA DE SERVICIOS                                ││
│  │  • Query Parser (NLP)                                                       ││
│  │  • SQL Generator                                                            ││
│  │  • Visualization Engine                                                     ││
│  │  • OLAP Engine                                                              ││
│  │  • ETL Services                                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            CAPA DE DATOS                                    ││
│  │  • MySQL Database                                                           ││
│  │  • Data Mart (Star Schema)                                                  ││
│  │  • SQLAlchemy ORM                                                           ││
│  │  • Raw Data Files (Excel/CSV)                                               ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Tecnologías y Versiones

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Backend** | Python | 3.13.2 | Lenguaje principal |
| **Web Framework** | Flask | 3.1.2 | Framework web |
| **ORM** | SQLAlchemy | 2.0.43 | Mapeo objeto-relacional |
| **Database** | MySQL | 8.0 | Base de datos |
| **Data Processing** | Pandas | 2.3.2 | Manipulación de datos |
| **Numerical** | NumPy | 2.3.2 | Cálculos numéricos |
| **Frontend** | HTML5/CSS3/JS | - | Interfaz web |
| **UI Framework** | Bootstrap | 5.3.0 | Framework CSS |
| **Charts** | Chart.js | - | Visualizaciones |
| **Icons** | Font Awesome | 6.0.0 | Iconografía |

---

*Documentación generada mediante ingeniería inversa del proyecto SugarBI*
*Fecha: $(date)*
*Versión: 1.0*
