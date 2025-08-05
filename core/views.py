# core/views.py
from django.shortcuts import render
from .models import Propiedad
from django.db.models import Q
import re
from django.core.paginator import Paginator

def home(request):
    departamentos = Propiedad.objects.exclude(departamento='').order_by('departamento').values_list('departamento', flat=True).distinct()
    ciudades_barrios = Propiedad.objects.exclude(ciudad_barrio='').order_by('ciudad_barrio').values_list('ciudad_barrio', flat=True).distinct()

    if request.GET:
        queryset = Propiedad.objects.all()
        # ... (filtros de texto, departamento, etc. sin cambios)
        
        texto_libre = request.GET.get('texto_libre', '').strip()
        departamento_sel = request.GET.get('departamento', '')
        ciudad_barrio_sel = request.GET.get('ciudad_barrio', '')

        dormitorios_sel = request.GET.get('dormitorios', '')
        if dormitorios_sel:
            try:
                num_dorm = int(dormitorios_sel)
                # --- LÓGICA DE RANGO ---
                queryset = queryset.filter(dormitorios_min__lte=num_dorm, dormitorios_max__gte=num_dorm)
            except (ValueError, TypeError): pass

        banos_sel = request.GET.get('banos', '')
        if banos_sel:
            try:
                num_banos = int(banos_sel)
                queryset = queryset.filter(banos_min__lte=num_banos, banos_max__gte=num_banos)
            except (ValueError, TypeError): pass

        # --- FILTROS ADICIONALES ---
        moneda_sel = request.GET.get('moneda', '')
        precio_min = request.GET.get('precio_min', '')
        precio_max = request.GET.get('precio_max', '')
        cocheras_sel = request.GET.get('cocheras','')
        antiguedad_max = request.GET.get('antiguedad_max','')

        if texto_libre:
            palabras = [p for p in re.split(r'\s+', texto_libre.lower()) if len(p) > 2]
            q_objects = Q()
            for palabra in palabras:
                q_objects &= (Q(titulo__icontains=palabra) | Q(descripcion__icontains=palabra) | Q(caracteristicas_texto__icontains=palabra))
            queryset = queryset.filter(q_objects)

        if departamento_sel: queryset = queryset.filter(departamento__iexact=departamento_sel)
        if ciudad_barrio_sel: queryset = queryset.filter(ciudad_barrio__iexact=ciudad_barrio_sel)
        if dormitorios_sel: queryset = queryset.filter(dormitorios=dormitorios_sel)
        if banos_sel: queryset = queryset.filter(banos=banos_sel)
        if cocheras_sel: queryset = queryset.filter(cocheras__gte=int(cocheras_sel))
        if antiguedad_max: queryset = queryset.filter(antiguedad__lte=int(antiguedad_max))
        if moneda_sel: queryset = queryset.filter(precio_moneda__icontains=moneda_sel.replace('$', 'UYU'))
        if precio_min: queryset = queryset.filter(precio_valor__gte=int(precio_min))
        if precio_max: queryset = queryset.filter(precio_valor__lte=int(precio_max))
    else:
        queryset = Propiedad.objects.none()

    paginator = Paginator(queryset.order_by('-fecha_scrapeo'), 40)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj, 'request': request,
        'departamentos': departamentos, 'ciudades_barrios': ciudades_barrios
    }
    return render(request, 'core/home.html', context)