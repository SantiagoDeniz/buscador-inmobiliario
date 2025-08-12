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
            # Pasar el texto original para que el procesamiento sea correcto
            create_search({'name': name, 'filters': filters, 'keywords': keywords_text, 'enabled': True, 'platforms': ['mercadolibre']})
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
    return render(request, 'core/search_detail.html', {'search': search, 'results': results})

def delete_search_view(request, search_id):
    delete_search(search_id)
    return redirect('core:home')
