import os
from pathlib import Path

class Config:
    """Configuración base para la API"""
    
    # Configuración de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sugarbi-api-secret-key-2025'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Configuración de la base de datos
    @staticmethod
    def get_db_config():
        """Obtener configuración de la base de datos"""
        ruta_base = Path(__file__).parent.parent
        config_file = ruta_base / 'config' / 'config.ini'
        
        if not config_file.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_file}")
        
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        return config['mysql']
    
    # Configuración de CORS
    CORS_ORIGINS = [
        "http://localhost:3000",  # React
        "http://localhost:8080",  # Vue
        "http://localhost:4200",  # Angular
        "http://127.0.0.1:5000",  # Flask local
    ]
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
    
    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'api.log')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

