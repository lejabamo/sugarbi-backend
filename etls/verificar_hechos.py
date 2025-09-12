from sqlalchemy import create_engine, text
import configparser

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Verificar estructura de tabla de hechos
with engine.connect() as conn:
    print("--- Estructura de hechos_cosecha ---")
    result = conn.execute(text("DESCRIBE hechos_cosecha"))
    for row in result:
        print(f"  {row[0]} - {row[1]}")
    
    print("\n--- Conteo de registros en cada tabla ---")
    tables = ['dimfinca', 'dimvariedad', 'dimzona', 'dimtiempo', 'hechos_cosecha']
    for table in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.fetchone()[0]
        print(f"  {table}: {count} registros")

