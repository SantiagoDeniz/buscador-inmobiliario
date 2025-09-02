# Guía rápida para agentes de IA en este repo

Objetivo: ayudarte a ser productivo de inmediato en este proyecto Django (scraping + persistencia + UI) documentando arquitectura real, flujos y convenciones específicas.

## Lenguaje y estilo
- Responde siempre en español y mantén los nombres/terminología del código tal como están (ej.: Busqueda, PalabraClave).
- Prefiere cambios mínimos y seguros; si tocas scraping, actualiza ambos caminos: Selenium y requests/BS4 en `core/scraper.py`.

## Arquitectura en 1 minuto
- Django app `core` (lógica, modelos, vistas, scraper) + proyecto `buscador` (settings/urls/asgi).
- Scraping de MercadoLibre:
  - Selenium headless con `selenium-stealth` opcional para navegación/filtrado fino.
  - Requests/BS4 (o ScrapingBee opcional) para recolección rápida y parsing de detalle.
  - Progreso y capturas debug vía utilidades en `core/scraper/*` y vistas de soporte (`/debug_screenshots/`).
- Persistencia: modelos relacionales en `core/models.py`. CRUD y lógica de keywords/compatibilidad en `core/search_manager*.py` (las vistas importan `core.search_manager`).
- Realtime/fallback: Channels + Redis si `REDIS_URL` está definido; si no, `InMemoryChannelLayer`. Fallback HTTP en `views.http_search_fallback`.
- Exportación CSV/auditoría: endpoints en `core/urls.py` escriben a `exports/latest/` con manifiesto.

## Flujos clave de desarrollo
- Servidor dev: `python manage.py runserver` (tarea VS Code disponible: “Run Django server for test” en `0.0.0.0:10000`).
- Migraciones: `python manage.py makemigrations core` y `python manage.py migrate`.
- Tests principales: `python manage.py test core.tests_database` (incluye modelos y gestor de búsquedas). 
- Smoke del scraper: script `scripts/smoke_run_scraper.py` (configura `DJANGO_SETTINGS_MODULE` y ejecuta `run_scraper`).
- Docker compose (PostgreSQL/Redis/app): ver `docker-compose.yml` y `scripts/setup_postgresql.py` para automatizar.

## Scraping MercadoLibre: patrones y decisiones
- Construcción de URL y paginación: usa `_Desde_<n>` y `_NoIndex_True`; no dupliques `_NoIndex_True` si ya está en base. Ejemplo en `core/scraper.py`.
- Selectores de lista: Selenium usa `div.poly-card--grid-card`; requests/BS4 busca `li.ui-search-layout__item` y `a.poly-component__title|ui-search-link`.
- Detalle: precio título/moneda/valor, imagen, descripción y características con `tr.andes-table__row` y `div.ui-vpp-highlighted-specs__key-value`.
- Respeta robots y paths bloqueados: filtra `'/jms/'` y `'/adn/api'` (ver `url_prohibida`). Permite paths de publicaciones `/MLU-...`.
- Cookies: carga desde `MERCADOLIBRE_COOKIES` (JSON) o archivo `mercadolibre_cookies.json`. Si no son válidas, continúa con limitaciones y genera captura debug.
- ScrapingBee opcional: activa cuando `USE_THREADS=True` y `SCRAPINGBEE_API_KEY` esté presente.

## Datos y persistencia
- Modelos clave: `Busqueda` (UUID, `filtros` JSON), `PalabraClave` (sinónimos como string JSON por compatibilidad), `Propiedad`, `ResultadoBusqueda` y auxiliares.
- Gestor de búsquedas: `core/search_manager_db.py` implementa:
  - `procesar_keywords(texto)` → normaliza y agrega sinónimos; usa en scraper y vistas.
  - `save_search/create_search/update_search` → compatibilidad con flujos previos y vistas/consumers.
  - `save_results/load_results` → puente entre scraping y BD.
- Índices y ordenado ya definidos en Meta; evita consultas N+1 usando `select_related/prefetch_related` como en la doc técnica.

## Channels/Redis y fallback
- `settings.py` autodetecta `REDIS_URL` y convierte `redis://` a `rediss://` para Upstash. Sin Redis: fallback a `InMemoryChannelLayer`.
- Web: consumer/vistas usan `send_progress_update` y endpoints HTTP alternativos (`/http_search_fallback/`).

## IA (Gemini)
- `views.analyze_query_with_ia` usa `google-generativeai` (modelo `gemini-1.5-flash`) para derivar `filters`, `keywords` y `remaining_text`.
- Requiere `GEMINI_API_KEY`; sin clave → retorna estructura vacía y sigue flujo base.
- Al fusionar filtros, se prioriza lo inferido por IA sobre filtros manuales del cliente.

## Exportación CSV y auditoría
- Endpoints:
  - `GET /csv/export/all/` (regenera CSVs + manifiesto y poda snapshots).
  - `GET /csv/table/<tabla>/` (CSV on-the-fly).
  - `GET /csv/audit/latest/` (manifiesto más reciente).
- Salida en `exports/latest/` con `_manifest.json` y checksums/duplicados.

## Conexión/entornos
- Dev por defecto: SQLite `buscador_inmobiliario.db`.
- Producción: setear `DATABASE_ENGINE=postgresql` y variables `DB_*` (ver `README_POSTGRESQL.md`).
- Redis opcional vía `REDIS_URL` (Upstash: usa rediss://). Estáticos en `static/` y `staticfiles/`.

## Convenciones y trampas comunes
- Al añadir o cambiar filtros: sincroniza URL builder (en `core/scraper/url_builder.py`) y validación en vistas/IA.
- Si cambias selectores de ML, actualiza ambas rutas (Selenium y requests/BS4) y los logs de depuración.
- `PalabraClave.sinonimos` es TEXT con JSON serializado: usa `set_sinonimos()` y la propiedad `sinonimos_list`.
- Usa `send_progress_update` al reportar progreso en scraping y genera capturas con `tomar_captura_debug` para diagnósticos.

## Ejemplos rápidos
- Filtros típicos para `run_scraper`: `{ tipo:'apartamento', operacion:'alquiler', departamento:'Montevideo', ciudad:'Pocitos', moneda:'USD', precio_min:500, precio_max:1000 }`.
- Probar Redis/Channels: `GET /redis_diagnostic/`.
- Ver capturas debug: `GET /debug_screenshots/` (lee `static/debug_screenshots/latest_screenshots.json`).

¿Algo poco claro o faltante? Indica qué flujo necesitas mejorar (scraper, DB, IA, export, websockets) y lo iteramos.
