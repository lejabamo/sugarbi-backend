from sqlalchemy import create_engine, text
import configparser

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Tablas que NO pertenecen al data mart
tables_to_remove = ['dimtiposuelo', 'hechoscosecha']

print("=== LIMPIEZA DE BASE DE DATOS ===")
print("Eliminando tablas que no pertenecen al Data Mart...")

try:
    with engine.connect() as conn:
        # Deshabilitar verificaciones de clave foránea temporalmente
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        for table in tables_to_remove:
            try:
                # Verificar si la tabla existe
                result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                if result.fetchone():
                    # Eliminar la tabla
                    conn.execute(text(f"DROP TABLE {table}"))
                    print(f"  ✅ Tabla '{table}' eliminada exitosamente")
                else:
                    print(f"  ⚠️  Tabla '{table}' no existe")
            except Exception as e:
                print(f"  ❌ Error eliminando tabla '{table}': {e}")
        
        # Rehabilitar verificaciones de clave foránea
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        
        print("\n=== VERIFICACIÓN FINAL ===")
        result = conn.execute(text("SHOW TABLES"))
        remaining_tables = [row[0] for row in result]
        
        print("Tablas restantes en la base de datos:")
        for table in remaining_tables:
            print(f"  ✅ {table}")
        
        print(f"\nTotal de tablas: {len(remaining_tables)}")
        
except Exception as e:
    print(f"❌ Error general: {e}")

print("\n🎯 Base de datos limpia y lista para el Data Mart!")

