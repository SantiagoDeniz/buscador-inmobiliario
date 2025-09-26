# Guía rápida para agentes de IA en este repo

Objetivo: ayudarte a ser productivo de inmediato en este proyecto Django (scraping + persistencia + UI) documentando arquitectura real, flujos y convenciones específicas.

## Lenguaje y estilo
- Responde siempre en español y mantén los nombres/terminología del código tal como están (ej.: Busqueda, PalabraClave).
- Prefiere cambios mínimos y seguros; si tocas scraping, actualiza ambos caminos: Selenium y requests/BS4 en `core/scraper/` (paquete modular). 
- **IMPORTANTE**: No uses `core/scraper.py` (archivo monolítico eliminado), usa el paquete modular `core/scraper/`.

## Ejecución de comandos (PowerShell)
- Evita abrir REPLs interactivos por error (no uses `>>>`). Ejecuta comandos completos en una sola invocación.
- En PowerShell no uses heredocs de bash (<< 'EOF'); usa: `python -m unittest ...` o `python manage.py ...`.
- Para múltiples comandos en una línea, separa con `;`.
- **Siempre que haya una tarea disponible en VS Code, prefierela**.

## Servidor de Desarrollo (IMPORTANTE)
- **USAR DAPHNE, NO RUNSERVER**: `.\\.venv\\Scripts\\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application`
- **Puerto 10000**, NO 8000: http://localhost:10000
- **Razón**: Soporte WebSockets para sistema de progreso y Django Channels
- **Configurado en**: DEV_CONFIG.md para referencia

## Configuración de Límites (DESARROLLO vs PRODUCCIÓN)
- **DESARROLLO**: Usar plan "testing" por defecto (límites ilimitados)
- **PRODUCCIÓN**: Cambiar a planes reales (básico/premium/enterprise) cuando se solicite
- **Usuario testing**: `testing@example.com` creado automáticamente con plan testing
- **Variable entorno**: `BUSCADOR_TESTING_MODE=true` como alternativa

## Arquitectura del Scraper Modular

### Paquete `core/scraper/` (NO usar `core/scraper.py`)
```
core/scraper/
├── __init__.py              # API pública del scraper
├── run.py                   # Orquestador principal 
├── mercadolibre.py          # Lógica específica de MercadoLibre
├── browser.py               # Gestión de navegadores (Selenium + stealth)
├── extractors.py            # Extracción y parsing de datos
├── url_builder.py           # Construcción inteligente de URLs
├── utils.py                 # Utilidades (stemming, keywords, validación)
├── progress.py              # Sistema de progreso y notificaciones
└── constants.py             # Constantes y configuración
```

### API Pública del Scraper
Importa desde `core.scraper` (fachada con imports perezosos):
- **Funciones principales**: `run_scraper`, `scrape_mercadolibre`, `extraer_total_resultados_mercadolibre`
- **URL Building**: `build_mercadolibre_url`, `normalizar_para_url`, `parse_rango`
- **Extracción**: `scrape_detalle_con_requests`, `recolectar_urls_de_pagina`
- **Navegador**: `iniciar_driver`, `manejar_popups_cookies`, `verificar_necesita_login`, `cargar_cookies`
- **Progreso/Debug**: `send_progress_update`, `tomar_captura_debug`
- **Utilidades**: `stemming_basico`, `extraer_variantes_keywords`

### Estrategias de Scraping
- **Selenium headless** con `selenium-stealth` opcional para navegación/filtrado fino
- **Requests/BS4** (o ScrapingBee opcional) para recolección rápida y parsing de detalle
- **Progreso y capturas** debug vía utilidades en `core/scraper/*` y vistas de soporte (`/debug_screenshots/`)

## Datos y Persistencia

### Modelos Principales
- **`Busqueda`**: UUID, `filtros` JSON, `guardado` Boolean (visibilidad en UI)
- **`PalabraClave`**: sinónimos como string JSON por compatibilidad SQLite
- **`Propiedad`**: datos normalizados con metadata JSON
- **`ResultadoBusqueda`**: relación búsqueda-propiedad con scoring
- **Auxiliares**: `Usuario`, `Inmobiliaria`, `Plataforma`

### Sistema de Guardado Unificado
- **TODAS las búsquedas** se almacenan en BD
- **`guardado=True`**: búsquedas visibles en lista ("Buscar y Guardar")
- **`guardado=False`**: historial interno ("Buscar")
- **Diferencia botones**: "Buscar" (temporal) vs "Buscar y Guardar" (persistente)

### Gestor de Búsquedas (`core/search_manager.py`)
- `get_all_searches()` → solo búsquedas con `guardado=True` (interfaz)
- `get_all_search_history()` → todas las búsquedas (análisis)
- `delete_search()` → elimina búsqueda de la lista del usuario (suave, preserva datos)
- `restore_search_from_history()` → función administrativa para recuperar eliminadas
- `procesar_keywords(texto)` → normaliza y agrega sinónimos; usa en scraper y vistas
- `save_search/create_search/update_search` → compatibilidad con flujos previos
- `save_results/load_results` → puente entre scraping y BD

### Performance y Consultas
- Índices ya definidos en Meta
- Evita consultas N+1 usando `select_related/prefetch_related`
- Bulk operations para inserción masiva de resultados

## Scraping MercadoLibre: Patrones y Decisiones

### Construcción de URLs
- Usa `_Desde_<n>` y `_NoIndex_True` para paginación
- No dupliques `_NoIndex_True` si ya está en URL base
- Implementado en `core/scraper/url_builder.py`

### Selectores por Estrategia
- **Selenium**: `div.poly-card--grid-card` para listados
- **Requests/BS4**: `li.ui-search-layout__item` y `a.poly-component__title|ui-search-link` para listados
- **Detalle**: precio título/moneda/valor, imagen, descripción y características
- **Características**: `tr.andes-table__row` y `div.ui-vpp-highlighted-specs__key-value`

### Buenas Prácticas
- Respeta robots.txt y filtra paths bloqueados: `'/jms/'` y `'/adn/api'` (ver `url_prohibida`)
- Permite paths de publicaciones `/MLU-...`
- **Cookies**: carga desde `MERCADOLIBRE_COOKIES` (JSON) o archivo `mercadolibre_cookies.json`
- Si cookies no son válidas: continúa con limitaciones y genera captura debug
- **ScrapingBee opcional**: activa cuando `USE_THREADS=True` y `SCRAPINGBEE_API_KEY` presente

## Flujos Clave de Desarrollo

### Comandos de Desarrollo
- **Servidor dev**: `python manage.py runserver` (tarea VS Code: "Run Django server for test" en `0.0.0.0:10000`)
- **Migraciones**: `python manage.py makemigrations core` y `python manage.py migrate`
- **Tests principales**: `python manage.py test core.tests_database` (incluye modelos y gestor de búsquedas)
- **Tests puntuales**: `python manage.py test core.tests.FiltrosBusquedaTest.test_formulario_filtros -v 2`

### Testing y Debugging  
- **Smoke del scraper**: script `scripts/smoke_run_scraper.py` (configura `DJANGO_SETTINGS_MODULE`)
- **Docker compose**: PostgreSQL/Redis/app en `docker-compose.yml` + `scripts/setup_postgresql.py`
- **Probar Redis/Channels**: `GET /redis_diagnostic/`
- **Ver capturas debug**: `GET /debug_screenshots/` (lee `static/debug_screenshots/latest_screenshots.json`)

## Channels/Redis y Fallback

### Configuración Automática
- `settings.py` autodetecta `REDIS_URL` y convierte `redis://` a `rediss://` para Upstash
- Sin Redis: fallback a `InMemoryChannelLayer`
- Consumer/vistas usan `send_progress_update` y endpoints HTTP alternativos (`/http_search_fallback/`)

## IA (Gemini) y Análisis

### Integración de IA
- `views.analyze_query_with_ia` usa `google-generativeai` (modelo `gemini-1.5-flash`)
- Deriva `filters`, `keywords` y `remaining_text` de texto libre
- Requiere `GEMINI_API_KEY`; sin clave → retorna estructura vacía y sigue flujo base
- **Fusión de filtros**: se prioriza lo inferido por IA sobre filtros manuales del cliente

## Exportación CSV y Auditoría

### Endpoints de Exportación
- `GET /csv/export/all/` → regenera CSVs + manifiesto y poda snapshots
- `GET /csv/table/<tabla>/` → CSV on-the-fly  
- `GET /csv/audit/latest/` → manifiesto más reciente
- **Salida**: `exports/latest/` con `_manifest.json` y checksums/duplicados

## Configuración de Entornos

### Desarrollo vs Producción
- **Dev por defecto**: SQLite `buscador_inmobiliario.db`
- **Producción**: setear `DATABASE_ENGINE=postgresql` y variables `DB_*` (ver `README_POSTGRESQL.md`)
- **Redis opcional**: vía `REDIS_URL` (Upstash: usa `rediss://`)
- **Estáticos**: `static/` y `staticfiles/`

## Convenciones y Trampas Comunes

### Mantenimiento de Consistencia
- **Al añadir/cambiar filtros**: sincroniza URL builder (`core/scraper/url_builder.py`) y validación en vistas/IA
- **Si cambias selectores ML**: actualiza ambas rutas (Selenium y requests/BS4) y logs de depuración
- **`PalabraClave.sinonimos`**: es TEXT con JSON serializado, usa `set_sinonimos()` y propiedad `sinonimos_list`

### Debugging y Progreso
- Usa `send_progress_update` al reportar progreso en scraping
- Genera capturas con `tomar_captura_debug` para diagnósticos
- Logs detallados en cada nivel crítico

## Ejemplos Rápidos

### Filtros Típicos
```python
filtros = {
    'tipo': 'apartamento', 
    'operacion': 'alquiler',
    'departamento': 'Montevideo', 
    'ciudad': 'Pocitos',
    'moneda': 'USD', 
    'precio_min': 500, 
    'precio_max': 1000
}
```

### Diferencia de Botones
- **"Buscar"**: `guardado=False`, no aparece en lista, solo para análisis
- **"Buscar y Guardar"**: `guardado=True`, visible en interfaz del usuario
- **Ambos** se almacenan en BD para trazabilidad completa

## Preguntas y Mejoras

Si tienes dudas sobre algo, **antes de implementarlo haz las preguntas necesarias**. 

¿Algo poco claro o faltante? Indica qué flujo necesitas mejorar:
- **Scraper**: arquitectura modular, estrategias, selectores
- **BD**: modelos, relaciones, consultas optimizadas  
- **IA**: integración Gemini, procesamiento de texto
- **Export**: CSV, auditoría, manifiestos
- **WebSockets**: tiempo real, fallbacks, progreso

Y lo iteramos juntos para mantener la documentación actualizada.