import pandas as pd
from sqlalchemy import create_engine
import configparser
from pathlib import Path
from functools import wraps
import time
import logging

def get_db_connection():
    """Crear conexión a la base de datos"""
    ruta_base = Path(__file__).parent.parent
    config = configparser.ConfigParser()
    config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
    
    db_config = config['mysql']
    cadena_conexion = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    return create_engine(cadena_conexion)

def validate_filters(filters):
    """Validar filtros de consulta"""
    valid_filters = {}
    
    # Validar finca_id
    if 'finca_id' in filters and filters['finca_id']:
        try:
            valid_filters['finca_id'] = int(filters['finca_id'])
        except ValueError:
            raise ValueError("finca_id debe ser un número entero")
    
    # Validar variedad_id
    if 'variedad_id' in filters and filters['variedad_id']:
        try:
            valid_filters['variedad_id'] = int(filters['variedad_id'])
        except ValueError:
            raise ValueError("variedad_id debe ser un número entero")
    
    # Validar zona_id
    if 'zona_id' in filters and filters['zona_id']:
        try:
            valid_filters['zona_id'] = int(filters['zona_id'])
        except ValueError:
            raise ValueError("zona_id debe ser un número entero")
    
    # Validar año
    if 'año' in filters and filters['año']:
        try:
            año = int(filters['año'])
            if año < 2000 or año > 2030:
                raise ValueError("año debe estar entre 2000 y 2030")
            valid_filters['año'] = año
        except ValueError:
            raise ValueError("año debe ser un número entero válido")
    
    # Validar mes
    if 'mes' in filters and filters['mes']:
        try:
            mes = int(filters['mes'])
            if mes < 1 or mes > 12:
                raise ValueError("mes debe estar entre 1 y 12")
            valid_filters['mes'] = mes
        except ValueError:
            raise ValueError("mes debe ser un número entero entre 1 y 12")
    
    return valid_filters

def validate_pagination(page, per_page):
    """Validar parámetros de paginación"""
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 100
        
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 100
        if per_page > 1000:
            per_page = 1000
            
        return page, per_page
    except ValueError:
        return 1, 100

def build_cosecha_query(filters=None, limit=100, offset=0):
    """Construir consulta SQL para datos de cosecha"""
    query = """
    SELECT 
        h.id_hecho,
        f.nombre_finca,
        v.nombre_variedad,
        z.nombre_zona,
        t.año,
        t.mes,
        t.nombre_mes,
        h.toneladas_cana_molida,
        h.tch,
        h.area_cosechada,
        h.brix,
        h.sacarosa,
        h.rendimiento_teorico
    FROM hechos_cosecha h
    JOIN dimfinca f ON h.id_finca = f.finca_id
    JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
    JOIN dimzona z ON h.codigo_zona = z.codigo_zona
    JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
    WHERE 1=1
    """
    
    params = {}
    
    if filters:
        if 'finca_id' in filters:
            query += " AND h.id_finca = :finca_id"
            params['finca_id'] = filters['finca_id']
        
        if 'variedad_id' in filters:
            query += " AND h.codigo_variedad = :variedad_id"
            params['variedad_id'] = filters['variedad_id']
        
        if 'zona_id' in filters:
            query += " AND h.codigo_zona = :zona_id"
            params['zona_id'] = filters['zona_id']
        
        if 'año' in filters:
            query += " AND t.año = :año"
            params['año'] = filters['año']
        
        if 'mes' in filters:
            query += " AND t.mes = :mes"
            params['mes'] = filters['mes']
    
    query += " ORDER BY h.toneladas_cana_molida DESC"
    query += " LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = offset
    
    return query, params

def format_response(data, success=True, message=None, **kwargs):
    """Formatear respuesta de la API"""
    response = {
        "success": success,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    # Agregar metadatos adicionales
    for key, value in kwargs.items():
        response[key] = value
    
    return response

def log_query_time(func):
    """Decorador para medir tiempo de ejecución de consultas"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logging.info(f"Query executed in {execution_time:.3f} seconds")
        
        return result
    return wrapper

def safe_float(value):
    """Convertir valor a float de manera segura"""
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None

def safe_int(value):
    """Convertir valor a int de manera segura"""
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None








