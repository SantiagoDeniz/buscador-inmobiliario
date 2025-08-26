from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync, sync_to_async
import os, json, threading, time
import google.generativeai as genai
from dotenv import load_dotenv

from .search_manager import get_search, delete_search as delete_search_manager
from .storage import load_results

# Cargar variables de entorno desde .env
load_dotenv()

# Sistema de control de búsquedas activas
active_searches = {}
search_lock = threading.Lock()

# Configurar API key sólo si existe
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        print("[DEPURACIÓN] GEMINI_API_KEY configurada correctamente desde .env")
    except Exception as e:
        print(f"[DEPURACIÓN] No se pudo configurar Gemini: {e}")
else:
    print("[DEPURACIÓN] GEMINI_API_KEY no configurada. Se usará modo fallback.")

def home(request):
    # Vista home mínima para evitar el error de importación
    return render(request, 'core/home.html')

def search_detail(request, search_id):
    print(f"[DEPURACIÓN] Iniciando búsqueda para search_id={search_id}")
    search = get_search(search_id)
    print(f"[DEPURACIÓN] Datos de búsqueda: {search}")
    results = load_results(search_id)
    print(f"[DEPURACIÓN] Resultados cargados: {len(results) if results else 0}")
    advertencias = ["El texto de la búsqueda encuentra las palabras por separado en las publicaciones."]
    print(f"[DEPURACIÓN] Renderizando resultados...")
    return render(request, 'core/search_detail_partial.html', {'search': search, 'results': results, 'advertencias': advertencias})

@require_POST
def ia_sugerir_filtros(request):
    """Endpoint síncrono que llama a la función async de análisis vía async_to_sync."""
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
        texto = body.get('texto', '')
        filtros_manual = body.get('filtros', {}) or {}
        print(f"[DEPURACIÓN][IA SUGERIR] Texto recibido: {texto}")
        print(f"[DEPURACIÓN][IA SUGERIR] Filtros manuales: {filtros_manual}")
        ia_result = async_to_sync(analyze_query_with_ia)(texto)
        ia_filters = ia_result.get('filters', {})
        # Prioriza filtros provenientes del texto (IA)
        filtros_final = {**filtros_manual, **ia_filters}
        print(f"[DEPURACIÓN][IA SUGERIR] Filtros IA: {ia_filters}")
        print(f"[DEPURACIÓN][IA SUGERIR] Filtros fusionados: {filtros_final}")
        import datetime
        marca_tiempo = datetime.datetime.now().isoformat()
        return JsonResponse({
            'filters': filtros_final,
            'keywords': ia_result.get('keywords', []),
            'remaining_text': ia_result.get('remaining_text', ''),
            'original_text': texto,
            'datetime': marca_tiempo
        })
    except Exception as e:
        print(f"[DEPURACIÓN] Error en ia_sugerir_filtros: {e}")
        return JsonResponse({'error': str(e)}, status=500)

async def analyze_query_with_ia(query: str) -> dict:
    """Analiza texto libre y retorna dict con filters y remaining_text.
    Fallback: si no hay API key o error, devuelve estructura vacía.
    """
    if not query:
        return {"filters": {}, "remaining_text": ""}

    prompt = (
        "Eres un asistente para búsqueda inmobiliaria en Uruguay. Tu tarea es extraer filtros estructurados del texto y también identificar palabras clave relevantes para la búsqueda. "
        "Devuelve SOLO un JSON con las siguientes keys: "
        "- filters: solo los filtros soportados (ver lista abajo), NO inventes filtros nuevos. "
        "- keywords: palabras o frases relevantes para la búsqueda que no coincidan con los filtros. Si el usuario menciona condiciones, restricciones o detalles para los que NO hay filtro estructurado (por ejemplo, gastos comunes, distancia a la rambla, barrio específico, cercanía a lugares, etc.), agrega la frase completa como keyword. "
        "- remaining_text: el texto restante que no fue usado para filtros ni keywords. "
        "Campos soportados como filtros: "
        "- departamento: Montevideo, Canelones, Maldonado, Rocha, Colonia, San José, Florida, Lavalleja, Rivera, Tacuarembó, Salto, Paysandú, Artigas, Durazno, Treinta y Tres, Cerro Largo, Río Negro, Flores, Soriano. "
        "- ciudad: Aguada, Pocitos, Carrasco, Centro, Cordón, Malvín, Buceo, Parque Batlle, Punta Carretas, La Blanqueada, Tres Cruces, Sayago, Florida, Piriápolis, Punta Gorda, Ciudad Vieja, Barrio Sur, etc. (ciudades de cada departamento)"
        "- operacion: Venta, Alquiler, Alquiler temporal. "
        "- tipo: Apartamento, Casa, Terreno, Oficina, Local, Galpón, Garaje, Dúplex, PH, Penthouse, Monoambiente, Chacra. "
        "- condicion: Nuevo/Usado. "
        "- moneda: USD, UYU. "
        "- precio_min, precio_max, dormitorios_min, dormitorios_max, banos_min, banos_max, cocheras_min, cocheras_max, antiguedad_min, antiguedad_max, superficie_total_min, superficie_total_max, superficie_cubierta_min, superficie_cubierta_max: valores numéricos. "
        "- amoblado, terraza, aire_acondicionado, piscina, jardin, ascensor: true/false. "
        "IMPORTANTE: Si el valor original del usuario para ciudad/barrio es más específico que el filtro (por ejemplo, 'Pocitos Nuevo' en vez de 'Pocitos'), guarda el valor original como keyword además del filtro. "
        "Si el usuario indica barrio pero no ciudad, intuir y completar ciudad y departamento correspondiente. Si indica ciudad pero no departamento, intuir departamento correspondiente."
        "Si dice 'a estrenar' se refiere a antigüedad 0 años"
        "No inventes filtros nuevos, si el usuario menciona algo para lo que no hay filtro, agrégalo como keyword. "
        "Ejemplo: 'Apartamento de 2 dormitorios y 2 baños en Pocitos Nuevo, con terraza lavadero, garage para 2 autos, gastos comunes menores a 5.000 pesos y a menos de 3 cuadras de la rambla.' -> filters con tipo='apartamento', dormitorios_min/max=2, banos_min/max=2, ciudad='Pocitos', departamento='Montevideo', terraza=true, cocheras_min/max=2. keywords=['Pocitos Nuevo', 'terraza lavadero', 'garage para 2 autos', 'gastos comunes menores a 5.000 pesos', 'a menos de 3 cuadras de la rambla']. "
        f"\nTexto: {query}\nResponde SOLO JSON sin explicación adicional."
    )

    if not API_KEY:
        return {"filters": {}, "remaining_text": query}

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await sync_to_async(model.generate_content)(prompt)
        raw = response.text.strip() if hasattr(response, 'text') else str(response)
        # Limpiar bloques ```json ... ``` si existen
        if raw.startswith('```'):
            import re
            m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if m:
                raw = m.group(1)
        try:
            data = json.loads(raw)
        except Exception:
            print(f"[DEPURACIÓN] No se pudo parsear JSON de IA. Respuesta cruda: {raw[:200]}")
            return {"filters": {}, "remaining_text": query}

        # Normalizar booleans en filters
        for k, v in list(data.get('filters', {}).items()):
            if isinstance(v, str):
                if v.lower() == 'true':
                    data['filters'][k] = True
                elif v.lower() == 'false':
                    data['filters'][k] = False
        data.setdefault('filters', {})
        data.setdefault('remaining_text', '')
        return data
    except Exception as e:
        print(f"[DEPURACIÓN] Error IA: {e}")
        return {"filters": {}, "remaining_text": query}

def delete_search(request, search_id):
    """Eliminar una búsqueda guardada."""
    try:
        success = delete_search_manager(search_id)
        if success:
            return JsonResponse({'success': True, 'message': 'Búsqueda eliminada correctamente'})
        else:
            return JsonResponse({'success': False, 'message': 'Búsqueda no encontrada'}, status=404)
    except Exception as e:
        print(f"[DEPURACIÓN] Error eliminando búsqueda {search_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def search_detail_ajax(request, search_id):
    """Vista AJAX para cargar detalles de búsqueda."""
    try:
        search = get_search(search_id)
        if not search:
            return JsonResponse({'error': 'Búsqueda no encontrada'}, status=404)
        
        results = load_results(search_id)
        advertencias = ["El texto de la búsqueda encuentra las palabras por separado en las publicaciones."]
        html = render_to_string('core/search_detail_partial.html', {
            'search': search, 
            'results': results, 
            'advertencias': advertencias
        })
        return JsonResponse({'html': html})
    except Exception as e:
        print(f"[DEPURACIÓN] Error en search_detail_ajax {search_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def detener_busqueda_view(request):
    """Detener búsqueda en progreso."""
    if request.method == 'POST':
        try:
            with search_lock:
                # Marcar todas las búsquedas activas para detenerse
                for search_id in list(active_searches.keys()):
                    active_searches[search_id]['stop_requested'] = True
                    print(f"[DEPURACIÓN] Solicitada parada para búsqueda {search_id}")
                
                print(f"[DEPURACIÓN] Búsquedas marcadas para detener: {len(active_searches)}")
            
            return JsonResponse({'success': True, 'message': 'Señal de parada enviada a búsquedas activas'})
        except Exception as e:
            print(f"[DEPURACIÓN] Error deteniendo búsqueda: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

def is_search_stopped(search_id):
    """Verificar si una búsqueda debe detenerse."""
    with search_lock:
        return active_searches.get(search_id, {}).get('stop_requested', False)

def register_active_search(search_id):
    """Registrar una búsqueda como activa."""
    with search_lock:
        active_searches[search_id] = {'stop_requested': False}
        print(f"[DEPURACIÓN] Búsqueda {search_id} registrada como activa")

def unregister_active_search(search_id):
    """Desregistrar una búsqueda activa."""
    with search_lock:
        if search_id in active_searches:
            del active_searches[search_id]
            print(f"[DEPURACIÓN] Búsqueda {search_id} desregistrada")

@csrf_exempt
@require_POST
def http_search_fallback(request):
    """Fallback HTTP para búsquedas cuando WebSockets no funcionan"""
    try:
        data = json.loads(request.body)
        texto = data.get('texto', '')
        filtros_manual = data.get('filtros', {})
        
        print(f"[HTTP FALLBACK] Iniciando búsqueda HTTP: {texto}")
        
        # USAR IA como en el WebSocket consumer
        print('🤖 [HTTP FALLBACK] Procesando texto con IA...')
        try:
            ia_result = async_to_sync(analyze_query_with_ia)(texto)
            print(f'🤖 [HTTP FALLBACK] Resultado IA: {ia_result}')
            
            # Fusionar filtros como en el consumer
            filtros_ia = ia_result.get('filters', {})
            filtros_final = filtros_manual.copy()
            for k, v in filtros_ia.items():
                filtros_final[k] = v  # Prioriza IA
            
            keywords = ia_result.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [keywords] if keywords else []
                
            print(f'🎚️ [HTTP FALLBACK] Filtros fusionados: {filtros_final}')
            print(f'🔍 [HTTP FALLBACK] Keywords de IA: {keywords}')
            
        except Exception as e:
            print(f'🤖 [HTTP FALLBACK] Error procesando con IA: {e}')
            # Fallback al procesamiento básico
            from .search_manager import procesar_keywords
            keywords = procesar_keywords(texto) if texto else []
            filtros_final = filtros_manual
        
        # Ejecutar scraper con los filtros y keywords procesados
        from .scraper import run_scraper
        run_scraper(filtros_final, keywords, max_paginas=2, workers_fase1=1, workers_fase2=1)
        
        # Obtener resultados de la base de datos
        from .models import Propiedad
        propiedades = Propiedad.objects.order_by('-id')[:20]  # Últimas 20
        
        resultados = []
        for prop in propiedades:
            if texto:  # Si hay texto de búsqueda, filtrar por keywords
                import unicodedata
                def normalizar(texto):
                    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
                
                texto_propiedad = f"{prop.titulo} {prop.descripcion} {prop.caracteristicas_texto}".lower()
                texto_norm = normalizar(texto_propiedad)
                keywords_norm = [normalizar(kw) for kw in keywords]
                
                if all(kw in texto_norm for kw in keywords_norm):
                    resultados.append({
                        'title': prop.titulo,
                        'url': prop.url_publicacion
                    })
            else:
                resultados.append({
                    'title': prop.titulo,
                    'url': prop.url_publicacion
                })
        
        return JsonResponse({
            'success': True,
            'matched_publications': resultados[:10],  # Limitar a 10 para no sobrecargar
            'total': len(resultados)
        })
        
    except Exception as e:
        print(f"[HTTP FALLBACK] Error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'matched_publications': []
        })

def redis_diagnostic(request):
    """Vista de diagnóstico para verificar Redis y WebSockets"""
    try:
        from channels.layers import get_channel_layer
        import os
        
        channel_layer = get_channel_layer()
        redis_url = os.environ.get('REDIS_URL', 'No configurada')
        
        diagnostics = {
            'redis_url': redis_url[:50] + '...' if len(redis_url) > 50 else redis_url,
            'channel_layer': str(type(channel_layer)) if channel_layer else None,
            'channel_layer_available': channel_layer is not None,
        }
        
        # Intentar una operación simple con channel_layer
        if channel_layer:
            try:
                from asgiref.sync import async_to_sync
                async_to_sync(channel_layer.group_send)("test_group", {
                    "type": "test_message",
                    "message": "test"
                })
                diagnostics['channel_layer_test'] = 'SUCCESS'
            except Exception as e:
                diagnostics['channel_layer_test'] = f'ERROR: {str(e)}'
        
        return JsonResponse(diagnostics)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'redis_url': os.environ.get('REDIS_URL', 'No configurada')[:50] + '...'
        })

def debug_screenshots(request):
    """Vista para mostrar capturas de debug cuando no hay WebSockets disponibles"""
    try:
        debug_file = os.path.join('static', 'debug_screenshots', 'latest_screenshots.json')
        screenshots = []
        
        if os.path.exists(debug_file):
            try:
                with open(debug_file, 'r', encoding='utf-8') as f:
                    screenshots = json.load(f)
            except:
                screenshots = []
        
        # Ordenar por timestamp más reciente primero
        screenshots.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        context = {
            'screenshots': screenshots,
            'has_screenshots': len(screenshots) > 0
        }
        
        return render(request, 'core/debug_screenshots.html', context)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})
