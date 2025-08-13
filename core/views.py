from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def detener_busqueda_view(request):
    if request.method == 'POST':
        # Aquí deberías agregar la lógica real para detener la búsqueda (por ejemplo, señal a un thread)
        return JsonResponse({'status': 'ok', 'message': 'La búsqueda ha sido detenida.'})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
from django.template.loader import render_to_string
from django.http import JsonResponse
def search_detail_ajax(request, search_id):
    search = get_search(search_id)
    results = load_results(search_id)
    advertencias = ["El texto de la búsqueda encuentra las palabras por separado en las publicaciones."]
    html = render_to_string('core/search_detail_partial.html', {'search': search, 'results': results, 'advertencias': advertencias})
    return JsonResponse({'html': html})



from django.shortcuts import render, redirect
from .search_manager import get_all_searches, create_search, get_search, delete_search
from .storage import load_results
from .scraper import build_mercadolibre_url, scrape_mercadolibre

def home(request):
    searches = get_all_searches()
    results = None
    search_data = None
    mensaje_guardado = None
    url_generada = None
    if request.method == 'POST':
        print("\n--- DATOS RECIBIDOS EN POST ---")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        name = request.POST.get('name', '')
        departamento = request.POST.get('departamento', '')
        ciudad = request.POST.get('ciudad', '') if departamento == 'Montevideo' else ''
        operacion = request.POST.get('operacion', '')
        tipo = request.POST.get('tipo', '')
        keywords_text = request.POST.get('keywords', '')
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        precio_min = request.POST.get('precio_min', '')
        precio_max = request.POST.get('precio_max', '')
        moneda = request.POST.get('moneda', 'USD')
        filters = {
            'departamento': departamento,
            'ciudad': ciudad,
            'operacion': operacion,
            'tipo': tipo,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'moneda': moneda,
        }
        url_generada = build_mercadolibre_url(filters)
        print(f"URL generada: {url_generada}")
        results = scrape_mercadolibre(filters, keywords)
        search_data = {'name': name, 'filters': filters, 'keywords': keywords}
        if request.POST.get('guardar') == '1' and name:
            from core.search_manager import update_search
            import datetime
            # Crear la búsqueda y obtener el id
            new_search = create_search({'name': name, 'filters': filters, 'keywords': keywords_text, 'enabled': True, 'platforms': ['mercadolibre']})
            # Guardar resultados y links visitados
            titulos = [r.get('titulo', r.get('url', '')) for r in results]
            links = [r.get('url') for r in results]
            update_search(new_search['id'], {
                'resultados': titulos,
                'links_visitados': links,
                'ultima_revision': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
            mensaje_guardado = f"Búsqueda '{name}' guardada correctamente."
            searches = get_all_searches()
    return render(request, 'core/home.html', {
        'searches': searches,
        'results': results,
        'search_data': search_data,
        'mensaje_guardado': mensaje_guardado,
        'url_generada': url_generada,
    })

def search_detail_view(request, search_id):
    search = get_search(search_id)
    results = load_results(search_id)
    advertencias = ["El texto de la búsqueda encuentra las palabras por separado en las publicaciones."]
    return render(request, 'core/search_detail.html', {'search': search, 'results': results, 'advertencias': advertencias})

def delete_search_view(request, search_id):
    delete_search(search_id)
    return redirect('core:home')
