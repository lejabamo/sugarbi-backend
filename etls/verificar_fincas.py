from sqlalchemy import create_engine, text
import configparser

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Verificar códigos de finca
with engine.connect() as conn:
    print("=== CÓDIGOS DE FINCA EN DIMFINCA ===")
    result = conn.execute(text("SELECT codigo_finca, nombre_finca FROM dimfinca ORDER BY codigo_finca LIMIT 10"))
    for row in result:
        print(f"  {row[0]} - {row[1]}")
    
    print(f"\nTotal de fincas: {conn.execute(text('SELECT COUNT(*) FROM dimfinca')).fetchone()[0]}")
    
    print("\n=== RANGO DE CÓDIGOS ===")
    result = conn.execute(text("SELECT MIN(codigo_finca), MAX(codigo_finca) FROM dimfinca"))
    min_code, max_code = result.fetchone()
    print(f"  Mínimo: {min_code}")
    print(f"  Máximo: {max_code}")

