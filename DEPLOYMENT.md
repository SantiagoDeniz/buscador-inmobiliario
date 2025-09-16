# 🚀 Guía de Deployment para Producción

Esta guía explica cómo desplegar el **Buscador Inmobiliario Inteligente** en la plataforma **Render** (opción principal) y otras alternativas como VPS con Docker.

---

## 📋 Tabla de Contenidos

1. [Requisitos de Producción](#requisitos-de-producción)
2. [Deployment en Render (Recomendado)](#deployment-en-render-recomendado)
3. [Configuración de Base de Datos](#configuración-de-base-de-datos)
4. [Redis para Cache y WebSockets](#redis-para-cache-y-websockets)
5. [Variables de Entorno](#variables-de-entorno)
6. [Deployment Alternativo con Docker](#deployment-alternativo-con-docker)
7. [SSL/HTTPS](#ssl-https)
8. [Monitoreo y Logs](#monitoreo-y-logs)
9. [Backup y Recuperación](#backup-y-recuperación)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Requisitos de Producción

### **Hardware Mínimo**
- **CPU**: 2 cores
- **RAM**: 4GB (8GB recomendado)
- **Almacenamiento**: 20GB SSD
- **Ancho de banda**: 100Mbps

## 🎯 Requisitos de Producción

### **Render (Opción Principal)**
- **Plan Web Service**: Pro ($25/mes) o superior
- **PostgreSQL**: Plan Starter ($7/mes) o superior
- **Redis**: Plan Starter ($7/mes) o superior

### **VPS/Cloud Alternativo**
- **CPU**: 2 cores
- **RAM**: 4GB (8GB recomendado)
- **Almacenamiento**: 20GB SSD
- **Ancho de banda**: 100Mbps

### **Servicios Externos Requeridos**
- **PostgreSQL** 13+ (Render PostgreSQL o RDS)
- **Redis** 6+ (Render Redis o Upstash)
- **Google Gemini API** (para búsquedas IA)

---

## 🌐 Deployment en Render (Recomendado)

### **1. Preparación del Repositorio**

Crear `render.yaml` en la raíz del proyecto:

```yaml
services:
  - type: web
    name: buscador-inmobiliario
    env: python
    plan: starter  # o pro para producción
    buildCommand: "pip install -r requirements.txt"
    startCommand: "daphne -b 0.0.0.0 -p 10000 buscador.asgi:application"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: buscador-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: buscador-redis
          property: connectionString

databases:
  - name: buscador-db
    plan: starter  # $7/mes

services:
  - type: redis
    name: buscador-redis  
    plan: starter  # $7/mes
```

### **2. Variables de Entorno en Render**

En el dashboard de Render, configurar:

```env
# Base de datos (auto-configurado por Render)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (auto-configurado por Render)  
REDIS_URL=rediss://user:pass@host:port

# Configuración Django
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com,tu-dominio.com
SECRET_KEY=tu-clave-secreta-muy-larga

# APIs externas
GEMINI_API_KEY=tu-clave-gemini
SCRAPINGBEE_API_KEY=tu-clave-opcional

# Configuración de producción
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### **3. Configuración de Build en Render**

```bash
# Build Command
pip install -r requirements.txt

# Start Command  
daphne -b 0.0.0.0 -p 10000 buscador.asgi:application
```

### **4. Proceso de Deployment**

1. **Push a GitHub/GitLab**:
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Conectar en Render**:
   - Crear nuevo Web Service
   - Conectar repositorio
   - Configurar variables de entorno
   - Deploy automático

3. **Verificar Deployment**:
   ```bash
   # Check de salud
   curl https://tu-app.onrender.com/health/
   
   # Verificar WebSockets
   curl https://tu-app.onrender.com/redis_diagnostic/
   ```

---

## �️ Configuración de Base de Datos

### **PostgreSQL en Render**

1. **Crear base de datos**:
   - En dashboard de Render → New → PostgreSQL
   - Plan: Starter ($7/mes)
   - Configurar nombre: `buscador-db`

2. **Configuración automática**:
   ```python
   # settings.py se autoconfigura con DATABASE_URL
   import dj_database_url
   
   DATABASES = {
       'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
   }
   ```

3. **Migraciones iniciales**:
   ```bash
   # En el build command de Render
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

### **PostgreSQL Local/VPS**

Para desarrollo o VPS alternativo:

```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Crear usuario y base de datos
sudo -u postgres psql
CREATE DATABASE buscador_inmobiliario;
CREATE USER buscador_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE buscador_inmobiliario TO buscador_user;
\q
```

---

## 📦 Redis para Cache y WebSockets

### **Redis en Render**

1. **Crear servicio Redis**:
   - En dashboard de Render → New → Redis
   - Plan: Starter ($7/mes)
   - Configurar nombre: `buscador-redis`

2. **URL automática**:
   ```python
   # settings.py
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               "hosts": [os.environ.get('REDIS_URL')],
           },
       },
   }
   ```

### **Redis con Upstash (Alternativa)**

Para proyectos que necesiten Redis independiente:

```bash
# 1. Crear cuenta en Upstash.com
# 2. Crear base de datos Redis
# 3. Copiar la REDIS_URL
# 4. Configurar en variables de entorno

REDIS_URL=rediss://default:password@host:port
```

---

## 🔧 Variables de Entorno

### **Render Environment Variables**

Configurar en el dashboard de Render:

```env
# Configuración básica
DEBUG=False
SECRET_KEY=tu-clave-muy-larga-y-segura-aqui
ALLOWED_HOSTS=tu-app.onrender.com,tu-dominio.com

# Base de datos (auto-configurado)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (auto-configurado)
REDIS_URL=rediss://user:pass@host:port

# APIs externas
GEMINI_API_KEY=tu-clave-gemini
SCRAPINGBEE_API_KEY=clave-opcional

# Configuración de seguridad
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# Configuración de archivos estáticos
USE_S3=False  # True si usas S3 para archivos
```

---

## 🐳 Deployment Alternativo con Docker

Para VPS o servidores propios:

### **1. Docker Compose para Producción**

```yaml
version: '3.8'

services:
  # Base de datos PostgreSQL
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - backend

  # Redis para cache y WebSockets
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - backend

  # Aplicación Django
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    environment:
      - DEBUG=False
      - DATABASE_ENGINE=postgresql
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./exports:/app/exports
    depends_on:
      - db
      - redis
    networks:
      - backend
      - frontend

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/static
      - media_volume:/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    networks:
      - frontend

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  frontend:
  backend:
```

### **2. Dockerfile para Producción**

Crea `Dockerfile.prod`:

```dockerfile
# Multi-stage build para optimizar imagen
FROM python:3.11-slim as builder

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Imagen de producción
FROM python:3.11-slim

# Instalar dependencias runtime
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar entorno virtual
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Crear usuario no-root
RUN groupadd -r django && useradd -r -g django django

# Configurar directorio de trabajo
WORKDIR /app

# Copiar código
COPY . .

# Cambiar permisos
RUN chown -R django:django /app
USER django

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# Script de entrada
COPY docker-entrypoint.sh /app/
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "buscador.wsgi:application"]
```

### **3. Script de Entrada**

Crea `docker-entrypoint.sh`:

```bash
#!/bin/bash
set -e

# Esperar a que PostgreSQL esté listo
echo "Esperando PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done

echo "PostgreSQL está listo"

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe
echo "Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='${ADMIN_PASSWORD:-changeme}'
    )
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
"

# Ejecutar comando pasado
exec "$@"
```

---

## 🗄️ Base de Datos PostgreSQL

### **1. Configuración de PostgreSQL**

Para PostgreSQL externo (recomendado para producción):

```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Configurar usuario y base de datos
sudo -u postgres psql

-- En PostgreSQL
CREATE DATABASE buscador_inmobiliario;
CREATE USER buscador_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE buscador_inmobiliario TO buscador_user;
ALTER USER buscador_user CREATEDB;  -- Para tests
\q
```

### **2. Configuración de Performance**

Edita `/etc/postgresql/13/main/postgresql.conf`:

```ini
# Memoria
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Conexiones
max_connections = 100

# Logging
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 1000

# Checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

### **3. Migración de SQLite a PostgreSQL**

Script para migrar datos existentes:

```python
# scripts/migrate_sqlite_to_postgres.py
import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

# Backup SQLite data
print("Exportando datos de SQLite...")
call_command('dumpdata', '--natural-foreign', '--natural-primary', 
             '--exclude=contenttypes', '--exclude=auth.permission', 
             '--output=sqlite_backup.json')

# Switch to PostgreSQL settings
os.environ['DATABASE_ENGINE'] = 'postgresql'
os.environ['DB_NAME'] = 'buscador_inmobiliario'
os.environ['DB_USER'] = 'buscador_user'
os.environ['DB_PASSWORD'] = 'secure_password'
os.environ['DB_HOST'] = 'localhost'

# Apply migrations to PostgreSQL
print("Aplicando migraciones a PostgreSQL...")
call_command('migrate')

# Load data
print("Importando datos a PostgreSQL...")
call_command('loaddata', 'sqlite_backup.json')

print("Migración completada!")
```

---

## 🔥 Redis para Cache y WebSockets

### **1. Configuración de Redis**

Para Redis externo:

```bash
# Instalar Redis
sudo apt install redis-server

# Configurar Redis para producción
sudo nano /etc/redis/redis.conf
```

Configuraciones importantes:

```ini
# Seguridad
requirepass tu_password_seguro
bind 127.0.0.1

# Persistencia
save 900 1
save 300 10
save 60 10000

# Memoria
maxmemory 512mb
maxmemory-policy allkeys-lru

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### **2. Redis con Docker**

Para Redis containerizado (más simple):

```yaml
redis:
  image: redis:7-alpine
  restart: unless-stopped
  command: redis-server --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  networks:
    - backend
```

---

## 🔧 Variables de Entorno

### **Archivo `.env` para Producción**

```env
# Django
DEBUG=False
SECRET_KEY=tu-secret-key-super-seguro-aqui
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,localhost

# Base de Datos
DATABASE_ENGINE=postgresql
DB_NAME=buscador_inmobiliario
DB_USER=buscador_user
DB_PASSWORD=password-super-seguro
DB_HOST=db  # o IP del servidor PostgreSQL
DB_PORT=5432

# Redis
REDIS_URL=redis://:password-redis@redis:6379
# o para Redis externo:
# REDIS_URL=redis://:password@localhost:6379

# APIs Externas
GEMINI_API_KEY=tu-clave-gemini-aqui
SCRAPINGBEE_API_KEY=tu-clave-scrapingbee-opcional

# Configuración de Scraping
USE_THREADS=True
MAX_WORKERS=3

# Administración
ADMIN_PASSWORD=password-admin-seguro

# Email (opcional para notificaciones)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
EMAIL_USE_TLS=True

# Monitoring (opcional)
SENTRY_DSN=https://tu-sentry-dsn-aqui
```

### **Gestión Segura de Secretos**

Para producción, usa herramientas como:
- **Docker Secrets**
- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**

---

## 🔒 Nginx como Reverse Proxy

### **Configuración de Nginx**

Crea `nginx/default.conf`:

```nginx
upstream django_app {
    server web:8000;
}

# Redirection HTTP -> HTTPS
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static Files
    location /static/ {
        alias /static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /media/;
        expires 7d;
    }

    # WebSocket Support
    location /ws/ {
        proxy_pass http://django_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Django Application
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # Para scraping largo
    }

    # Health Check
    location /health/ {
        access_log off;
        proxy_pass http://django_app;
    }
}
```

---

## 🔐 SSL/HTTPS

### **1. Certificados con Let's Encrypt**

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificados
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### **2. Configuración de Auto-renovación**

```bash
# Agregar cron job para renovación
sudo crontab -e

# Agregar línea:
0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

---

## 📊 Monitoreo y Logs

### **1. Configuración de Logging**

En `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'core.scraper': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### **2. Health Checks**

Crea `core/views.py`:

```python
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """Endpoint de health check para monitoreo"""
    status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 30)
        status['checks']['redis'] = 'ok'
    except Exception as e:
        status['checks']['redis'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)
```

### **3. Monitoreo con Prometheus + Grafana**

Agrega al `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - backend

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - backend
```

---

## 💾 Backup y Recuperación

### **1. Script de Backup**

Crea `scripts/backup.sh`:

```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="buscador_inmobiliario"

# Backup PostgreSQL
echo "Iniciando backup de PostgreSQL..."
docker exec postgres pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup archivos estáticos
echo "Backup de archivos..."
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /app/exports /app/media

# Limpiar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

### **2. Automatizar Backups**

```bash
# Cron job para backup diario
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### **3. Recuperación de Datos**

```bash
# Restaurar desde backup
docker exec -i postgres psql -U $DB_USER $DB_NAME < backup_file.sql

# Restaurar archivos
tar -xzf files_backup_DATE.tar.gz -C /
```

---

## 🚀 Deployment Commands

### **1. Deploy Inicial**

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/buscador-inmobiliario.git
cd buscador-inmobiliario

# Configurar variables de entorno
cp .env.example .env.prod
nano .env.prod

# Build y deploy
docker-compose -f docker-compose.prod.yml up --build -d

# Verificar servicios
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### **2. Actualizaciones**

```bash
# Actualizar código
git pull origin main

# Rebuild y redeploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones si es necesario
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### **3. Rollback**

```bash
# Ver tags disponibles
git tag

# Rollback a versión anterior
git checkout v1.2.0
docker-compose -f docker-compose.prod.yml up --build -d
```

---

## 🔧 Troubleshooting

### **Problemas Comunes**

#### **"502 Bad Gateway"**
```bash
# Verificar logs
docker-compose logs web
docker-compose logs nginx

# Verificar conectividad
docker-compose exec nginx ping web
```

#### **"Database connection failed"**
```bash
# Verificar PostgreSQL
docker-compose logs db
docker-compose exec db psql -U $DB_USER -l

# Verificar variables de entorno
docker-compose exec web env | grep DB_
```

#### **"WebSocket connection failed"**
```bash
# Verificar Redis
docker-compose logs redis
docker-compose exec redis redis-cli ping

# Verificar configuración Nginx
docker-compose exec nginx nginx -t
```

#### **"Out of Memory"**
```bash
# Verificar uso de memoria
docker stats

# Ajustar configuración
# Reducir workers en Gunicorn
# Ajustar memory limits en docker-compose
```

### **Performance Issues**

#### **Scraping Lento**
- Reducir `MAX_WORKERS` en configuración
- Verificar que Redis esté funcionando
- Optimizar consultas de base de datos

#### **Alta Latencia**
- Verificar configuración de Nginx
- Optimizar consultas SQL
- Implementar cache adicional

---

## 📈 Escalabilidad

### **Múltiples Instancias**

```yaml
# docker-compose.prod.yml
web:
  # ... configuración base
  deploy:
    replicas: 3
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
```

### **Load Balancer**

```nginx
upstream django_cluster {
    server web_1:8000;
    server web_2:8000;
    server web_3:8000;
}
```

---

## ✅ Checklist Pre-producción

- [ ] Variables de entorno configuradas
- [ ] SSL/HTTPS funcionando
- [ ] Backups automatizados
- [ ] Monitoring configurado
- [ ] Health checks funcionando
- [ ] Tests pasando
- [ ] Performance optimizada
- [ ] Logs configurados
- [ ] Seguridad verificada
- [ ] Documentación actualizada

---

*Con esta configuración tendrás un deployment robusto y escalable para producción.*