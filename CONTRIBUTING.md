# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir al **Buscador Inmobiliario Inteligente**! Esta guía te ayudará a empezar y seguir las mejores prácticas del proyecto.

---

## 📋 Tabla de Contenidos

1. [Código de Conducta](#código-de-conducta)
2. [Tipos de Contribuciones](#tipos-de-contribuciones)
3. [Setup para Desarrolladores](#setup-para-desarrolladores)
4. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
5. [Flujo de Desarrollo](#flujo-de-desarrollo)
6. [Estándares de Código](#estándares-de-código)
7. [Testing](#testing)
8. [Documentación](#documentación)
9. [Pull Request Process](#pull-request-process)

---

## 🤝 Código de Conducta

Este proyecto se adhiere a un código de conducta que todos los contribuidores deben seguir:

- ✅ **Sé respetuoso**: Trata a todos con dignidad y respeto
- ✅ **Sé inclusivo**: Acepta diferentes perspectivas y experiencias
- ✅ **Sé constructivo**: Ofrece críticas constructivas y ayuda
- ✅ **Sé paciente**: Entiende que todos estamos aprendiendo
- ❌ **No toleres**: Discriminación, acoso o comportamiento tóxico

---

## 🎯 Tipos de Contribuciones

### 🐛 **Reportar Bugs**
- Usa el template de bug report en GitHub Issues
- Incluye pasos para reproducir el problema
- Agrega capturas de pantalla si es relevante
- Especifica tu entorno (OS, Python version, etc.)

### 💡 **Proponer Features**
- Usa el template de feature request
- Explica el problema que resuelve
- Describe la solución propuesta
- Considera alternativas y limitaciones

### 🔧 **Contribuir Código**
- Arreglos de bugs
- Nuevas funcionalidades
- Mejoras de performance
- Refactoring y limpieza de código

### 📚 **Mejorar Documentación**
- Corregir errores en docs
- Agregar ejemplos
- Mejorar claridad
- Traducir contenido

### 🧪 **Testing**
- Escribir tests para funcionalidades existentes
- Mejorar cobertura de tests
- Reportar casos edge encontrados

---

## 🛠️ Setup para Desarrolladores

### **Requisitos Previos**
- Python 3.10+
- Git
- VS Code (recomendado)
- Docker (opcional, para BD local)

### **1. Fork y Clone**
```bash
# Fork el repo en GitHub primero
git clone https://github.com/TU_USERNAME/buscador-inmobiliario.git
cd buscador-inmobiliario

# Agrega el upstream
git remote add upstream https://github.com/ORIGINAL_OWNER/buscador-inmobiliario.git
```

### **2. Entorno de Desarrollo**
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno
# Windows
.venv\Scripts\activate
# Linux/Mac  
source .venv/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe
```

### **3. Configuración de Base de Datos**
```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Cargar datos de ejemplo (opcional)
python manage.py loaddata fixtures/sample_data.json
```

### **4. Variables de Entorno**
Crea un archivo `.env` en la raíz:
```env
# Desarrollo
DEBUG=True
SECRET_KEY=tu-secret-key-para-desarrollo

# IA (opcional pero recomendado)
GEMINI_API_KEY=tu-clave-de-gemini

# Redis (opcional)
REDIS_URL=redis://localhost:6379

# Scraping (opcional)
SCRAPINGBEE_API_KEY=tu-clave-opcional
USE_THREADS=True
```

### **5. Verificar Setup**
```bash
# Ejecutar tests
python manage.py test

# Ejecutar servidor
python manage.py runserver

# Verificar que funciona en http://localhost:8000
```

---

## 🏗️ Arquitectura del Proyecto

### **Estructura de Directorios**
```
buscador-inmobiliario/
├── buscador/                 # Configuración Django
│   ├── settings.py          # Settings del proyecto
│   ├── urls.py              # URLs principales
│   └── asgi.py              # Configuración ASGI/WebSocket
├── core/                    # App principal
│   ├── scraper/             # Paquete modular de scraping
│   │   ├── __init__.py     # API pública
│   │   ├── run.py          # Orquestador
│   │   ├── mercadolibre.py # Lógica específica ML
│   │   ├── browser.py      # Gestión navegadores
│   │   ├── extractors.py   # Extracción de datos
│   │   └── ...
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas HTTP/WebSocket
│   ├── consumers.py        # WebSocket consumers
│   ├── search_manager.py   # Lógica de búsquedas
│   └── ...
├── static/                  # Archivos estáticos
├── templates/               # Templates HTML
└── exports/                 # Exportaciones CSV
```

### **Componentes Clave**

#### **Scraper Modular (`core/scraper/`)**
- ✅ **API unificada**: Importa desde `core.scraper`
- ✅ **Múltiples estrategias**: Selenium, Requests/BS4, ScrapingBee
- ✅ **Rate limiting**: Scraping responsable
- ✅ **Error handling**: Resilente a fallos parciales

#### **Base de Datos Relacional**
- ✅ **Modelos normalizados**: Busqueda, Propiedad, PalabraClave
- ✅ **Búsquedas unificadas**: Sistema guardado vs temporal
- ✅ **Performance**: Índices y consultas optimizadas

#### **Sistema en Tiempo Real**
- ✅ **WebSockets**: Django Channels + Redis
- ✅ **Fallback HTTP**: Para cuando falla WebSocket
- ✅ **Progreso granular**: Updates cada fase del scraping

---

## 🔄 Flujo de Desarrollo

### **1. Configurar Trabajo**
```bash
# Asegúrate de estar en main actualizado
git checkout main
git pull upstream main

# Crear rama para tu feature
git checkout -b feature/nombre-descriptivo
# o
git checkout -b bugfix/descripcion-bug
```

### **2. Hacer Cambios**
- 📝 Haz commits pequeños y descriptivos
- 🧪 Ejecuta tests frecuentemente
- 📚 Actualiza documentación si es necesario
- 🎯 Sigue los estándares de código

### **3. Testing Local**
```bash
# Tests unitarios
python manage.py test

# Tests específicos
python manage.py test core.tests_database

# Verificar scraper
python scripts/smoke_run_scraper.py

# Linter (si está configurado)
flake8 core/
# o
pylint core/
```

### **4. Preparar PR**
```bash
# Rebase con main (opcional pero recomendado)
git rebase upstream/main

# Push a tu fork
git push origin feature/nombre-descriptivo
```

---

## 📝 Estándares de Código

### **Python (PEP 8)**
```python
# ✅ Buenos nombres de variables
user_searches = get_all_searches()
property_count = len(properties)

# ✅ Docstrings descriptivos
def procesar_keywords(texto: str) -> List[Dict]:
    """
    Procesa texto libre y extrae keywords normalizadas.
    
    Args:
        texto: Texto de búsqueda del usuario
        
    Returns:
        Lista de diccionarios con keywords procesadas
    """
    pass

# ✅ Type hints cuando sea posible
def save_search(search_data: Dict[str, Any]) -> str:
    pass

# ✅ Imports organizados
# Standard library
import json
import time

# Third party
import requests
from django.db import models

# Local
from core.models import Busqueda
from core.scraper import run_scraper
```

### **JavaScript**
```javascript
// ✅ Usar const/let en lugar de var
const searchButton = document.getElementById('search-btn');

// ✅ Nombres descriptivos
function updateProgressDisplay(progressData) {
    // ...
}

// ✅ Comentarios cuando sea necesario
// Conectar WebSocket para progreso en tiempo real
const socket = new WebSocket(wsUrl);
```

### **HTML/CSS**
```html
<!-- ✅ Estructura semántica -->
<main class="search-container">
    <section class="search-form">
        <h2>Búsqueda Inteligente</h2>
        <!-- ... -->
    </section>
</main>

<!-- ✅ Clases descriptivas -->
<div class="property-card property-card--new">
    <img class="property-card__image" alt="Apartamento en Pocitos">
    <div class="property-card__details">
        <!-- ... -->
    </div>
</div>
```

---

## 🧪 Testing

### **Estructura de Tests**
```
core/
├── tests.py                 # Tests legacy (mantenidos)
├── tests_database.py        # Tests de modelos y BD
├── test_procesar_keywords.py # Tests específicos keywords
└── tests/                   # Tests organizados (futuro)
    ├── test_models.py
    ├── test_views.py
    ├── test_scraper.py
    └── test_search_manager.py
```

### **Tipos de Tests**

#### **Tests Unitarios**
```python
from django.test import TestCase
from core.models import Busqueda, PalabraClave

class TestPalabraClave(TestCase):
    def test_sinonimos_property(self):
        """Test que la propiedad sinonimos_list funciona correctamente"""
        palabra = PalabraClave.objects.create(
            texto='luminoso',
            sinonimos='["luminosa", "iluminado", "brillante"]'
        )
        expected = ["luminosa", "iluminado", "brillante"]
        self.assertEqual(palabra.sinonimos_list, expected)
```

#### **Tests de Integración**
```python
class TestSearchFlow(TestCase):
    def test_complete_search_flow(self):
        """Test del flujo completo de búsqueda"""
        # 1. Crear búsqueda
        search_data = {
            'nombre_busqueda': 'Test Search',
            'texto_original': 'apartamento pocitos',
            'filtros': {'tipo': 'apartamento'},
            'guardado': True
        }
        search_id = save_search(search_data)
        
        # 2. Verificar que se guardó
        search = get_search(search_id)
        self.assertIsNotNone(search)
        
        # 3. Verificar relaciones
        self.assertEqual(search['nombre_busqueda'], 'Test Search')
```

### **Ejecutar Tests**
```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test core.tests_database.TestSearchManagerDatabase

# Con verbosidad
python manage.py test -v 2

# Con coverage (si está instalado)
coverage run --source='.' manage.py test
coverage report
```

### **Agregar Nuevos Tests**
1. ✅ **Test casos normales**: El happy path
2. ✅ **Test casos límite**: Valores extremos
3. ✅ **Test errores**: Manejo de excepciones
4. ✅ **Test performance**: Para funciones críticas
5. ✅ **Mocks cuando sea necesario**: Para servicios externos

---

## 📚 Documentación

### **Que Documentar**
- ✅ **APIs públicas**: Funciones principales del scraper
- ✅ **Modelos complejos**: Campos JSON, relaciones
- ✅ **Procesos de negocio**: Flujo de búsquedas, keywords
- ✅ **Configuración**: Variables de entorno, deployment
- ✅ **Troubleshooting**: Problemas comunes

### **Formato de Documentación**
```python
def procesar_keywords(texto_busqueda: str) -> List[Dict[str, Any]]:
    """
    Procesa texto libre del usuario y extrae keywords normalizadas.
    
    Este método implementa el pipeline completo de procesamiento:
    1. Normalización de texto (acentos, minúsculas)
    2. Tokenización inteligente
    3. Stemming básico en español
    4. Generación de sinónimos automáticos
    5. Persistencia en BD con relaciones
    
    Args:
        texto_busqueda: Texto libre ingresado por el usuario.
                       Ejemplo: "apartamento luminoso con terraza"
    
    Returns:
        Lista de diccionarios con keywords procesadas:
        [
            {
                'texto': 'luminoso',
                'stem': 'lumin',
                'sinonimos': ['luminosa', 'iluminado'],
                'peso': 0.8
            }
        ]
    
    Raises:
        ValidationError: Si el texto está vacío o tiene formato inválido
    
    Example:
        >>> keywords = procesar_keywords("apartamento luminoso")
        >>> len(keywords)
        2
        >>> keywords[0]['texto']
        'apartamento'
    """
```

### **Actualizar Documentación**
Cuando hagas cambios, actualiza también:
- 📝 **Docstrings** en el código
- 📚 **README.md** si cambia la instalación/uso
- 🔧 **DOCUMENTACION_TECNICA.md** si cambia arquitectura
- 🤖 **copilot-instructions.md** si cambian patrones de desarrollo

---

## 🔄 Pull Request Process

### **1. Antes de Enviar**
- ✅ Los tests pasan localmente
- ✅ El código sigue los estándares
- ✅ La documentación está actualizada
- ✅ Los commits son descriptivos
- ✅ La rama está actualizada con main

### **2. Template de PR**
```markdown
## 📝 Descripción
Breve descripción de los cambios realizados.

## 🎯 Tipo de Cambio
- [ ] Bug fix (cambio que arregla un problema sin romper funcionalidad existente)
- [ ] New feature (cambio que agrega funcionalidad sin romper existente)
- [ ] Breaking change (cambio que podría causar que funcionalidad existente no funcione)
- [ ] Documentation update (cambios solo en documentación)

## 🧪 Testing
- [ ] Los tests existentes pasan
- [ ] Agregué tests para los cambios
- [ ] Probé manualmente la funcionalidad

## 📋 Checklist
- [ ] Mi código sigue los estándares del proyecto
- [ ] Hice self-review de mi código
- [ ] Comenté código complejo donde era necesario
- [ ] Actualicé documentación relevante
- [ ] Los commits son descriptivos

## 📸 Screenshots (si aplica)
Agrega capturas si hay cambios visuales.

## 🔗 Issues Relacionados
Fixes #123
```

### **3. Proceso de Review**
1. 👥 **Automated checks**: CI debe pasar
2. 🔍 **Peer review**: Al menos 1 reviewer aprueba
3. 💬 **Feedback**: Responde a comentarios constructivamente
4. 🔄 **Iterations**: Haz cambios solicitados
5. ✅ **Merge**: Una vez aprobado, será mergeado

### **4. Después del Merge**
```bash
# Limpiar rama local
git checkout main
git pull upstream main
git branch -d feature/nombre-descriptivo

# Limpiar rama remota
git push origin --delete feature/nombre-descriptivo
```

---

## 🚀 Áreas Que Necesitan Contribuciones

### **Alta Prioridad**
- 🐛 **Mejoras en error handling** del scraper
- 🧪 **Aumentar test coverage** (actualmente ~80%)
- 📊 **Dashboard de métricas** para análisis
- 🔔 **Sistema de notificaciones** push

### **Media Prioridad**
- 🌐 **Integración con otros portales** (InfoCasas, Gallito)
- 📱 **PWA capabilities** (service workers, offline)
- 🎨 **Mejoras de UI/UX** en formularios
- 📈 **Análisis de tendencias** de mercado

### **Contribuciones Simples (Good First Issues)**
- 📝 **Corregir typos** en documentación
- 🎨 **Mejorar estilos CSS** de componentes
- 🧪 **Agregar tests** para funciones existentes
- 📚 **Traducir mensajes** a inglés/portugués
- 🔧 **Refactoring** de funciones pequeñas

---

## 💡 Consejos para Contribuidores

### **Para Nuevos Desarrolladores**
- 🌟 **Empieza por los "good first issues"**
- 📚 **Lee toda la documentación** antes de empezar
- ❓ **Pregunta si tienes dudas** - preferible a asumir
- 🧪 **Ejecuta tests frecuentemente** mientras desarrollas

### **Para Desarrolladores Experimentados**
- 🏗️ **Considera la arquitectura** antes de cambios grandes
- 🔄 **Propón refactoring** cuando veas oportunidades
- 📝 **Mejora documentación** mientras trabajas
- 👥 **Ayuda a revisar PRs** de otros contribuidores

### **Buenas Prácticas**
- ✅ **Commits atómicos**: Un concepto por commit
- ✅ **Branches descriptivos**: `feature/add-email-notifications`
- ✅ **PRs pequeños**: Más fáciles de revisar
- ✅ **Comunicación clara**: Explica el "por qué", no solo el "qué"

---

## 🆘 ¿Necesitas Ayuda?

### **Recursos**
- 📖 **[Documentación Técnica](DOCUMENTACION_TECNICA.md)**: Arquitectura detallada
- 🔧 **[README.md](README.md)**: Instalación y uso básico
- 🏠 **[Funcionalidades](core/Funcionalidades.md)**: Features del sistema

### **Contacto**
- 💬 **GitHub Discussions**: Para preguntas generales
- 🐛 **GitHub Issues**: Para bugs específicos
- 💼 **Email**: [maintainer@ejemplo.com] para temas urgentes

### **Community**
- 🌟 **Discord/Slack**: [Link al servidor] (si existe)
- 📱 **Twitter**: [@BuscadorInmo] para updates

---

## 🙏 Reconocimientos

Gracias a todos los contribuidores que han ayudado a hacer este proyecto mejor:

<!-- Esta sección se actualizará automáticamente con contributors -->

---

*¡Esperamos tu contribución! Cada mejora, por pequeña que sea, hace la diferencia.*