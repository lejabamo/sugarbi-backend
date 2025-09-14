from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import configparser
from pathlib import Path
import os

# Configuración de la aplicación
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Permitir caracteres Unicode sin escape
CORS(app)  # Habilitar CORS para todas las rutas

# Configuración de la base de datos
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

# Rutas de la API

@app.route('/')
def home():
    """Endpoint de bienvenida"""
    return jsonify({
        "message": "API SugarBI - Data Mart de Cosecha de Caña",
        "version": "1.0.0",
        "endpoints": {
            "dimensiones": {
                "fincas": "/api/fincas",
                "variedades": "/api/variedades", 
                "zonas": "/api/zonas",
                "tiempo": "/api/tiempo"
            },
            "hechos": {
                "cosecha": "/api/cosecha",
                "estadisticas": "/api/estadisticas"
            }
        }
    })

@app.route('/api/fincas')
def get_fincas():
    """Obtener todas las fincas"""
    try:
        engine = get_db_connection()
        query = "SELECT finca_id, codigo_finca, nombre_finca FROM dimfinca ORDER BY nombre_finca"
        df = pd.read_sql(query, engine)
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "total": len(df)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/variedades')
def get_variedades():
    """Obtener todas las variedades"""
    try:
        engine = get_db_connection()
        query = "SELECT variedad_id, nombre_variedad FROM dimvariedad ORDER BY nombre_variedad"
        df = pd.read_sql(query, engine)
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "total": len(df)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/zonas')
def get_zonas():
    """Obtener todas las zonas"""
    try:
        engine = get_db_connection()
        query = "SELECT codigo_zona, nombre_zona FROM dimzona ORDER BY codigo_zona"
        df = pd.read_sql(query, engine)
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "total": len(df)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tiempo')
def get_tiempo():
    """Obtener períodos de tiempo"""
    try:
        engine = get_db_connection()
        query = """
        SELECT tiempo_id, año, mes, nombre_mes, trimestre, fecha 
        FROM dimtiempo 
        ORDER BY año DESC, mes DESC
        """
        df = pd.read_sql(query, engine)
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "total": len(df)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cosecha')
def get_cosecha():
    """Obtener datos de cosecha con filtros opcionales"""
    try:
        engine = get_db_connection()
        
        # Parámetros de consulta
        finca_id = request.args.get('finca_id')
        variedad_id = request.args.get('variedad_id')
        zona_id = request.args.get('zona_id')
        año = request.args.get('año')
        mes = request.args.get('mes')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Construir consulta base
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
        
        # Agregar filtros
        params = {}
        if finca_id:
            query += " AND h.id_finca = :finca_id"
            params['finca_id'] = finca_id
        if variedad_id:
            query += " AND h.codigo_variedad = :variedad_id"
            params['variedad_id'] = variedad_id
        if zona_id:
            query += " AND h.codigo_zona = :zona_id"
            params['zona_id'] = zona_id
        if año:
            query += " AND t.año = :año"
            params['año'] = año
        if mes:
            query += " AND t.mes = :mes"
            params['mes'] = mes
            
        query += " ORDER BY h.toneladas_cana_molida DESC"
        query += f" LIMIT {limit} OFFSET {offset}"
        
        df = pd.read_sql(query, engine, params=params)
        
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "total": len(df),
            "filters": {
                "finca_id": finca_id,
                "variedad_id": variedad_id,
                "zona_id": zona_id,
                "año": año,
                "mes": mes
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/estadisticas')
def get_estadisticas():
    """Obtener estadísticas generales del data mart"""
    try:
        engine = get_db_connection()
        
        # Estadísticas generales
        stats = {}
        
        # Total de registros por tabla
        tables = ['dimfinca', 'dimvariedad', 'dimzona', 'dimtiempo', 'hechos_cosecha']
        for table in tables:
            query = f"SELECT COUNT(*) as total FROM {table}"
            result = pd.read_sql(query, engine)
            stats[f"total_{table}"] = int(result['total'].iloc[0])
        
        # Estadísticas de cosecha
        query = """
        SELECT 
            COUNT(*) as total_cosechas,
            SUM(toneladas_cana_molida) as total_toneladas,
            AVG(tch) as promedio_tch,
            AVG(brix) as promedio_brix,
            AVG(sacarosa) as promedio_sacarosa,
            MIN(t.año) as año_inicio,
            MAX(t.año) as año_fin
        FROM hechos_cosecha h
        JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
        """
        result = pd.read_sql(query, engine)
        # Convertir valores numpy a tipos nativos de Python para serialización JSON
        cosecha_stats = {}
        for key, value in result.iloc[0].to_dict().items():
            if pd.isna(value):
                cosecha_stats[key] = None
            elif isinstance(value, (np.integer, np.int64)):
                cosecha_stats[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                cosecha_stats[key] = float(value)
            else:
                cosecha_stats[key] = value
        stats.update(cosecha_stats)
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cosecha/top')
def get_top_cosechas():
    """Obtener top cosechas por diferentes criterios"""
    try:
        engine = get_db_connection()
        
        criterio = request.args.get('criterio', 'toneladas')  # toneladas, tch, brix
        limit = request.args.get('limit', 10, type=int)
        
        # Mapear criterios a columnas
        criterios_map = {
            'toneladas': 'h.toneladas_cana_molida',
            'tch': 'h.tch',
            'brix': 'h.brix',
            'sacarosa': 'h.sacarosa'
        }
        
        if criterio not in criterios_map:
            return jsonify({"success": False, "error": "Criterio no válido"}), 400
        
        query = f"""
        SELECT 
            f.nombre_finca,
            v.nombre_variedad,
            z.nombre_zona,
            t.año,
            t.mes,
            h.toneladas_cana_molida,
            h.tch,
            h.brix,
            h.sacarosa,
            h.rendimiento_teorico
        FROM hechos_cosecha h
        JOIN dimfinca f ON h.id_finca = f.finca_id
        JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
        JOIN dimzona z ON h.codigo_zona = z.codigo_zona
        JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
        ORDER BY {criterios_map[criterio]} DESC
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, engine)
        
        return jsonify({
            "success": True,
            "data": df.to_dict('records'),
            "criterio": criterio,
            "total": len(df)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    print("🚀 Iniciando API SugarBI...")
    print("📊 Data Mart de Cosecha de Caña")
    print("🌐 Servidor disponible en: http://localhost:5000")
    print("📖 Documentación en: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

