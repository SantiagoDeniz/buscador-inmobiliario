
# Guía Técnica para Desarrolladores: Buscador Inmobiliario

## Propósito
Este documento está dirigido a desarrolladores que colaboren en el proyecto. Aquí encontrarás la estructura, convenciones, selectores clave y detalles técnicos para mantener, mejorar y depurar el código.

## Descripción General
El proyecto es una aplicación web en Django para búsqueda y gestión de propiedades inmobiliarias. Incluye scraping, almacenamiento, enriquecimiento de datos y una interfaz web. El foco está en la extensibilidad y la automatización de procesos.

## Estructura del Proyecto


### Estructura principal
- **buscador/**: Configuración Django (settings, urls, wsgi, asgi).
- **core/**: Lógica de negocio, scraping, modelos, vistas, administración, almacenamiento, tests.
   - `scraper.py`: Scraping y extracción de datos.
   - `search_manager.py`: Gestión de búsquedas y resultados.
   - `models.py`: Modelos de datos.
   - `views.py`: Vistas y endpoints.
   - `admin.py`: Panel de administración.
   - `storage.py`: Persistencia de resultados.
   - `scheduler.py`: Tareas programadas.
   - `urls.py`: Rutas core.
   - `tests.py` y `test_procesar_keywords.py`: Pruebas unitarias.
- **management/commands/**: Comandos custom para scraping y enriquecimiento.
- **migrations/**: Migraciones de base de datos.
- **templates/**: HTML para la UI.
- **static/**: Archivos estáticos.
- **user_data/**: Búsquedas y resultados en JSON.
- **requirements.txt**: Dependencias.
- **Dockerfile**: Contenedores Docker.
- **manage.py**: Script de gestión Django.

## Principales Funcionalidades

### Funcionalidades principales
### Nueva funcionalidad: Búsqueda inteligente con IA

Al realizar una búsqueda, el texto libre ingresado por el usuario se envía a un modelo de IA (Gemini 2.5 Flash, gratuito) que interpreta el texto y completa automáticamente los filtros del formulario. El resto del texto se transforma en palabras clave para la búsqueda. Esto permite búsquedas más naturales y rápidas.

Además, la interfaz minimiza los filtros con una animación mientras se realiza la búsqueda, restaurándolos al finalizar o detener la búsqueda.

## Instalación y Ejecución

### Instalación y ejecución
1. Clona el repo y crea un entorno virtual.
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Aplica migraciones:
   ```bash
   python manage.py migrate
   ```
4. Ejecuta el servidor:
   ```bash
   python manage.py runserver
   ```

### Configuración de la API de Gemini
Para usar la búsqueda inteligente, necesitas una clave de API gratuita de Gemini. Regístrate en https://aistudio.google.com/ y obtén tu clave. Luego, crea una variable de entorno:
```bash
set GEMINI_API_KEY=tu_clave_aqui
```
O agrégala en tu archivo `.env` si usas dotenv.

## Uso de Comandos Personalizados

### Comandos útiles
Ejecutar el scraper:
```bash
python manage.py run_scraper
```

## Tests

### Tests
Para ejecutar los tests:
```bash
python manage.py test core
```

## Docker

### Docker
Para construir y correr el contenedor:
```bash
docker build -t buscador-inmobiliario .
docker run -p 8000:8000 buscador-inmobiliario
```

## Contacto y Soporte

## Colaboración y Soporte
Para dudas técnicas, sugerencias o reportes, contacta al propietario o abre un issue/pull request.
Se recomienda documentar cualquier cambio relevante en esta guía.

## Links y Selectores Clave Usados en el Scraping

### Esta sección es clave para desarrolladores que deban modificar scraping, parseo o agregar nuevos portales.

### MercadoLibre
- **URL base de búsqueda:**
   - `https://listado.mercadolibre.com.uy/inmuebles/{tipo_inmueble}/{operacion}/{ubicacion}/`
   - Filtros de precio: `_PriceRange_{precio_min}USD-{precio_max}USD`
- **Selector de items en resultados:**
   - Selenium: `div.poly-card--grid-card`
   - BeautifulSoup: `li.ui-search-layout__item`
- **Selector de link/título:**
   - Selenium: `h3.poly-component__title-wrapper > a.poly-component__title`
   - BeautifulSoup: `a.ui-search-link`
- **Selector de descripción:**
   - Selenium: `p.ui-pdp-description__content[data-testid="content"]`
   - BeautifulSoup: `p.ui-pdp-description__content`
- **Selector de tabla de características:**
   - BeautifulSoup: `tr.andes-table__row` (clave-valor)
- **Selector de características destacadas:**
   - BeautifulSoup: `div.ui-vpp-highlighted-specs__key-value`
- **Selector de imagen principal:**
   - BeautifulSoup: `figure.ui-pdp-gallery__figure img`
- **Selector de precio:**
   - BeautifulSoup: `div.ui-pdp-price__main-container span.andes-money-amount__fraction`

### ScrapingBee
- **URL de proxy:**
   - `https://app.scrapingbee.com/api/v1/?api_key={API_KEY}&url={url_target}`

### Otros detalles
- **Función para filtrar links prohibidos:**
   - Paths bloqueados: `/jms/`, `/adn/api` (solo si el path después del dominio coincide)
- **Keywords:**
   - Se procesan y normalizan para filtrar resultados relevantes.

Esta sección sirve como referencia rápida para modificar o depurar el scraping y extracción de datos.
