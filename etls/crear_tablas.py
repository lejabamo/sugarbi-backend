import pandas as pd
from sqlalchemy import create_engine, text
import os
import configparser
from pathlib import Path

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
print("Creando tablas del Data Mart...")

# Construir rutas relativas al script actual
ruta_base = Path(__file__).parent.parent

# Leer la configuración de la base de datos
config = configparser.ConfigParser()
config_path = ruta_base / 'config' / 'config.ini'
config.read(config_path, encoding='utf-8')

db_config = config['mysql']
cadena_conexion = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
engine = create_engine(cadena_conexion)

# --- 2. CREAR TABLAS ---
print("Creando tablas del Data Mart...")

# Crear tabla DimFinca
create_dimfinca = """
CREATE TABLE IF NOT EXISTS dimfinca (
    id_finca INT AUTO_INCREMENT PRIMARY KEY,
    codigo_finca VARCHAR(50) NOT NULL,
    nombre_finca VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_codigo_finca (codigo_finca)
);
"""

# Crear tabla DimVariedad
create_dimvariedad = """
CREATE TABLE IF NOT EXISTS dimvariedad (
    codigo_variedad INT AUTO_INCREMENT PRIMARY KEY,
    nombre_variedad VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_nombre_variedad (nombre_variedad)
);
"""

# Crear tabla DimZona
create_dimzona = """
CREATE TABLE IF NOT EXISTS dimzona (
    codigo_zona INT AUTO_INCREMENT PRIMARY KEY,
    nombre_zona VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_nombre_zona (nombre_zona)
);
"""

# Crear tabla DimTiempo
create_dimtiempo = """
CREATE TABLE IF NOT EXISTS dimtiempo (
    codigo_tiempo VARCHAR(10) PRIMARY KEY,
    año INT NOT NULL,
    mes INT NOT NULL,
    trimestre INT NOT NULL,
    semestre INT NOT NULL,
    fecha DATE NOT NULL
);
"""

# Crear tabla de hechos (sin claves foráneas por ahora)
create_hechos_cosecha = """
CREATE TABLE IF NOT EXISTS hechos_cosecha (
    id_hecho INT AUTO_INCREMENT PRIMARY KEY,
    codigo_tiempo VARCHAR(10) NOT NULL,
    codigo_zona INT NOT NULL,
    codigo_variedad INT NOT NULL,
    id_finca INT NOT NULL,
    toneladas_cana_molida DECIMAL(15,2),
    tch DECIMAL(10,2),
    area_cosechada DECIMAL(15,2),
    brix DECIMAL(5,2),
    sacarosa DECIMAL(5,2),
    rendimiento_teorico DECIMAL(10,2)
);
"""

# Ejecutar las consultas de creación
try:
    with engine.connect() as conn:
        conn.execute(text(create_dimfinca))
        print("✅ Tabla DimFinca creada/verificada")
        
        conn.execute(text(create_dimvariedad))
        print("✅ Tabla DimVariedad creada/verificada")
        
        conn.execute(text(create_dimzona))
        print("✅ Tabla DimZona creada/verificada")
        
        conn.execute(text(create_dimtiempo))
        print("✅ Tabla DimTiempo creada/verificada")
        
        conn.execute(text(create_hechos_cosecha))
        print("✅ Tabla Hechos_Cosecha creada/verificada")
        
        conn.commit()
        
except Exception as e:
    print(f"❌ Error creando tablas: {e}")

print("\n--- ¡Tablas del Data Mart creadas exitosamente! ---")
