# core/views.py

from django.shortcuts import render
from .scraper import scrape_mercadolibre

def home(request):
    resultados = None
    resultados_count = None
    
    search_params = {
        'operacion': request.GET.get('operacion', 'alquiler'),
        'tipo_inmueble': request.GET.get('tipo_inmueble', 'apartamento'),
        'ubicacion': request.GET.get('ubicacion', 'montevideo'),
        'precio_min': request.GET.get('precio_min', ''),
        'precio_max': request.GET.get('precio_max', ''),
        'dormitorios': request.GET.get('dormitorios', ''),
        'banos': request.GET.get('banos', ''),
        'cochera': request.GET.get('cochera', ''),
        'condicion': request.GET.get('condicion', ''),
        'barrio': request.GET.get('barrio', ''),
        'superficie': request.GET.get('superficie', ''),
        'antiguedad': request.GET.get('antiguedad', ''),
        # --- NUEVOS CHECKBOXES ---
        'amueblado': request.GET.get('amueblado', ''),
        'mascotas': request.GET.get('mascotas', ''),
        'aire': request.GET.get('aire', ''),
        'piscina': request.GET.get('piscina', ''),
        'terraza': request.GET.get('terraza', ''),
        'jardin': request.GET.get('jardin', ''),
    }

    if 'operacion' in request.GET:
        resultados = scrape_mercadolibre(search_params)
        if resultados is not None:
            resultados_count = len(resultados)

    context = {
        'resultados': resultados,
        'resultados_count': resultados_count,
        **search_params
    }
    
    return render(request, 'core/home.html', context)