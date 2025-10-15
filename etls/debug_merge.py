import pandas as pd
from sqlalchemy import create_engine, text
import configparser
from pathlib import Path

# Configuración
ruta_base = Path(__file__).parent.parent
config = configparser.ConfigParser()
config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
db_config = config['mysql']
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Leer datos
ruta_data_principal = ruta_base / 'raw_data' / 'data.xlsx'
df_data_raw = pd.read_excel(ruta_data_principal)

# Crear mapeos
df_fincas_map = pd.read_sql("SELECT finca_id, codigo_finca FROM dimfinca", engine)

print("=== DEBUG MERGE FINCAS ===")
print(f"Registros en df_data_raw: {len(df_data_raw)}")
print(f"Registros en df_fincas_map: {len(df_fincas_map)}")

print("\nPrimeros 5 códigos de finca en datos originales:")
print(df_data_raw['Cod Finca'].head().tolist())
print(f"Tipo de datos: {df_data_raw['Cod Finca'].dtype}")

print("\nPrimeros 5 códigos de finca en mapeo:")
print(df_fincas_map['codigo_finca'].head().tolist())
print(f"Tipo de datos: {df_fincas_map['codigo_finca'].dtype}")

# Convertir tipos
df_data_raw['Cod Finca'] = df_data_raw['Cod Finca'].astype(str)
df_fincas_map['codigo_finca'] = df_fincas_map['codigo_finca'].astype(str)

print("\nDespués de conversión:")
print(f"Tipo en datos originales: {df_data_raw['Cod Finca'].dtype}")
print(f"Tipo en mapeo: {df_fincas_map['codigo_finca'].dtype}")

# Hacer merge
hechos = df_data_raw[['Año', 'Mes', 'Zona Adm', 'Cod Finca', 'Variedad']].copy()
hechos = hechos.merge(df_fincas_map, left_on='Cod Finca', right_on='codigo_finca', how='left')

print(f"\nRegistros después del merge: {len(hechos)}")
print(f"Registros con finca_id NULL: {hechos['finca_id'].isnull().sum()}")

print("\nPrimeros 10 registros del merge:")
print(hechos[['Cod Finca', 'codigo_finca', 'finca_id']].head(10))

