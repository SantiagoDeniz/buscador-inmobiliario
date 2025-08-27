# README_POSTGRESQL.md

# 🐘 Migración a PostgreSQL

Este documento explica cómo migrar el proyecto de SQLite a PostgreSQL usando Docker.

## 📋 Prerrequisitos

- Python 3.10+ con entorno virtual activado
- Docker Desktop instalado y funcionando
- Dependencias del proyecto instaladas (`pip install -r requirements.txt`)

## 🚀 Proceso de Migración Automática

### Opción 1: Configuración completa automática

```bash
# 1. Configurar PostgreSQL con Docker
python scripts/setup_postgresql.py

# 2. Migrar datos de SQLite a PostgreSQL
python scripts/migrate_to_postgresql.py

# 3. Crear datos de ejemplo (opcional)
python manage.py create_sample_data

# 4. Iniciar servidor
python manage.py runserver
```

### Opción 2: Paso a paso manual

#### Paso 1: Configurar Docker Compose

```bash
# Iniciar servicios PostgreSQL y Redis
docker-compose up -d db redis

# Verificar que PostgreSQL esté funcionando
docker-compose ps
```

#### Paso 2: Actualizar configuración

Modificar `.env`:
```env
DATABASE_ENGINE=postgresql
DB_NAME=buscador_inmobiliario
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=localhost
DB_PORT=5432
```

#### Paso 3: Exportar datos de SQLite (si existen)

```bash
# Exportar datos actuales
python manage.py export_sqlite_data --backup-first
```

#### Paso 4: Aplicar migraciones

```bash
# Aplicar migraciones a PostgreSQL
python manage.py migrate

# Cargar datos exportados (si existen)
python manage.py loaddata core/fixtures/exported_data.json
```

#### Paso 5: Verificar migración

```bash
# Crear superusuario
python manage.py createsuperuser

# Verificar datos
python manage.py shell -c "from core.models import *; print(f'Búsquedas: {Busqueda.objects.count()}')"
```

## 🔧 Comandos de Gestión

### Comandos Django personalizados

- `migrate_to_postgresql`: Migración automática completa
- `export_sqlite_data`: Exportar datos desde SQLite
- `create_sample_data`: Crear datos de ejemplo

### Comandos Docker

```bash
# Ver logs de PostgreSQL
docker-compose logs db

# Conectar a PostgreSQL
docker-compose exec db psql -U postgres -d buscador_inmobiliario

# Backup de base de datos
docker-compose exec db pg_dump -U postgres -d buscador_inmobiliario > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U postgres -d buscador_inmobiliario < backup.sql

# Detener servicios
docker-compose down
```

## 📊 Configuración de Docker Compose

El archivo `docker-compose.yml` incluye:

- **PostgreSQL 15**: Base de datos principal
- **Redis 7**: Para WebSocket channels y cache
- **pgAdmin** (opcional): Interface web para PostgreSQL

### Servicios disponibles

| Servicio | Puerto | URL |
|----------|--------|-----|
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| pgAdmin | 5050 | http://localhost:5050 |

## 🎯 Optimizaciones PostgreSQL

### Índices agregados

Los modelos incluyen índices optimizados para PostgreSQL:

```python
class Busqueda(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['usuario', '-created_at']),
            models.Index(fields=['guardado', '-created_at']),
        ]

class PalabraClave(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['texto']),
            models.Index(fields=['idioma']),
        ]

class Propiedad(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['plataforma', '-created_at']),
        ]
```

### Configuraciones de rendimiento

En `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'statement_timeout': 30000,
        },
        'CONN_MAX_AGE': 600,  # Reutilizar conexiones
    }
}
```

## 🛡️ Backup y Recuperación

### Backup automático

```bash
# Crear backup completo
docker-compose exec db pg_dump -U postgres -d buscador_inmobiliario > backup_$(date +%Y%m%d).sql

# Backup solo esquema
docker-compose exec db pg_dump -U postgres -d buscador_inmobiliario --schema-only > schema.sql

# Backup solo datos
docker-compose exec db pg_dump -U postgres -d buscador_inmobiliario --data-only > data.sql
```

### Restauración

```bash
# Restaurar backup completo
docker-compose exec -T db psql -U postgres -d buscador_inmobiliario < backup.sql

# Crear nueva base de datos y restaurar
docker-compose exec db createdb -U postgres nueva_bd
docker-compose exec -T db psql -U postgres -d nueva_bd < backup.sql
```

## 🔍 Solución de Problemas

### Error de conexión

```bash
# Verificar que PostgreSQL esté funcionando
docker-compose ps
docker-compose logs db

# Probar conexión
docker-compose exec db pg_isready -U postgres
```

### Error de migraciones

```bash
# Resetear migraciones
python manage.py migrate core zero
python manage.py migrate

# Forzar recreación
python manage.py migrate --run-syncdb
```

### Error de permisos

```bash
# Verificar usuario y permisos
docker-compose exec db psql -U postgres -c "\du"
docker-compose exec db psql -U postgres -c "\l"
```

### Limpiar y reiniciar

```bash
# Detener y limpiar todo
docker-compose down -v
docker-compose up -d db

# Recrear base de datos
docker-compose exec db dropdb -U postgres buscador_inmobiliario
docker-compose exec db createdb -U postgres buscador_inmobiliario
python manage.py migrate
```

## 📈 Monitoreo

### Consultas de estado

```sql
-- Conexiones activas
SELECT count(*) FROM pg_stat_activity;

-- Tamaño de tablas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname='public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Estadísticas de uso
SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del 
FROM pg_stat_user_tables;
```

### Logs importantes

```bash
# Ver logs en tiempo real
docker-compose logs -f db

# Filtrar errores
docker-compose logs db | grep ERROR
```

## 🎉 Verificación Final

Después de la migración, verificar:

1. ✅ Conexión PostgreSQL exitosa
2. ✅ Migraciones aplicadas
3. ✅ Datos migrados correctamente
4. ✅ Tests funcionando
5. ✅ Servidor Django funcionando

```bash
# Test rápido
python manage.py test core.tests_database
python manage.py runserver 0.0.0.0:8000
```

¡La migración a PostgreSQL está completa! 🐘
