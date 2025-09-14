+---------------------------------------------------------------------------------+
|                                  Sistema SugarBI                                |
|                                                                                 |
|    +-------------------------+      +-------------------------+      +-------------------------+
|    |      Frontend           |      |      Backend API        |      |      Base de Datos      |
|    |  (Aplicación Web SPA)   |----->|  (Python/Flask)         |----->|      (MySQL Server)     |
|    |  [React]                |      |  [Contenedor Docker]    |      |  [Contenedor Docker]    |
|    |                         |      |                         |      |                         |
|    | • Renderiza dashboards  |      | • Endpoint de Auth      |      | • Data Mart (Esquema    |
|    | • Interfaz de Chatbot   |      | • Endpoints de datos    |      |   Estrella)             |
|    | • Visualizaciones       |      | • Lógica NLP -> SQL     |      | • Tablas de Hechos y    |
|    |   (Chart.js)            |      | • Módulo OLAP           |      |   Dimensiones           |
|    +-------------------------+      +-------------------------+      +-------------------------+
|                                                                                 |
+---------------------------------------------------------------------------------+

Usuario --> [1. Frontend: Ingresa pregunta en Chatbot] --> [2. Backend API: POST /chatbot/query]
                                                                        |
                                                                        v
            [6. Backend API: Devuelve JSON con la respuesta] <-- [5. Data Mart (MySQL): Ejecuta SQL y devuelve resultados]
                                 ^                                      |
                                 |                                      v
            [3. Backend: Módulo NLP procesa la pregunta] --> [4. Backend: Generador SQL crea la consulta]



 +--------------------------------------------------------------------------------------+
|                                     Sistema SugarBI                                    |
|                                                                                      |
|   (Visualizar Dashboard de KPIs) <----------+                                        |
|                                             |                                        |
|   (Realizar Consulta con Chatbot) <---------+---- (Usuario Analítico)                |
|               ^                             |      (Gerente, Supervisor, Analista)   |
|               |                             |                                        |
|          <<extends>>                        |                                        |
|               |                             |                                        |
|   (Exportar Resultados) <-------------------+                                        |
|                                                                                      |
|                                                                                      |
|   (Autenticar Usuario) <-------------------------------------------------------------+
|                                                                                      |
+--------------------------------------------------------------------------------------+           

+---------------------------+       +---------------------------+       +---------------------------+
|    <<Controller>>         |       |    <<Service>>            |       |    <<Service>>            |
|   ChatbotController       |------>|   QueryService            |------>|   DatabaseService         |
+---------------------------+       +---------------------------+       +---------------------------+
| + handle_query(request)   |       | + process_nl_query(text)  |       | + execute(sql_query)      |
+---------------------------+       +---------------------------+       +---------------------------+
                                              |
                                              | Composes
                                              v
      +-------------------------+      +-------------------------+
      |  <<Component>>          |      |  <<Component>>          |
      |  NLPProcessor           |      |  SQLGenerator           |
      +-------------------------+      +-------------------------+
      | + extract_intent(text)  |      | + build_query(intent)   |
      +-------------------------+      +-------------------------+


+-----------------------------------+
|          Frontend                 |
|       (React Application)         |
+-----------------------------------+
       |
       |  <<consumes>>
       v
+-----------------------------------+
|          Backend API              |
|          (Flask App)              |
|-----------------------------------|
|                                   |
|  +-----------------------------+  |
|  |     <<Component>>           |  |
|  |     API Endpoints           |  |
|  |     (Controllers)           |  |
|  +-----------------------------+  |
|                 |                 |
|  +-----------------------------+  |
|  |     <<Component>>           |  |
|  |     Business Logic          |  |
|  |     (Services, NLP, SQLGen) |  |
|  +-----------------------------+  |
|                 |                 |
|  +-----------------------------+  |
|  |     <<Component>>           |  |
|  |     Data Access Layer       |  |
|  |     (SQLAlchemy)            |  |
|  +-----------------------------+  |
|                                   |
+-----------------------------------+
       |
       |  <<connects to>>
       v
+-----------------------------------+
|          Database                 |
|       (MySQL Server)              |
+-----------------------------------+

Usuario        Frontend             Backend API           NLP Service       SQL Generator       Database
  |               |                      |                     |                   |                |
  | Ingresa Pregunta  |                      |                     |                   |                |
  |-------------->|                      |                     |                   |                |
  |               | POST /chatbot/query  |                     |                   |                |
  |               |--------------------->|                     |                   |                |
  |               |                      | procesarTexto()     |                   |                |
  |               |                      |-------------------->|                   |                |
  |               |                      |                     | Devuelve Intención  |                |
  |               |                      |                     |<------------------- |                |
  |               |                      | generarSQL()        |                   |                |
  |               |                      |---------------------------------------->|                |
  |               |                      |                     |                   | Devuelve SQL   |
  |               |                      |                     |                   |<---------------|
  |               |                      |                     |                   |                |
  |               |                      | executeQuery(SQL)   |                   |                |
  |               |                      |-------------------------------------------------------->|
  |               |                      |                     |                   |                | Devuelve Resultados
  |               |                      |                     |                   |                |<---------------|
  |               | Devuelve JSON        |                     |                   |                |
  |               |<---------------------|                     |                   |                |
  |               |                      |                     |                   |                |
  | Muestra Respuesta |                      |                     |                   |                |
  |<--------------|                      |                     |                   |                |
  |               |                      |                     |                   |                |