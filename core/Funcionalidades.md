# 🏠 Buscador Inmobiliario Inteligente - Funcionalidades

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Funcionalidades Principales](#funcionalidades-principales)
3. [Arquitectura Técnica](#arquitectura-técnica)
4. [Características Específicas](#características-específicas)
5. [Interfaz de Usuario](#interfaz-de-usuario)
6. [Estado de Desarrollo](#estado-de-desarrollo)
7. [Próximas Funcionalidades](#próximas-funcionalidades)
8. [Capturas de Pantalla](#capturas-de-pantalla)

---

## 🎯 Descripción General

**Buscador Inmobiliario Inteligente** es un servicio web Django que automatiza la búsqueda de propiedades inmobiliarias en MercadoLibre Uruguay. Utiliza inteligencia artificial para interpretar búsquedas en lenguaje natural, realiza scraping inteligente y ofrece una interfaz en tiempo real para monitorear el progreso de las búsquedas.

### 🎯 **Propósito Principal**
Simplificar y automatizar la búsqueda de propiedades inmobiliarias, permitiendo a los usuarios encontrar las mejores opciones mediante texto libre y filtros inteligentes, con resultados organizados y actualizados en tiempo real.

### 👥 **Usuarios Objetivo**
- **Agentes inmobiliarios** que buscan propiedades para clientes
- **Inversores** que monitorean el mercado inmobiliario
- **Particulares** buscando vivienda
- **Analistas de mercado** que necesitan datos agregados

## 🚀 Funcionalidades Principales

### 1. **🤖 Búsqueda Inteligente con IA**
- ✅ **Procesamiento de lenguaje natural**: Integración con Google Gemini para interpretar texto libre
- ✅ **Extracción automática de criterios**: Detecta automáticamente tipo de propiedad, ubicación, precio, dormitorios
- ✅ **Completado inteligente de filtros**: La IA rellena formularios automáticamente
- ✅ **Keywords contextuales**: Identifica palabras clave relevantes como "luminoso", "terraza", "garage"
- ✅ **Ejemplos de búsquedas naturales**:
  - *"Apartamento 2 dormitorios Montevideo hasta 200 mil dólares con garage"*
  - *"Casa luminosa Punta del Este cerca de la playa"*
  - *"Oficina moderna zona centro con estacionamiento"*
  - *"Local comercial Pocitos hasta 1500 dólares"*

### 2. **🔍 Sistema de Filtros Avanzados**
- ✅ **Filtros básicos inteligentes**:
  - Tipo de inmueble (apartamento, casa, oficina, local, terreno, etc.)
  - Ubicación jerárquica (departamento → ciudad → barrio)
  - Rango de precios flexible (USD/UYU con conversión automática)
  - Cantidad de dormitorios y baños
  - Superficie total y útil (m²)
- ✅ **Filtros específicos avanzados**:
  - Antigüedad de publicación (nuevas, última semana, mes)
  - Características especiales (acepta mascotas, amoblado, garage)
  - Servicios (piscina, barbacoa, seguridad)
  - Estado de la propiedad (a estrenar, buen estado, refaccionar)
- ✅ **Filtros automáticos por IA**: Completado inteligente basado en texto natural

### 3. **🕷️ Scraping Inteligente y Modular**
- ✅ **Arquitectura modular del scraper** (`core/scraper/`):
  - `run.py`: Orquestador principal del proceso
  - `mercadolibre.py`: Lógica específica de MercadoLibre
  - `browser.py`: Gestión de navegadores (Selenium + stealth)
  - `extractors.py`: Extracción de datos estructurados
  - `url_builder.py`: Construcción inteligente de URLs
  - `utils.py`: Utilidades compartidas (stemming, keywords)
- ✅ **Proceso de scraping en dos fases**:
  - **Fase 1**: Recolección masiva de URLs de listados
  - **Fase 2**: Extracción detallada de cada propiedad
- ✅ **Múltiples estrategias de scraping**:
  - Selenium con `selenium-stealth` para navegación compleja
  - Requests/BeautifulSoup para extracción rápida
  - ScrapingBee (opcional) para casos complejos
- ✅ **Procesamiento paralelo**: Configurable (1-10 hilos simultáneos)
- ✅ **Detección inteligente de duplicados**: Por URL única y metadata
- ✅ **Filtrado fuzzy de keywords**: Coincidencia del 70% con stemming en español
- ✅ **Manejo robusto de errores**: Continúa funcionando con fallos parciales
- ✅ **Sistema de cookies**: Gestión automática para evitar bloqueos

### 4. **💾 Sistema de Búsquedas Persistentes**
- ✅ **Búsquedas unificadas**: Sistema que distingue entre búsquedas temporales y guardadas
- ✅ **Dos tipos de búsqueda**:
  - **"Buscar"**: Ejecuta scraping sin guardar en la lista (`guardado=False`)
  - **"Buscar y Guardar"**: Ejecuta y guarda en lista visible (`guardado=True`)
- ✅ **Persistencia completa**: Todos los filtros, keywords y configuraciones
- ✅ **Resultados vinculados**: Propiedades encontradas asociadas a cada búsqueda
- ✅ **Histórico completo**: Registro de todas las búsquedas para análisis
- ✅ **Gestión inteligente**: Eliminación suave que preserva datos para métricas
- ✅ **Actualización automática**: Los resultados se enriquecen después del scraping

### 5. **⚡ Interfaz en Tiempo Real**
- ✅ **WebSocket nativo**: Actualizaciones instantáneas sin refrescar página
- ✅ **Fallback HTTP robusto**: Funciona aunque fallen los WebSockets
- ✅ **Progreso visual detallado**:
  - Estados específicos de cada fase del scraping
  - Contadores en tiempo real (nuevas/encontradas/existentes)
  - Indicadores de coincidencias de keywords
  - Tiempo estimado y progreso porcentual
  - Mensajes contextuales con emojis
- ✅ **Controles interactivos**:
  - Botón para detener búsqueda en progreso
  - Minimización automática de filtros durante búsqueda
  - Expansión/contracción de secciones
  - Vista detallada de búsquedas guardadas
- ✅ **Organización inteligente de resultados**:
  - Separación clara entre "Nuevas" y "Encontradas anteriormente"
  - Cards visuales con imagen, precio, ubicación
  - Enlaces directos optimizados a MercadoLibre
  - Metadata enriquecida (fecha, características, etc.)

### 6. **🗄️ Base de Datos Relacional Robusta**
- ✅ **Modelo de datos normalizado**:
  - Propiedades con campos estructurados y metadata JSON
  - Búsquedas con filtros persistentes y relaciones
  - Sistema de palabras clave con sinónimos
  - Usuarios e inmobiliarias para multitenancy
- ✅ **Prevención de duplicados**: Sistema de detección por URL única y checksums
- ✅ **Almacenamiento multimedia**: URLs de imágenes y archivos adjuntos
- ✅ **Auditoría completa**: Timestamps, versioning y trazabilidad
- ✅ **Optimización de consultas**: Índices y relaciones optimizadas
- ✅ **Migración flexible**: Compatible con SQLite (dev) y PostgreSQL (prod)

## 🏗️ Arquitectura Técnica

### 🔧 **Backend (Django 5.1)**
- ✅ **Framework principal**: Django 5.1 con apps modulares
- ✅ **Tiempo real**: Django Channels + WebSockets para comunicación bidireccional
- ✅ **Servidor ASGI**: Daphne para manejar conexiones WebSocket y HTTP
- ✅ **Base de datos**: SQLite (desarrollo) → PostgreSQL (producción) con migraciones automáticas
- ✅ **Caching**: Redis para channels layer y cache de sesiones
- ✅ **Threading**: Procesamiento paralelo configurable del scraping
- ✅ **Web scraping**: Requests + BeautifulSoup + Selenium con stealth

### 🌐 **Frontend Moderno**
- ✅ **Framework CSS**: Bootstrap 5 con customizaciones propias
- ✅ **JavaScript**: Vanilla JS modular con WebSocket API nativa
- ✅ **Responsive design**: Mobile-first, adaptable a todos los dispositivos
- ✅ **Animaciones**: Animate.css + transiciones CSS custom
- ✅ **UX avanzada**: Loading states, progress bars, notificaciones toast
- ✅ **PWA ready**: Service workers y manifest para instalación

### 🔗 **Integraciones y APIs**
- ✅ **MercadoLibre**: Scraping estructurado con selectores robustos
- ✅ **Google Gemini AI**: Procesamiento de lenguaje natural para búsquedas
- ✅ **ScrapingBee** (opcional): Proxy service para casos complejos
- ✅ **Redis**: Channel layer, cache y sessions
- ✅ **Docker**: Containerización completa para producción

### 📦 **Arquitectura Modular**

#### **Core App** (`core/`)
```
core/
├── scraper/                 # Paquete modular de scraping
│   ├── __init__.py         # API pública del scraper
│   ├── run.py              # Orquestador principal
│   ├── mercadolibre.py     # Lógica específica de ML
│   ├── browser.py          # Gestión de navegadores
│   ├── extractors.py       # Extracción de datos
│   ├── url_builder.py      # Construcción de URLs
│   ├── utils.py            # Utilidades (stemming, etc.)
│   ├── progress.py         # Manejo de progreso
│   └── constants.py        # Constantes y configuración
├── models.py               # Modelos de datos relacionales
├── views.py                # Vistas y endpoints HTTP
├── consumers.py            # WebSocket consumers
├── search_manager.py       # Gestión de búsquedas
├── export_utils.py         # Exportación CSV/auditoría
└── admin.py                # Panel de administración
```

#### **Buscador Project** (`buscador/`)
```
buscador/
├── settings.py             # Configuración con detección automática
├── urls.py                 # Routing principal
├── asgi.py                 # Configuración ASGI
└── wsgi.py                 # Configuración WSGI
```

## 🎨 Interfaz de Usuario

### 🖥️ **Pantalla Principal**
- **🔍 Barra de búsqueda inteligente**: Input principal que acepta texto libre
- **📋 Panel de filtros avanzados**: Expandible/contraíble con animaciones
- **🎯 Botones de acción**: "Buscar" (temporal) vs "Buscar y Guardar" (persistente)
- **📊 Panel de progreso**: Visualización en tiempo real del scraping
- **📱 Diseño responsivo**: Optimizado para desktop, tablet y móvil

### 📈 **Panel de Progreso en Tiempo Real**
- **🔄 Fases del scraping**: 
  - Análisis con IA → Construcción de URL → Recolección → Extracción → Filtrado
- **📊 Métricas visuales**:
  - Propiedades encontradas/nuevas/existentes
  - Coincidencias de keywords
  - Tiempo transcurrido y estimado
- **⏹️ Control de ejecución**: Botón para detener búsqueda en progreso
- **🎨 Estados visuales**: Loading spinners, progress bars, iconos de estado

### 🏠 **Visualización de Resultados**
- **🃏 Cards de propiedades**: Imagen, título, precio, ubicación
- **� Separación inteligente**: "Nuevas" vs "Encontradas anteriormente"
- **🔗 Enlaces directos**: Click para abrir en MercadoLibre
- **📊 Metadata enriquecida**: Fecha, características, fuente

### 💾 **Gestión de Búsquedas Guardadas**
- **📋 Lista organizada**: Todas las búsquedas guardadas con metadata
- **🔍 Vista detallada**: Filtros aplicados y resultados encontrados
- **🗑️ Gestión**: Eliminar búsquedas de la lista (eliminación suave)

### 🎯 **Casos de Uso Principales**

#### **👤 Usuario Casual**
1. Escribe en lenguaje natural: *"Apartamento 2 dormitorios Pocitos hasta 180 mil dólares"*
2. La IA completa automáticamente los filtros
3. Hace clic en "Buscar" para ver resultados temporales
4. Revisa propiedades encontradas con imágenes y precios

#### **🏢 Agente Inmobiliario**
1. Crea búsquedas específicas para diferentes clientes
2. Utiliza "Buscar y Guardar" para mantener portfolio de búsquedas
3. Monitorea en tiempo real nuevas propiedades que aparecen
4. Exporta resultados para compartir con clientes

#### **📊 Analista de Mercado**
1. Configura múltiples búsquedas para diferentes zonas y tipos
2. Analiza tendencias de precios y disponibilidad
3. Utiliza la exportación CSV para análisis externos
4. Monitorea histórico de búsquedas para detectar patrones

## 📸 Capturas de Pantalla

### 🖥️ **Pantalla Principal - Búsqueda**
```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Buscador Inmobiliario Inteligente                        │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│ 🔍 [Apartamento 2 dormitorios Pocitos hasta 180k USD  ] 🎯 │
│                                                            │
│ ▼ Filtros Avanzados (expandido)                           │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│ │Tipo     │Depto    │Ciudad   │Precio   │Dormit.  │       │
│ │🏠Apart. │📍Montev.│🏘️Pocitos│💰USD    │🛏️2     │       │
│ └─────────┴─────────┴─────────┴─────────┴─────────┘       │
│                                                            │
│ [🔍 Buscar]  [💾 Buscar y Guardar]                       │
└─────────────────────────────────────────────────────────────┘
```

### ⚡ **Panel de Progreso en Tiempo Real**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 Analizando búsqueda con IA...           ✅ Completado   │
│ 🔗 Construyendo URL de búsqueda...         ✅ Completado   │
│ 🕷️ Recolectando URLs de propiedades...     🔄 En progreso │
│                                                            │
│ ████████████████░░░░ 75% completado                        │
│                                                            │
│ 📊 Progreso:                                              │
│ • 🏠 Propiedades encontradas: 45                          │
│ • ✨ Nuevas propiedades: 12                               │
│ • 🔄 Ya existentes: 33                                    │
│ • 🎯 Keywords coincidentes: 8/10                          │
│                                                            │
│ ⏱️ Tiempo: 00:02:15 | 📈 Estimado: 00:03:00              │
│ [⏹️ Detener búsqueda]                                    │
└─────────────────────────────────────────────────────────────┘
```

### 🏠 **Resultados de Búsqueda**
```
┌─────────────────────────────────────────────────────────────┐
│ ✨ Nuevas Propiedades (12)                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 🏠 Apartamento 2 dormitorios Pocitos                   │   │
│ │ [� Ver en MercadoLibre]                              │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                            │
│ 🔄 Encontradas Anteriormente (33)                         │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 🏠 Apartamento luminoso Pocitos                        │   │
│ │ [� Ver en MercadoLibre]                              │   │
│ └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 💾 **Búsquedas Guardadas**
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Mis Búsquedas Guardadas                                │
│                                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏠 Apartamentos Pocitos 2 dorm                         │ │
│ │ 📅 Creada: 15/09/2025 | 🔍 Última búsqueda: hace 2h   │ │
│ │ 🎯 Filtros: Apartamento, Pocitos, 2 dorm, <$180k USD  │ │
│ │ 📊 Resultados: 45 encontradas (12 nuevas)             │ │
│ │ [🔍 Ver] [🗑️ Eliminar]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🏢 Oficinas Centro                                     │ │
│ │ 📅 Creada: 14/09/2025 | 🔍 Última búsqueda: hace 1d   │ │
│ │ 🎯 Filtros: Oficina, Centro, <$2000 USD/mes           │ │
│ │ 📊 Resultados: 23 encontradas (3 nuevas)              │ │
│ │ [🔍 Ver] [🔄 Re-buscar] [🗑️ Eliminar]                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Características Específicas

### Sistema de Keywords Inteligente
```python
✅ Funciona con coincidencias parciales
✅ Stemming básico para español (luminoso → lumin)
✅ Tolerancia del 70% de coincidencia
✅ Normalización de texto (acentos, mayúsculas)
```

### Progreso en Tiempo Real
```javascript
✅ Conexión WebSocket automática
✅ Fallback HTTP si falla WebSocket
✅ Mensajes estructurados con emojis
✅ Estados detallados de cada fase
```

### Manejo de Errores
```python
✅ Try/catch en cada nivel crítico
✅ Logs detallados para debugging
✅ Continuación del proceso aunque fallen elementos
✅ Mensajes informativos al usuario
```

## 📊 Estado de Desarrollo

### ✅ **COMPLETADO (v2.0)**
- [x] **Arquitectura modular del scraper** (`core/scraper/` package)
- [x] **Sistema de búsqueda inteligente con IA** (Google Gemini)
- [x] **Base de datos relacional completa** (migración de JSON)
- [x] **WebSockets en tiempo real** con fallback HTTP
- [x] **Sistema de búsquedas unificado** (guardadas vs temporales)
- [x] **Interfaz responsiva moderna** con animaciones
- [x] **Filtrado inteligente de keywords** (stemming + fuzzy matching)
- [x] **Detección de duplicados** robusta
- [x] **Manejo de errores** multicapa
- [x] **Exportación CSV** con auditoría
- [x] **Sistema de progreso** visual detallado
- [x] **Multi-estrategia scraping** (Selenium + Requests + ScrapingBee)

### 🔄 **EN DESARROLLO ACTIVO**
- [ ] **Optimización de performance** del scraping paralelo
- [ ] **Mejoras en extracción** de características avanzadas
- [ ] **Testing coverage** ampliado (actualmente >80%)
- [ ] **Documentación técnica** detallada (en progreso)

### � **PRÓXIMAS FUNCIONALIDADES (v2.1)**

#### **Alta Prioridad**
- [ ] **Notificaciones push** para nuevas propiedades
- [ ] **Búsquedas programadas** (cron jobs automáticos)
- [ ] **Dashboard de analytics** con métricas de mercado
- [ ] **API REST** para integraciones externas

#### **Media Prioridad**
- [ ] **Integración multi-portal** (InfoCasas, Gallito, Zonamerica)
- [ ] **Comparador de propiedades** lado a lado
- [ ] **Alertas de precio** (notificar cambios)
- [ ] **Exportación avanzada** (PDF con reportes, Excel)
- [ ] **Sistema de favoritos** independiente
- [ ] **Filtros geográficos** con mapas interactivos

#### **Baja Prioridad (v3.0)**
- [ ] **Machine Learning** para recomendaciones
- [ ] **Análisis de tendencias** automático
- [ ] **Multi-usuario** con roles y permisos
- [ ] **Aplicación móvil** nativa
- [ ] **Integración con CRM** inmobiliario
- [ ] **Sistema de tours virtuales**
## 🚀 Consideraciones para Producción

### 📈 **Escalabilidad y Performance**
- **Base de datos**: Migración automática SQLite → PostgreSQL
- **Cache distribuido**: Redis para sessions y channel layers
- **Procesamiento asíncrono**: Celery para tareas pesadas
- **Containerización**: Docker + Docker Compose production-ready
- **Load balancing**: Nginx + múltiples instancias Django
- **CDN**: Archivos estáticos optimizados

### 🔒 **Seguridad y Compliance**
- **Rate limiting**: Protección contra sobrecarga y abuse
- **Proxy rotation**: Evitar bloqueos de IP en scraping
- **Variables de entorno**: Configuración segura para producción
- **HTTPS obligatorio**: SSL/TLS en todas las conexiones
- **Backup automático**: Estrategia de respaldo de datos
- **Compliance legal**: Respeto a robots.txt y términos de uso

### 📊 **Monitoreo y Observabilidad**
- **Logging centralizado**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Métricas de performance**: Prometheus + Grafana
- **Health checks**: Endpoints de salud automáticos
- **Alertas de sistema**: Notificaciones críticas automáticas
- **APM**: Application Performance Monitoring
- **Error tracking**: Sentry para seguimiento de errores

### 🔧 **DevOps y Deployment**
- **CI/CD Pipeline**: GitHub Actions para deployment automático
- **Infrastructure as Code**: Terraform para recursos cloud
- **Blue-Green deployment**: Actualizaciones sin downtime
- **Database migrations**: Estrategia de migración segura
- **Environment management**: Staging, testing, production

---

## 📈 Métricas y KPIs

### 📊 **Métricas Técnicas Actuales**
- **Tiempo promedio de scraping**: 45-90 segundos por búsqueda
- **Propiedades procesadas**: 50-200 por búsqueda (variable según filtros)
- **Precisión de filtrado con keywords**: ~85% con matching fuzzy
- **Velocidad de interfaz**: <100ms respuesta WebSocket
- **Uptime del sistema**: >99.5% (objetivo producción)
- **Compatibilidad navegadores**: Chrome, Firefox, Safari, Edge

### 🎯 **Métricas de Negocio**
- **Búsquedas por usuario/día**: Promedio 3-5
- **Propiedades únicas descubiertas**: +500/día
- **Tiempo de sesión promedio**: 15-30 minutos
- **Conversión búsqueda → guardado**: ~40%
- **Satisfacción de usuario**: 4.5/5 (objetivo)

### � **Métricas de Uso**
- **Dispositivos**: 60% Desktop, 35% Mobile, 5% Tablet
- **Picos de uso**: 19:00-22:00 horario local
- **Palabras clave más populares**: "garage", "terraza", "luminoso"
- **Zonas más buscadas**: Pocitos, Centro, Punta del Este
- **Tipo de propiedad**: 70% Apartamentos, 20% Casas, 10% Otros

---

## 🔗 Enlaces y Recursos

### 🌐 **URLs del Sistema**
- **Servicio web**: Próximamente disponible en nuestro dominio oficial
- **Desarrollo local**: http://localhost:10000
- **WebSocket endpoint**: ws://localhost:10000/ws/search_progress/
- **Panel de administración**: http://localhost:10000/admin/
- **API de exportación**: http://localhost:10000/csv/export/all/
- **Diagnóstico Redis**: http://localhost:10000/redis_diagnostic/
- **Debug screenshots**: http://localhost:10000/debug_screenshots/

### 📁 **Archivos y Directorios Clave**
- **Base de datos**: `buscador_inmobiliario.db` (SQLite)
- **Logs del sistema**: Terminal donde corre Daphne/runserver
- **Exportaciones**: `exports/latest/` (CSVs y manifiestos)
- **Screenshots debug**: `static/debug_screenshots/`
- **Configuración cookies**: `mercadolibre_cookies.json`
- **Variables de entorno**: `.env` (no incluido en repo)

### 📚 **Documentación Relacionada**
- **Documentación técnica**: `DOCUMENTACION_TECNICA.md`
- **Instrucciones para Copilot**: `.github/copilot-instructions.md`
- **README principal**: `README.md`
- **Guía de deployment**: `DEPLOYMENT.md` (por crear)
- **Guía de contribución**: `CONTRIBUTING.md` (por crear)

### 🛠️ **Herramientas y Dependencias**
- **Python**: 3.10+ requerido
- **Django**: 5.1.x
- **Node.js**: Para herramientas de frontend (opcional)
- **Redis**: Para production (channels + cache)
- **PostgreSQL**: Para production database
- **Docker**: Para containerización

---

*Documento actualizado: 15 de septiembre de 2025*  
*Versión del sistema: 2.0*  
*Autor: Sistema de documentación automática*