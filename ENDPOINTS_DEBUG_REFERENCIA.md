# 🔧 Referencias Rápidas - Endpoints de Debug y Progreso

## 📋 Tabla Resumen de Endpoints

| Endpoint | Método | Propósito | Autenticación |
|----------|--------|-----------|---------------|
| `/redis_diagnostic/` | GET | Diagnosticar Redis/WebSockets | No |
| `/debug_screenshots/` | GET | Visualizar capturas debug | No |
| `/detener_busqueda/` | POST | Detener búsquedas activas | No |
| `/http_search_fallback/` | POST | Búsqueda sin WebSockets | No |
| `/ws/search_progress/` | WebSocket | Progreso en tiempo real | No |

## 🚀 Comandos de Testing Rápido

### Diagnóstico Redis
```bash
curl -X GET http://localhost:10000/redis_diagnostic/
```

### Detener búsquedas activas
```bash
curl -X POST http://localhost:10000/detener_busqueda/ \
  -H "Content-Type: application/json"
```

### Búsqueda con fallback HTTP
```bash
curl -X POST http://localhost:10000/http_search_fallback/ \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "apartamento 2 dormitorios Pocitos",
    "filtros": {"tipo": "apartamento", "operacion": "alquiler"},
    "guardar": false,
    "plataforma": "mercadolibre"
  }'
```

### Ver capturas debug
```bash
# En navegador
http://localhost:10000/debug_screenshots/
```

## 📁 Archivos de Debug Generados

### Capturas de Screenshots
```
static/debug_screenshots/
├── latest_screenshots.json          # Índice de capturas recientes
├── login_check_20240922_143052.png  # Captura de pantalla
├── login_check_20240922_143052.html # HTML completo
└── login_check_20240922_143052_info.txt # Metadata
```

### Estructura latest_screenshots.json
```json
[
  {
    "path": "/static/debug_screenshots/login_check_20240922_143052.png",
    "timestamp": "2024-09-22T14:30:52.123456",
    "message": "Verificando necesidad de login en MercadoLibre"
  }
]
```

## 🔌 WebSocket Testing

### Conexión desde JavaScript
```javascript
// Conectar al WebSocket
const socket = new WebSocket('ws://localhost:10000/ws/search_progress/');

// Escuchar progreso
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Progreso:', data);
};

// Enviar búsqueda
socket.send(JSON.stringify({
    'text': 'apartamento 2 dormitorios',
    'filters': {'tipo': 'apartamento'}
}));
```

### Testing con wscat (si está instalado)
```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c ws://localhost:10000/ws/search_progress/

# Enviar mensaje
> {"text": "apartamento", "filters": {}}
```

## 🐛 Solución de Problemas Comunes

### Redis no disponible
- **Síntoma**: `channel_layer_available: false` en `/redis_diagnostic/`
- **Solución**: Verificar `REDIS_URL` o usar fallback HTTP con `/http_search_fallback/`

### WebSocket no conecta
- **Síntoma**: Error de conexión WebSocket
- **Solución**: Usar endpoint `/http_search_fallback/` como alternativa

### Capturas no aparecen
- **Síntoma**: `/debug_screenshots/` muestra vacío
- **Solución**: Verificar permisos de escritura en `static/debug_screenshots/`

### Búsqueda no se detiene
- **Síntoma**: Proceso continúa después de `/detener_busqueda/`
- **Diagnóstico**: Verificar logs por mensajes `[DEPURACIÓN] Solicitada parada`

## 💡 Tips de Desarrollo

### Habilitar capturas debug en scraper
```python
from core.scraper import tomar_captura_debug

# Durante desarrollo del scraper
def mi_funcion_scraper(driver):
    # ... lógica ...
    tomar_captura_debug(driver, "mi_debug_personalizado")
```

### Enviar progreso personalizado
```python
from core.scraper import send_progress_update

send_progress_update(
    current_search_item="Procesando datos específicos...",
    matched_publications=5,
    debug_screenshot="/path/to/screenshot.png"
)
```

### Verificar estado de búsquedas activas
```python
# En views.py o shell de Django
from core.views import active_searches
print(f"Búsquedas activas: {len(active_searches)}")
for search_id, state in active_searches.items():
    print(f"ID: {search_id}, Stop requested: {state.get('stop_requested', False)}")
```

## 🔄 Integración con Frontend

### Detección automática de capacidades
```javascript
// Probar WebSocket primero
function initializeSearchMethod() {
    try {
        const testSocket = new WebSocket('ws://localhost:10000/ws/search_progress/');
        testSocket.onopen = () => {
            console.log('WebSocket disponible');
            useWebSocketSearch();
            testSocket.close();
        };
        testSocket.onerror = () => {
            console.log('WebSocket no disponible, usando HTTP fallback');
            useHttpFallbackSearch();
        };
    } catch (e) {
        useHttpFallbackSearch();
    }
}
```

### Mostrar progreso en UI
```javascript
function updateProgressBar(data) {
    if (data.total_found) {
        document.getElementById('total-count').textContent = data.total_found;
    }
    if (data.current_search_item) {
        document.getElementById('status').textContent = data.current_search_item;
    }
    if (data.debug_screenshot) {
        showDebugScreenshot(data.debug_screenshot);
    }
}
```

## 📊 Monitoreo en Producción

### Logs importantes
```bash
# Filtrar logs de progreso
tail -f logs/django.log | grep -E "\[PROGRESO\]|\[FINAL\]|\[WebSocket\]"

# Filtrar logs de debug
tail -f logs/django.log | grep -E "\[DEBUG\]|\[DEPURACIÓN\]"
```

### Health checks
```bash
# Verificar servicios esenciales
curl -s http://localhost:10000/redis_diagnostic/ | jq '.channel_layer_available'

# Verificar capturas recientes
ls -la static/debug_screenshots/ | head -10
```