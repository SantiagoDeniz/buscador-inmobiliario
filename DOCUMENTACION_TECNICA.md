# 📚 Documentación Técnica - Buscador Inmobiliario

## 🎯 Migración Completa a Base de Datos Relacional

### 📋 Resumen de la Migración

El sistema Buscador Inmobiliario ha sido completamente migrado de un sistema basado en archivos JSON a una arquitectura de base de datos relacional moderna. Esta migración proporciona mayor escalabilidad, integridad de datos y capacidades de consulta avanzadas.

---

## 🗃️ Arquitectura de Base de Datos

### Modelos Principales

#### 1. **Inmobiliaria**
```python
class Inmobiliaria(models.Model):
    nombre = models.CharField(max_length=200)
    plan = models.CharField(max_length=50, default='básico')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. **Usuario**
```python
class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 3. **Plataforma**
```python
class Plataforma(models.Model):
    nombre = models.CharField(max_length=100)
    url = models.URLField()
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 4. **Búsqueda** (Modelo Principal)
```python
class Busqueda(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    nombre_busqueda = models.CharField(max_length=200)
    texto_original = models.TextField()
    filtros = models.JSONField(default=dict)
    guardado = models.BooleanField(default=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 5. **Palabra Clave**
```python
class PalabraClave(models.Model):
    texto = models.CharField(max_length=100, unique=True)
    idioma = models.CharField(max_length=10, default='es')
    sinonimos = models.TextField(blank=True, default='')  # JSON string para SQLite
    
    @property
    def sinonimos_list(self):
        """Convertir string JSON a lista"""
        return json.loads(self.sinonimos) if self.sinonimos else []
    
    def set_sinonimos(self, lista):
        """Convertir lista a string JSON"""
        self.sinonimos = json.dumps(lista)
```

#### 6. **Propiedad**
```python
class Propiedad(models.Model):
    url = models.URLField(unique=True)
    titulo = models.CharField(max_length=500, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    plataforma = models.ForeignKey(Plataforma, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 7. **Relaciones**
- **BusquedaPalabraClave**: Many-to-Many entre Búsquedas y Palabras Clave
- **ResultadoBusqueda**: Relaciona Búsquedas con Propiedades encontradas

---

## 🔧 Sistema de Gestión (search_manager.py)

### Funciones Principales

#### **Gestión de Búsquedas**
```python
def get_all_searches() -> List[Dict[str, Any]]
def get_search(search_id: str) -> Optional[Dict[str, Any]]
def save_search(search_data: Dict[str, Any]) -> str
def delete_search(search_id: str) -> bool
```

#### **Procesamiento de Palabras Clave**
```python
def procesar_keywords(texto_busqueda: str) -> List[Dict[str, Any]]
def get_or_create_palabra_clave(texto: str, idioma: str = 'es') -> PalabraClave
def generar_sinonimos(palabra: str) -> List[str]
```

#### **Sistema de Coincidencias**
```python
def buscar_coincidencias(busqueda_id: str, propiedades: List[Dict]) -> List[Dict]
def verificar_coincidencia(palabras_clave_rel, propiedad_data: Dict) -> Dict
```

#### **Estadísticas y Reportes**
```python
def get_search_stats() -> Dict[str, Any]
def get_popular_keywords(limit: int = 10) -> List[Dict[str, Any]]
```

### Funciones de Compatibilidad
Para mantener compatibilidad con el sistema anterior:

```python
def load_results(search_id: str) -> List[Dict]  # Compatible con storage.py
def save_results(search_id: str, results: List[Dict]) -> bool
def create_search(search_data: Dict[str, Any]) -> Dict[str, Any]  # Compatible con consumers.py
def update_search(search_id: str, data: Dict[str, Any]) -> bool
```

---

## ⚡ Integración WebSocket/Redis

### Configuración Redis
```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}
```

### Consumer WebSocket
El `SearchProgressConsumer` en `consumers.py` ha sido actualizado para usar las nuevas funciones de base de datos:

```python
# En consumers.py
from core.search_manager import create_search, update_search

# Crear búsqueda durante WebSocket
created_search = create_search(search_data)
saved_search_id = created_search.get('id')

# Actualizar con resultados
update_search(saved_search_id, {'results': resultados})
```

---

## 🧪 Sistema de Testing

### Cobertura de Tests

#### **Tests de Modelos** (`TestModelsDatabase`)
- ✅ Creación de inmobiliarias, usuarios, plataformas
- ✅ Búsquedas con filtros JSON
- ✅ Sistema de sinónimos en palabras clave
- ✅ Relaciones many-to-many

#### **Tests de Search Manager** (`TestSearchManagerDatabase`)
- ✅ CRUD completo de búsquedas
- ✅ Procesamiento de palabras clave
- ✅ Sistema de resultados
- ✅ Funciones de compatibilidad

#### **Tests de Integración** (`TestRedisChannelsIntegration`)
- ✅ Channel Layer Redis disponible
- ✅ Integración WebSocket Consumer
- ✅ Flujo completo de búsqueda

#### **Tests de Performance** (`TestDatabasePerformance`)
- ✅ Consultas optimizadas (<1 segundo)
- ✅ Indexado de palabras clave
- ✅ Bulk operations

### Ejecutar Tests
```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Tests completos
python manage.py test core.tests_database

# Tests específicos
python manage.py test core.tests_database.TestSearchManagerDatabase

# Con verbosidad
python manage.py test core.tests_database -v 2
```

---

## 🚀 Despliegue y Configuración

### Base de Datos

#### **Desarrollo** (SQLite)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### **Producción** (PostgreSQL)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Migraciones
```bash
# Crear migraciones
python manage.py makemigrations core

# Aplicar migraciones
python manage.py migrate

# Cargar datos iniciales
python manage.py loaddata core/fixtures/initial_data.json

# Crear datos de ejemplo
python manage.py create_sample_data
```

### Variables de Entorno Requeridas
```env
# Base de datos
DB_NAME=buscador_inmobiliario
DB_USER=usuario
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis/WebSocket
REDIS_URL=redis://localhost:6379
CHANNEL_LAYERS_BACKEND=channels_redis.core.RedisChannelLayer

# API Keys
GEMINI_API_KEY=your_gemini_api_key
```

---

## 📊 Performance y Optimizaciones

### Consultas Optimizadas
```python
# En lugar de múltiples consultas
for busqueda in Busqueda.objects.all():
    print(busqueda.usuario.nombre)  # N+1 queries

# Usar select_related
for busqueda in Busqueda.objects.select_related('usuario').all():
    print(busqueda.usuario.nombre)  # 1 query

# Para relaciones many-to-many
busqueda = Busqueda.objects.prefetch_related(
    'busquedapalabraclave_set__palabra_clave'
).get(id=search_id)
```

### Índices Recomendados
```python
# En models.py
class Busqueda(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'created_at']),
            models.Index(fields=['guardado', 'created_at']),
        ]

class PalabraClave(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['texto']),
            models.Index(fields=['idioma']),
        ]
```

---

## 🔍 Admin Panel

### Configuración Admin
Acceso completo desde Django Admin:
- **Inmobiliarias**: Gestión de planes y empresas
- **Usuarios**: CRUD de usuarios por inmobiliaria
- **Búsquedas**: Visualización de búsquedas guardadas con filtros
- **Palabras Clave**: Gestión de sinónimos
- **Propiedades**: Resultados de scraping
- **Resultados**: Relación búsqueda-propiedad

### URL Admin
```
http://localhost:10000/admin/
```

---

## 🛡️ Seguridad y Buenas Prácticas

### Validación de Datos
- ✅ Validación de campos requeridos en modelos
- ✅ Unique constraints en URLs y emails
- ✅ Sanitización de texto en procesamiento de palabras clave
- ✅ JSONField para datos estructurados

### Transacciones
```python
from django.db import transaction

@transaction.atomic
def save_search_with_keywords(search_data):
    # Operaciones atómicas garantizadas
    busqueda = Busqueda.objects.create(...)
    for keyword in keywords:
        BusquedaPalabraClave.objects.create(...)
```

### Logs y Debugging
```python
import logging
logger = logging.getLogger(__name__)

def save_search(search_data):
    logger.info(f"Guardando búsqueda: {search_data['nombre_busqueda']}")
    # ...
```

---

## 📈 Métricas y Estadísticas

### Estadísticas Disponibles
```python
stats = get_search_stats()
# Retorna:
{
    'total_searches': 15,
    'saved_searches': 12,
    'total_keywords': 45,
    'total_properties': 120,
    'total_results': 89,
    'successful_results': 67
}
```

### Palabras Clave Populares
```python
popular = get_popular_keywords(limit=10)
# Retorna las 10 palabras más utilizadas con conteos
```

---

## 🔄 Migración de Datos Existentes

### Script de Migración
```python
# management/commands/migrate_json_to_db.py
from django.core.management.base import BaseCommand
from core.search_manager import save_search
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Leer archivos JSON existentes
        with open('user_data/searches.json', 'r') as f:
            searches = json.load(f)
        
        # Migrar a base de datos
        for search in searches:
            save_search({
                'nombre_busqueda': search['name'],
                'texto_original': search['original_text'],
                'palabras_clave': search['keywords'],
                'filtros': search.get('filters', {}),
                'guardado': True
            })
```

---

## ⚠️ Troubleshooting

### Errores Comunes

#### 1. **Channel Layer No Disponible**
```bash
# Instalar channels_redis
pip install channels_redis

# Verificar Redis
python manage.py shell -c "from channels.layers import get_channel_layer; print(get_channel_layer())"
```

#### 2. **Errores de Migración**
```bash
# Reset migraciones si es necesario
python manage.py migrate core zero
python manage.py migrate core
```

#### 3. **Performance Lenta**
- Revisar consultas con Django Debug Toolbar
- Añadir índices necesarios
- Usar select_related/prefetch_related

#### 4. **Tests Fallando**
```bash
# Ejecutar tests con debugging
python manage.py test core.tests_database --debug-mode -v 2

# Tests específicos
python manage.py test core.tests_database.TestSearchManagerDatabase.test_save_search
```

---

## 🎯 Próximos Pasos

### Mejoras Planificadas
1. **🔍 Búsqueda Fulltext**: Implementar búsqueda PostgreSQL fulltext
2. **📊 Dashboard Analytics**: Métricas avanzadas y visualizaciones
3. **🤖 ML Integration**: Mejores algoritmos de matching
4. **📱 API REST**: Endpoints para aplicaciones móviles
5. **🔄 Background Jobs**: Celery para scraping asíncrono
6. **📈 Monitoring**: Logging avanzado y alertas

### Optimizaciones de Performance
1. **Redis Caching**: Cache de búsquedas frecuentes
2. **Database Connection Pooling**: Optimizar conexiones
3. **CDN Integration**: Assets estáticos
4. **Load Balancing**: Preparación para múltiples instancias

---

## 📞 Soporte

Para problemas técnicos o preguntas sobre la implementación:

1. **Revisar logs**: `python manage.py shell` para debugging
2. **Ejecutar tests**: Verificar funcionamiento con test suite
3. **Consultar documentación**: Este documento y docstrings en código
4. **Admin panel**: Verificar datos desde interfaz administrativa

---

*Documentación actualizada: 27 de agosto de 2025*  
*Versión del sistema: 2.0.0 (Base de datos relacional)*
