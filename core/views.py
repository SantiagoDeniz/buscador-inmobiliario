# core/views.py
from django.shortcuts import render
from .models import Propiedad
from django.db.models import Q
import re
from django.core.paginator import Paginator

def home(request):
    # Obtener valores únicos para los dropdowns, excluyendo valores vacíos y ordenando
    departamentos = Propiedad.objects.exclude(departamento__exact='').order_by('departamento').values_list('departamento', flat=True).distinct()
    ciudades_barrios = Propiedad.objects.exclude(ciudad_barrio__exact='').order_by('ciudad_barrio').values_list('ciudad_barrio', flat=True).distinct()

    # Empezamos con todas las propiedades si el formulario fue enviado, sino con ninguna
    if request.GET:
        queryset = Propiedad.objects.all()

        # --- Lógica de Filtrado ---
        texto_libre = request.GET.get('texto_libre', '')
        departamento_sel = request.GET.get('departamento', '')
        ciudad_barrio_sel = request.GET.get('ciudad_barrio', '')
        dormitorios_sel = request.GET.get('dormitorios', '')
        banos_sel = request.GET.get('banos', '')
        moneda_sel = request.GET.get('moneda', 'USD')
        precio_min = request.GET.get('precio_min', '')
        precio_max = request.GET.get('precio_max', '')

        if texto_libre:
            palabras = [p for p in re.split(r'\s+', texto_libre.lower()) if len(p) > 2]
            query_combinada = Q()
            for palabra in palabras:
                query_combinada &= (Q(titulo__icontains=palabra) | Q(descripcion__icontains=palabra) | Q(caracteristicas__icontains=palabra))
            queryset = queryset.filter(query_combinada)

        if departamento_sel:
            queryset = queryset.filter(departamento__iexact=departamento_sel)
        
        if ciudad_barrio_sel:
            queryset = queryset.filter(ciudad_barrio__iexact=ciudad_barrio_sel)

        if dormitorios_sel:
            try:
                num_dorm = int(dormitorios_sel)
                # Búsqueda flexible en texto (cuando los datos estructurados son None)
                filtro_texto = Q(caracteristicas__icontains=f"{num_dorm} dormitorios") | Q(caracteristicas__icontains=f"Dormitorios: {num_dorm}")
                # Búsqueda en el campo numérico Y en el texto
                queryset = queryset.filter(Q(dormitorios=num_dorm) | filtro_texto)
            except (ValueError, TypeError): pass

        if banos_sel:
            try:
                num_banos = int(banos_sel)
                filtro_texto = Q(caracteristicas__icontains=f"{num_banos} baños") | Q(caracteristicas__icontains=f"Baños: {num_banos}")
                queryset = queryset.filter(Q(banos=num_banos) | filtro_texto)
            except (ValueError, TypeError): pass
        
        if moneda_sel:
            queryset = queryset.filter(precio_moneda__icontains=moneda_sel.replace('$', 'UYU'))
        
        if precio_min:
            try: queryset = queryset.filter(precio_valor__gte=int(precio_min))
            except (ValueError, TypeError): pass
        
        if precio_max:
            try: queryset = queryset.filter(precio_valor__lte=int(precio_max))
            except (ValueError, TypeError): pass
    else:
        queryset = Propiedad.objects.none()

    # --- Paginación ---
    paginator = Paginator(queryset.order_by('-fecha_scrapeo'), 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'request': request,
        'departamentos': departamentos,
        'ciudades_barrios': ciudades_barrios
    }
    
    return render(request, 'core/home.html', context)