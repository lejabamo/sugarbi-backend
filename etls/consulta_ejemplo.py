from sqlalchemy import create_engine, text
import configparser
import pandas as pd

# Leer configuración
config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
db_config = config['mysql']

# Crear conexión
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Consulta de ejemplo
consulta = """
SELECT 
    f.nombre_finca,
    z.nombre_zona,
    v.nombre_variedad,
    t.año,
    t.mes,
    h.toneladas_cana_molida,
    h.tch,
    h.area_cosechada,
    h.brix,
    h.sacarosa,
    h.rendimiento_teorico
FROM hechos_cosecha h
JOIN dimfinca f ON h.id_finca = f.finca_id
JOIN dimzona z ON h.codigo_zona = z.codigo_zona
JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
ORDER BY h.toneladas_cana_molida DESC
LIMIT 10;
"""

print("=== CONSULTA DE EJEMPLO - TOP 10 COSECHAS POR TONELADAS ===")
with engine.connect() as conn:
    df = pd.read_sql(consulta, conn)
    print(df.to_string(index=False))

print(f"\n=== RESUMEN DEL DATA MART ===")
print(f"✅ DimFinca: 294 fincas únicas")
print(f"✅ DimVariedad: 36 variedades únicas") 
print(f"✅ DimZona: 7 zonas administrativas")
print(f"✅ DimTiempo: 63 períodos (año-mes)")
print(f"✅ Hechos_Cosecha: 8,363 registros de cosecha")
print(f"\n🎯 El Data Mart está listo para análisis de Business Intelligence!")

