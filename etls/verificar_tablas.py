from sqlalchemy import create_engine, text
import configparser
from pathlib import Path

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Verificar tablas
with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result]
    print("Tablas existentes:", tables)
    
    # Verificar estructura de cada tabla
    for table in tables:
        print(f"\n--- Estructura de {table} ---")
        result = conn.execute(text(f"DESCRIBE {table}"))
        for row in result:
            print(f"  {row[0]} - {row[1]}")

