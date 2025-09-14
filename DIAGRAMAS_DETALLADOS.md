# 🏗️ SugarBI - Diagramas Detallados del Sistema

## 📋 Índice
1. [Diagramas de Clases](#diagramas-de-clases)
2. [Diagrama de Base de Datos](#diagrama-base-datos)
3. [Diagrama de Componentes](#diagrama-componentes)
4. [Modelos Lógicos](#modelos-logicos)

---

## 🏛️ Diagramas de Clases {#diagramas-de-clases}

### 1. Clases Principales del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DIAGRAMA DE CLASES PRINCIPALES                       │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │  QueryParser    │    │  SQLGenerator   │    │ VisualizationEngine│           │
│  │                 │    │                 │    │                 │              │
│  │ + parse(text)   │    │ + generate_sql()│    │ + create_chart() │             │
│  │ + extract_intent│    │ + build_query() │    │ + get_chart_type│              │
│  │ + identify_type │    │ + optimize_sql()│    │ + format_data()  │             │
│  │ + get_filters() │    │ + validate_sql()│    │ + generate_config│             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│           │                       │                       │                     │
│           └───────────────────────┼───────────────────────┘                     │
│                                   │                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   OLAEEngine    │    │   Flask App     │    │   Auth System   │              │
│  │                 │    │                 │    │                 │              │
│  │ + execute_olap()│    │ + route()       │    │ + authenticate()│              │
│  │ + drill_down()  │    │ + process_chat()│    │ + authorize()   │              │
│  │ + roll_up()     │    │ + serve_static()│    │ + audit_log()   │              │
│  │ + slice_dice()  │    │ + handle_error()│    │ + manage_session│              │
│  │ + pivot()       │    │ + render_template│    │ + check_permission│           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Jerarquía de Enums y Dataclasses

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        JERARQUÍA DE ENUMS Y DATACLASSES                         │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              QueryParser                                    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              ││
│  │  │   QueryType     │  │   MetricType    │  │  DimensionType  │              ││
│  │  │   (Enum)        │  │   (Enum)        │  │   (Enum)        │              ││
│  │  │                 │  │                 │  │                 │              ││
│  │  │ • TOP_RANKING   │  │ • TONELADAS     │  │ • FINCA         │              ││
│  │  │ • STATISTICS    │  │ • TCH           │  │ • VARIEDAD      │              ││
│  │  │ • COMPARISON    │  │ • BRIX          │  │ • ZONA          │              ││
│  │  │ • TREND         │  │ • SACAROSA      │  │ • TIEMPO        │              ││
│  │  │ • BASIC         │  │ • AREA          │  │                 │              ││
│  │  │                 │  │ • RENDIMIENTO   │  │                 │              ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              QueryIntent                                    ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ @dataclass                                                              │││
│  │  │ class QueryIntent:                                                      │││
│  │  │     query_type: QueryType                                               │││
│  │  │     metric: MetricType                                                  │││
│  │  │     dimension: DimensionType                                            │││
│  │  │     filters: Dict[str, Any]                                             │││
│  │  │     limit: Optional[int]                                                │││
│  │  │     time_period: Optional[str]                                          │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Diagrama de Base de Datos {#diagrama-base-datos}

### 1. Esquema Estrella (Star Schema)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ESQUEMA ESTRELLA - SUGARBI                         │
│                                                                                 │
│                                    ┌─────────────────┐                          │
│                                    │  HECHOS_COSECHA │                          │
│                                    │   (Fact Table)  │                          │
│                                    │                 │                          │
│                                    │ • id (PK)       │                          │
│                                    │ • id_finca (FK) │                          │
│                                    │ • codigo_variedad(FK)│                     │
│                                    │ • codigo_zona (FK)│                        │
│                                    │ • codigo_tiempo(FK)│                       │
│                                    │ • toneladas_cana │                         │
│                                    │ • tch            │                         │
│                                    │ • area_cosechada │                         │
│                                    │ • brix           │                         │
│                                    │ • sacarosa       │                         │
│                                    │ • rendimiento    │                         │
│                                    └─────────────────┘                          │
│                                           │                                     │
│                    ┌──────────────────────┼──────────────────────┐              │
│                    │                      │                      │              │
│        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│        │   DIMFINCA      │    │  DIMVARIEDAD    │    │    DIMZONA      │        │
│        │ (Dimension)     │    │ (Dimension)     │    │ (Dimension)     │        │
│        │                 │    │                 │    │                 │        │
│        │ • finca_id (PK) │    │ • variedad_id   │    │ • codigo_zona   │        │
│        │ • codigo_finca  │    │ • nombre_variedad│   │ • nombre_zona   │        │
│        │ • nombre_finca  │    │ • descripcion   │    │ • region        │        │
│        │ • ubicacion     │    │ • caracteristicas│   │ • clima         │        │
│        │ • area_total    │    │ • rendimiento   │    │ • altitud       │        │
│        └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                    │                      │                      │              │
│                    └──────────────────────┼──────────────────────┘              │
│                                           │                                     │
│                                    ┌─────────────────┐                          │
│                                    │   DIMTIEMPO     │                          │
│                                    │ (Dimension)     │                          │
│                                    │                 │                          │
│                                    │ • tiempo_id (PK)│                          │
│                                    │ • año           │                          │
│                                    │ • mes           │                          │
│                                    │ • trimestre     │                          │
│                                    │ • semestre      │                          │
│                                    │ • fecha         │                          │
│                                    │ • dia_semana    │                          │
│                                    │ • es_festivo    │                          │
│                                    └─────────────────┘                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Modelos de Autenticación

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MODELOS DE AUTENTICACIÓN                             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │      User       │    │      Role       │    │  SessionToken   │            │
│  │    (Model)      │    │    (Model)      │    │    (Model)      │            │
│  │                 │    │                 │    │                 │            │
│  │ • id (PK)       │    │ • id (PK)       │    │ • id (PK)       │            │
│  │ • username      │    │ • name          │    │ • token         │            │
│  │ • email         │    │ • description   │    │ • user_id (FK)  │            │
│  │ • password_hash │    │ • permissions   │    │ • expires_at    │            │
│  │ • first_name    │    │ • created_at    │    │ • created_at    │            │
│  │ • last_name     │    │ • updated_at    │    │ • last_used     │            │
│  │ • is_active     │    │                 │    │ • ip_address    │            │
│  │ • is_admin      │    │                 │    │ • user_agent    │            │
│  │ • last_login    │    │                 │    │ • is_active     │            │
│  │ • login_attempts│    │                 │    │                 │            │
│  │ • locked_until  │    │                 │    │                 │            │
│  │ • role_id (FK)  │    │                 │    │                 │            │
│  │ • created_at    │    │                 │    │                 │            │
│  │ • updated_at    │    │                 │    │                 │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                   │
│           │ 1:N                   │                       │ 1:N               │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
│                            ┌─────────────────┐                               │
│                            │   AuditLog      │                               │
│                            │   (Model)       │                               │
│                            │                 │                               │
│                            │ • id (PK)       │                               │
│                            │ • user_id (FK)  │                               │
│                            │ • action        │                               │
│                            │ • resource      │                               │
│                            │ • details       │                               │
│                            │ • ip_address    │                               │
│                            │ • user_agent    │                               │
│                            │ • timestamp     │                               │
│                            └─────────────────┘                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Diagrama de Componentes {#diagrama-componentes}

### 1. Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ARQUITECTURA DE COMPONENTES                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            PRESENTATION LAYER                             ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │   Web Frontend  │  │   API Client    │  │   Mobile App    │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • HTML/CSS/JS   │  │ • REST Client   │  │ • React Native  │            ││
│  │  │ • Bootstrap     │  │ • JSON Parser   │  │ • API Calls     │            ││
│  │  │ • Chart.js      │  │ • Error Handler │  │ • UI Components │            ││
│  │  │ • AJAX Calls    │  │ • Auth Headers  │  │ • Offline Sync  │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                           APPLICATION LAYER                               ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │  Flask Routes   │  │   API Services  │  │   Web Socket    │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • @app.route()  │  │ • Chat Service  │  │ • Real-time     │            ││
│  │  │ • render_template│  │ • OLAP Service │  │ • Notifications │            ││
│  │  │ • request      │  │ • Auth Service  │  │ • Live Updates  │            ││
│  │  │ • jsonify      │  │ • Data Service  │  │ • Chat Messages │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            BUSINESS LAYER                                 ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │  Query Parser   │  │  SQL Generator  │  │  Viz Engine     │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • NLP Processing│  │ • Query Builder │  │ • Chart Creator │            ││
│  │  │ • Intent Extract│  │ • SQL Optimizer │  │ • Data Formatter│            ││
│  │  │ • Filter Parse  │  │ • Validator     │  │ • Config Gen    │            ││
│  │  │ • Type Detect   │  │ • Parameter Bind│  │ • Export Handler│            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  │  ┌─────────────────┐  ┌─────────────────┐                                  ││
│  │  │  OLAP Engine    │  │  Auth Manager   │                                  ││
│  │  │                 │  │                 │                                  ││
│  │  │ • Drill Down    │  │ • Authentication│                                  ││
│  │  │ • Roll Up       │  │ • Authorization │                                  ││
│  │  │ • Slice & Dice  │  │ • Session Mgmt  │                                  ││
│  │  │ • Pivot         │  │ • Audit Logging │                                  ││
│  │  │ • Aggregate     │  │ • Permission    │                                  ││
│  │  └─────────────────┘  └─────────────────┘                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                             DATA LAYER                                    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            ││
│  │  │  SQLAlchemy ORM │  │   ETL Process   │  │   File Storage  │            ││
│  │  │                 │  │                 │  │                 │            ││
│  │  │ • Model Mapping │  │ • Data Extract  │  │ • Excel Files   │            ││
│  │  │ • Query Builder │  │ • Transform     │  │ • CSV Files     │            ││
│  │  │ • Transaction   │  │ • Load          │  │ • Images        │            ││
│  │  │ • Connection    │  │ • Validation    │  │ • Reports       │            ││
│  │  │ • Migration     │  │ • Quality Check │  │ • Exports       │            ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Modelos Lógicos {#modelos-logicos}

### 1. Modelo de Datos - Tablas Principales

| Tabla | Atributos | Tipo | Descripción |
|-------|-----------|------|-------------|
| **hechos_cosecha** | id, id_finca, codigo_variedad, codigo_zona, codigo_tiempo, toneladas_cana_molida, tch, area_cosechada, brix, sacarosa, rendimiento_teorico | Fact | Tabla de hechos con métricas |
| **dimfinca** | finca_id, codigo_finca, nombre_finca, ubicacion, area_total | Dimension | Información de fincas |
| **dimvariedad** | variedad_id, nombre_variedad, descripcion, caracteristicas, rendimiento_esperado | Dimension | Tipos de caña |
| **dimzona** | codigo_zona, nombre_zona, region, clima, altitud | Dimension | Zonas geográficas |
| **dimtiempo** | tiempo_id, año, mes, trimestre, semestre, fecha, dia_semana, es_festivo | Dimension | Dimensiones temporales |

### 2. Modelo de Autenticación

| Tabla | Atributos | Tipo | Descripción |
|-------|-----------|------|-------------|
| **users** | id, username, email, password_hash, first_name, last_name, is_active, is_admin, last_login, login_attempts, locked_until, role_id, created_at, updated_at | Entity | Usuarios del sistema |
| **roles** | id, name, description, permissions, created_at, updated_at | Entity | Roles de usuario |
| **session_tokens** | id, token, user_id, expires_at, created_at, last_used, ip_address, user_agent, is_active | Entity | Tokens de sesión |
| **audit_logs** | id, user_id, action, resource, details, ip_address, user_agent, timestamp | Entity | Logs de auditoría |

### 3. Relaciones entre Modelos

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RELACIONES ENTRE MODELOS                         │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │     User        │◄───│      Role       │    │  SessionToken   │            │
│  │                 │ 1  │       1         │    │                 │            │
│  │ • role_id (FK)  │    │ • users 1:N     │    │ • user_id (FK)  │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                   │
│           │ 1:N                   │                       │ 1:N               │
│           ▼                       ▼                       ▼                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   AuditLog      │    │   hechos_cosecha│    │   dimfinca      │            │
│  │                 │    │                 │    │                 │            │
│  │ • user_id (FK)  │    │ • id_finca (FK) │◄──►│ • finca_id (PK) │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                  │                                            │
│                                  │ N:1                                        │
│                                  ▼                                            │
│                         ┌─────────────────┐                                  │
│                         │  dimvariedad    │                                  │
│                         │                 │                                  │
│                         │ • variedad_id   │                                  │
│                         └─────────────────┘                                  │
│                                  ▲                                            │
│                                  │ N:1                                        │
│                                  │                                            │
│                         ┌─────────────────┐                                  │
│                         │  hechos_cosecha │                                  │
│                         │                 │                                  │
│                         │ • codigo_variedad(FK)│                             │
│                         └─────────────────┘                                  │
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
