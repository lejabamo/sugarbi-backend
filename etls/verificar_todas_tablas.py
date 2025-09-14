from sqlalchemy import create_engine, text
import configparser

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

print("=== TODAS LAS TABLAS EN LA BASE DE DATOS ===")
with engine.connect() as conn:
    # Obtener todas las tablas
    result = conn.execute(text("SHOW TABLES"))
    all_tables = [row[0] for row in result]
    
    print(f"Total de tablas encontradas: {len(all_tables)}")
    print("\nLista de tablas:")
    for i, table in enumerate(all_tables, 1):
        print(f"  {i}. {table}")
    
    print("\n=== TABLAS DEL DATA MART (CORRECTAS) ===")
    data_mart_tables = ['dimfinca', 'dimvariedad', 'dimzona', 'dimtiempo', 'hechos_cosecha']
    for table in data_mart_tables:
        if table in all_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - NO ENCONTRADA")
    
    print("\n=== TABLAS QUE NO PERTENECEN AL DATA MART ===")
    tables_to_remove = [table for table in all_tables if table not in data_mart_tables]
    if tables_to_remove:
        for table in tables_to_remove:
            print(f"  🗑️  {table}")
    else:
        print("  ✅ No hay tablas extra")
    
    print(f"\n=== RESUMEN ===")
    print(f"Tablas del Data Mart: {len([t for t in all_tables if t in data_mart_tables])}")
    print(f"Tablas a eliminar: {len(tables_to_remove)}")
    print(f"Total de tablas: {len(all_tables)}")

