import pandas as pd
from sqlalchemy import create_engine, text
import os
import configparser
from pathlib import Path

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
print("Iniciando Proceso ETL...")

# Construir rutas relativas al script actual para que funcione en cualquier máquina
# Path(__file__) es la ubicación del script, .parent.parent es para subir dos niveles a la raíz 'sugarbi'
ruta_base = Path(__file__).parent.parent

# Leer la configuración de la base de datos desde el archivo .ini
config = configparser.ConfigParser()
config_path = ruta_base / 'config' / 'config.ini'
print(f"Leyendo configuración desde: {config_path}")
print(f"Archivo existe: {config_path.exists()}")

# Leer el archivo con codificación UTF-8
config.read(config_path, encoding='utf-8')
print(f"Secciones encontradas: {config.sections()}")

# Verificar si la sección mysql existe
if 'mysql' not in config:
    print("Error: Sección 'mysql' no encontrada en el archivo de configuración")
    print("Contenido del archivo:")
    with open(config_path, 'r', encoding='utf-8') as f:
        print(f.read())
    exit(1)

db_config = config['mysql']
cadena_conexion = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
engine = create_engine(cadena_conexion)

# Definir rutas a los archivos de datos en la carpeta raw_data
ruta_data_principal = ruta_base / 'raw_data' / 'data.xlsx'
ruta_fincas = ruta_base / 'raw_data' / 'Cronologico_2025_08_29.xlsx'

print("Conexión a MySQL establecida desde archivo de configuración.")

# --- 1.1 LIMPIAR TABLAS EXISTENTES ---
print("\nLimpiando tablas existentes...")
try:
    with engine.connect() as conn:
        # Deshabilitar verificaciones de clave foránea temporalmente
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # Limpiar tablas en orden correcto (hechos primero, luego dimensiones)
        conn.execute(text("DELETE FROM hechos_cosecha"))
        conn.execute(text("DELETE FROM dimtiempo"))
        conn.execute(text("DELETE FROM dimvariedad"))
        conn.execute(text("DELETE FROM dimzona"))
        conn.execute(text("DELETE FROM dimfinca"))
        
        # Reiniciar auto_increment
        conn.execute(text("ALTER TABLE dimfinca AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE dimvariedad AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE dimtiempo AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE hechos_cosecha AUTO_INCREMENT = 1"))
        
        # Rehabilitar verificaciones de clave foránea
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    print("✅ Tablas limpiadas exitosamente")
except Exception as e:
    print(f"⚠️  Error limpiando tablas: {e}")

# --- 2. PROCESO DE CARGA DE DIMENSIONES ---
# (El código es el mismo de la vez anterior, pero ahora usa las rutas relativas)

# --- 2.1 Cargar DimFinca ---
print("\nProcesando DimFinca...")
try:
    # Usar los códigos de finca del archivo principal data.xlsx
    df_data_raw = pd.read_excel(ruta_data_principal)
    dim_finca = df_data_raw[['Cod Finca', 'Hacienda']].copy()
    dim_finca.rename(columns={'Cod Finca': 'codigo_finca', 'Hacienda': 'nombre_finca'}, inplace=True)
    dim_finca.drop_duplicates(subset=['codigo_finca'], inplace=True)
    dim_finca.to_sql('dimfinca', con=engine, if_exists='append', index=False)
    print(f"{len(dim_finca)} registros cargados en DimFinca.")
except Exception as e:
    print(f"Error cargando DimFinca: {e}")

# --- 2.2 Cargar DimVariedad ---
print("\nProcesando DimVariedad...")
try:
    df_data_raw = pd.read_excel(ruta_data_principal)
    dim_variedad = df_data_raw[['Variedad']].copy()
    dim_variedad.rename(columns={'Variedad': 'nombre_variedad'}, inplace=True)
    dim_variedad.drop_duplicates(subset=['nombre_variedad'], inplace=True)
    # Usar la estructura existente: variedad_id, nombre_variedad
    dim_variedad = dim_variedad[['nombre_variedad']]
    dim_variedad.to_sql('dimvariedad', con=engine, if_exists='append', index=False)
    print(f"{len(dim_variedad)} registros cargados en DimVariedad.")
except Exception as e:
    print(f"Error cargando DimVariedad: {e}")

# --- 2.3 Cargar DimZona ---
print("\nProcesando DimZona...")
try:
    dim_zona = df_data_raw[['Zona Adm']].copy()
    dim_zona.rename(columns={'Zona Adm': 'codigo_zona'}, inplace=True)
    dim_zona.drop_duplicates(subset=['codigo_zona'], inplace=True)
    # La tabla existente tiene codigo_zona y nombre_zona como bigint, pero usaremos solo codigo_zona
    dim_zona['nombre_zona'] = dim_zona['codigo_zona']  # Usar el código como nombre también
    dim_zona = dim_zona[['codigo_zona', 'nombre_zona']]
    dim_zona.to_sql('dimzona', con=engine, if_exists='append', index=False)
    print(f"{len(dim_zona)} registros cargados en DimZona.")
except Exception as e:
    print(f"Error cargando DimZona: {e}")

# --- 2.4 Cargar DimTiempo ---
print("\nProcesando DimTiempo...")
try:
    dim_tiempo = df_data_raw[['Año', 'Mes']].copy()
    dim_tiempo.drop_duplicates(subset=['Año', 'Mes'], inplace=True)
    dim_tiempo['fecha'] = pd.to_datetime(dim_tiempo['Año'].astype(str) + '-' + dim_tiempo['Mes'].astype(str).str.zfill(2) + '-01')
    dim_tiempo['trimestre'] = ((dim_tiempo['Mes'] - 1) // 3) + 1
    # Usar la estructura existente: tiempo_id, fecha, año, mes, nombre_mes, trimestre
    dim_tiempo['nombre_mes'] = dim_tiempo['fecha'].dt.strftime('%B')
    dim_tiempo = dim_tiempo[['fecha', 'Año', 'Mes', 'nombre_mes', 'trimestre']]
    dim_tiempo.rename(columns={'Año': 'año', 'Mes': 'mes'}, inplace=True)
    dim_tiempo.to_sql('dimtiempo', con=engine, if_exists='append', index=False)
    print(f"{len(dim_tiempo)} registros cargados en DimTiempo.")
except Exception as e:
    print(f"Error cargando DimTiempo: {e}")

# --- 3. PROCESO DE CARGA DE HECHOS ---
print("\nProcesando Tabla de Hechos...")
try:
    # Crear mapeos para las claves foráneas usando la estructura existente
    df_fincas_map = pd.read_sql("SELECT finca_id, codigo_finca FROM dimfinca", engine)
    df_variedad_map = pd.read_sql("SELECT variedad_id, nombre_variedad FROM dimvariedad", engine)
    df_zona_map = pd.read_sql("SELECT codigo_zona FROM dimzona", engine)
    df_tiempo_map = pd.read_sql("SELECT tiempo_id, año, mes FROM dimtiempo", engine)
    
    # Preparar datos de hechos
    hechos = df_data_raw[['Año', 'Mes', 'Zona Adm', 'Cod Finca', 'Variedad', 'TonCña Molida', 'TCH', 'Area Cosechada', 'Brix', 'Sac.', 'Rdto Teór']].copy()
    
    # Convertir tipos de datos para evitar errores en merge
    hechos['Cod Finca'] = hechos['Cod Finca'].astype(str)
    df_fincas_map['codigo_finca'] = df_fincas_map['codigo_finca'].astype(str)
    
    # Hacer joins para obtener las claves foráneas
    hechos = hechos.merge(df_tiempo_map, left_on=['Año', 'Mes'], right_on=['año', 'mes'], how='left')
    hechos = hechos.merge(df_zona_map, left_on='Zona Adm', right_on='codigo_zona', how='left')
    hechos = hechos.merge(df_variedad_map, left_on='Variedad', right_on='nombre_variedad', how='left')
    hechos = hechos.merge(df_fincas_map, left_on='Cod Finca', right_on='codigo_finca', how='left')
    
    # Seleccionar columnas finales usando la estructura existente
    # La tabla hechos_cosecha usa: codigo_tiempo, codigo_zona, codigo_variedad, id_finca
    tabla_hechos = hechos[['tiempo_id', 'codigo_zona', 'variedad_id', 'finca_id', 
                          'TonCña Molida', 'TCH', 'Area Cosechada', 'Brix', 'Sac.', 'Rdto Teór']].copy()
    
    # Renombrar columnas para que coincidan con la estructura de la tabla
    tabla_hechos.rename(columns={
        'tiempo_id': 'codigo_tiempo',
        'variedad_id': 'codigo_variedad',
        'finca_id': 'id_finca'
    }, inplace=True)
    
    tabla_hechos.rename(columns={
        'TonCña Molida': 'toneladas_cana_molida',
        'Area Cosechada': 'area_cosechada',
        'Sac.': 'sacarosa',
        'Rdto Teór': 'rendimiento_teorico'
    }, inplace=True)
    
    tabla_hechos.to_sql('hechos_cosecha', con=engine, if_exists='append', index=False)
    print(f"{len(tabla_hechos)} registros cargados en tabla de hechos.")
    
except Exception as e:
    print(f"Error cargando tabla de hechos: {e}")

print("\n--- ¡Proceso ETL completado con éxito! ---")