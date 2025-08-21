from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync, sync_to_async
import os, json, threading
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
        "- condicion: Estreno, Usado, Pozo. "
        "- moneda: USD, UYU. "
        "- dormitorios_min, dormitorios_max, banos_min, banos_max, cocheras_min, cocheras_max, antiguedad_min, antiguedad_max, superficie_total_min, superficie_total_max, superficie_cubierta_min, superficie_cubierta_max: valores numéricos. "
        "- amoblado, terraza, aire_acondicionado, piscina, jardin, ascensor: true/false. "
        "IMPORTANTE: Si el valor original del usuario para ciudad/barrio es más específico que el filtro (por ejemplo, 'Pocitos Nuevo' en vez de 'Pocitos'), guarda el valor original como keyword además del filtro. "
        "Si el usuario indica barrio pero no ciudad, intuir y completar ciudad y departamento correspondiente. Si indica ciudad pero no departamento, intuir departamento correspondiente."
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
