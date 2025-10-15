# 🚀 Guía de Despliegue - SugarBI

## 📋 Prerrequisitos

### Sistema Operativo
- **Linux**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Windows**: Windows Server 2019+
- **macOS**: macOS 10.15+

### Software Requerido
- **Python**: 3.13+
- **MySQL**: 8.0+
- **Nginx**: 1.18+ (opcional)
- **Git**: 2.25+

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: Puerto 80/443, 3306

## 🏗️ Opciones de Despliegue

### 1. Despliegue Local (Desarrollo)

#### Instalación Rápida
```bash
# Clonar repositorio
git clone <repository-url>
cd SugarBI

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
cp config/config.ini.example config/config.ini
# Editar config/config.ini con tus credenciales

# Inicializar base de datos
python etls/crear_tablas.py
python etls/cargar_datos.py

# Ejecutar aplicación
python web/app.py
```

#### Verificar Instalación
```bash
# Probar endpoints
curl http://localhost:5001/api/estadisticas
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "top 5 fincas"}'
```

### 2. Despliegue con Docker

#### Dockerfile
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 5001

# Comando por defecto
CMD ["python", "web/app.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  sugarbi:
    build: .
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mysql+pymysql://sugarbi:password@db:3306/sugarbi_db
    depends_on:
      - db
    volumes:
      - ./raw_data:/app/raw_data
      - ./config:/app/config

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=sugarbi_db
      - MYSQL_USER=sugarbi
      - MYSQL_PASSWORD=password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - sugarbi

volumes:
  mysql_data:
```

#### Comandos Docker
```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f sugarbi

# Ejecutar comandos en el contenedor
docker-compose exec sugarbi python etls/cargar_datos.py

# Parar servicios
docker-compose down
```

### 3. Despliegue en Servidor (Producción)

#### Configuración del Servidor

**1. Instalar dependencias del sistema**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip mysql-server nginx git

# CentOS/RHEL
sudo yum update
sudo yum install python3.13 python3-pip mysql-server nginx git
```

**2. Configurar MySQL**
```bash
# Iniciar MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# Configurar seguridad
sudo mysql_secure_installation

# Crear base de datos
sudo mysql -u root -p
```

```sql
CREATE DATABASE sugarbi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sugarbi'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON sugarbi_db.* TO 'sugarbi'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**3. Configurar aplicación**
```bash
# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash sugarbi
sudo su - sugarbi

# Clonar repositorio
git clone <repository-url> /home/sugarbi/SugarBI
cd /home/sugarbi/SugarBI

# Crear entorno virtual
python3.13 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar aplicación
cp config/config.ini.example config/config.ini
nano config/config.ini
```

**4. Configurar Gunicorn**
```bash
# Instalar Gunicorn
pip install gunicorn

# Crear archivo de configuración
nano gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "127.0.0.1:5001"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

**5. Crear servicio systemd**
```bash
sudo nano /etc/systemd/system/sugarbi.service
```

```ini
[Unit]
Description=SugarBI Web Application
After=network.target mysql.service

[Service]
User=sugarbi
Group=sugarbi
WorkingDirectory=/home/sugarbi/SugarBI
Environment="PATH=/home/sugarbi/SugarBI/venv/bin"
ExecStart=/home/sugarbi/SugarBI/venv/bin/gunicorn --config gunicorn.conf.py web.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

**6. Configurar Nginx**
```bash
sudo nano /etc/nginx/sites-available/sugarbi
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redireccionar HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Certificados SSL
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Configuración de la aplicación
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Archivos estáticos
    location /static {
        alias /home/sugarbi/SugarBI/web/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Logs
    access_log /var/log/nginx/sugarbi_access.log;
    error_log /var/log/nginx/sugarbi_error.log;
}
```

**7. Activar servicios**
```bash
# Habilitar sitio de Nginx
sudo ln -s /etc/nginx/sites-available/sugarbi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Inicializar base de datos
cd /home/sugarbi/SugarBI
source venv/bin/activate
python etls/crear_tablas.py
python etls/cargar_datos.py

# Iniciar aplicación
sudo systemctl start sugarbi
sudo systemctl enable sugarbi

# Verificar estado
sudo systemctl status sugarbi
```

### 4. Despliegue en la Nube

#### AWS EC2
```bash
# Crear instancia EC2 (t3.medium o superior)
# Conectar por SSH
ssh -i tu-key.pem ubuntu@tu-ip

# Seguir pasos del despliegue en servidor
# Configurar Security Groups para puertos 80, 443, 22
```

#### Google Cloud Platform
```bash
# Crear instancia Compute Engine
gcloud compute instances create sugarbi-server \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium \
    --zone=us-central1-a

# Conectar por SSH
gcloud compute ssh sugarbi-server --zone=us-central1-a
```

#### Azure
```bash
# Crear VM
az vm create \
    --resource-group myResourceGroup \
    --name sugarbi-vm \
    --image UbuntuLTS \
    --size Standard_B2s \
    --admin-username azureuser

# Conectar por SSH
ssh azureuser@tu-ip
```

## 🔧 Configuración de Producción

### Variables de Entorno
```bash
# /home/sugarbi/.env
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=mysql+pymysql://sugarbi:password@localhost/sugarbi_db
SECRET_KEY=tu-clave-secreta-muy-segura
```

### Configuración de Seguridad

**1. Firewall**
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**2. SSL/TLS**
```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

**3. Backup de Base de Datos**
```bash
# Script de backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u sugarbi -p sugarbi_db > /backup/sugarbi_$DATE.sql
find /backup -name "sugarbi_*.sql" -mtime +7 -delete
```

### Monitoreo

**1. Logs**
```bash
# Ver logs de la aplicación
sudo journalctl -u sugarbi -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/sugarbi_access.log
sudo tail -f /var/log/nginx/sugarbi_error.log
```

**2. Monitoreo de Recursos**
```bash
# Instalar htop
sudo apt install htop

# Monitorear recursos
htop
df -h
free -h
```

## 🔄 Actualizaciones

### Actualización de Código
```bash
# Conectar al servidor
ssh usuario@tu-servidor

# Ir al directorio de la aplicación
cd /home/sugarbi/SugarBI

# Hacer backup
cp -r . ../SugarBI_backup_$(date +%Y%m%d)

# Actualizar código
git pull origin main

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar aplicación
sudo systemctl restart sugarbi
```

### Actualización de Base de Datos
```bash
# Backup antes de actualizar
mysqldump -u sugarbi -p sugarbi_db > backup_before_update.sql

# Ejecutar migraciones (si las hay)
python etls/migrate_database.py

# Verificar integridad
python etls/verificar_todas_tablas.py
```

## 🚨 Solución de Problemas

### Problemas Comunes

**1. Error de Conexión a Base de Datos**
```bash
# Verificar estado de MySQL
sudo systemctl status mysql

# Verificar configuración
mysql -u sugarbi -p -e "SHOW DATABASES;"
```

**2. Error 502 Bad Gateway**
```bash
# Verificar estado de la aplicación
sudo systemctl status sugarbi

# Ver logs
sudo journalctl -u sugarbi -n 50
```

**3. Error de Permisos**
```bash
# Corregir permisos
sudo chown -R sugarbi:sugarbi /home/sugarbi/SugarBI
sudo chmod -R 755 /home/sugarbi/SugarBI
```

**4. Error de Memoria**
```bash
# Verificar uso de memoria
free -h
ps aux --sort=-%mem | head

# Ajustar workers de Gunicorn
# Editar gunicorn.conf.py
workers = 2  # Reducir número de workers
```

### Comandos de Diagnóstico
```bash
# Estado general del sistema
sudo systemctl status sugarbi nginx mysql

# Verificar puertos
sudo netstat -tlnp | grep :5001
sudo netstat -tlnp | grep :80

# Verificar logs
sudo journalctl -u sugarbi --since "1 hour ago"
sudo tail -f /var/log/nginx/sugarbi_error.log

# Verificar base de datos
mysql -u sugarbi -p -e "SELECT COUNT(*) FROM hechos_cosecha;"
```

## 📊 Optimización

### Optimización de Base de Datos
```sql
-- Crear índices
CREATE INDEX idx_hechos_finca ON hechos_cosecha(id_finca);
CREATE INDEX idx_hechos_tiempo ON hechos_cosecha(codigo_tiempo);
CREATE INDEX idx_hechos_variedad ON hechos_cosecha(codigo_variedad);

-- Optimizar tablas
OPTIMIZE TABLE hechos_cosecha;
ANALYZE TABLE hechos_cosecha;
```

### Optimización de Aplicación
```python
# Configuración de Gunicorn optimizada
bind = "127.0.0.1:5001"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### Optimización de Nginx
```nginx
# Configuración optimizada
worker_processes auto;
worker_connections 1024;

# Compresión
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# Cache
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 📈 Escalabilidad

### Escalado Horizontal
- **Load Balancer**: Nginx/HAProxy
- **Múltiples instancias**: Docker Swarm/Kubernetes
- **Base de datos**: MySQL Cluster/Replicación

### Escalado Vertical
- **CPU**: Aumentar cores
- **RAM**: Aumentar memoria
- **Storage**: SSD con más IOPS

## 🔐 Seguridad

### Medidas de Seguridad
- **Firewall**: Configurar reglas estrictas
- **SSL/TLS**: Certificados válidos
- **Autenticación**: Implementar JWT/API keys
- **Backup**: Backups automáticos y encriptados
- **Monitoreo**: Logs y alertas de seguridad

---

**Nota**: Esta guía asume un entorno Linux. Para Windows Server, adaptar los comandos según corresponda.

