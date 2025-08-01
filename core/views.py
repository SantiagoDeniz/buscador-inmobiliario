# core/views.py

from django.shortcuts import render
from .models import Propiedad
from django.db.models import Q # Q nos permite hacer consultas complejas (OR, AND)
import re

def home(request):
    # Inicializamos la consulta con todos los objetos de la base de datos
    queryset = Propiedad.objects.all()
    
    # Obtenemos los parámetros del formulario
    search_params = {
        'operacion': request.GET.get('operacion'),
        'tipo_inmueble': request.GET.get('tipo_inmueble'),
        'ubicacion': request.GET.get('ubicacion'),
        'barrio': request.GET.get('barrio', ''),
        'dormitorios': request.GET.get('dormitorios'),
        'banos': request.GET.get('banos'),
        'texto_libre': request.GET.get('texto_libre', ''), # ¡NUESTRO CAMPO DE BÚSQUEDA PROFUNDA!
    }

    # --- Lógica de Filtrado en la Base de Datos ---
    # Solo aplicamos filtros si se envió el formulario (si 'operacion' tiene un valor)
    if search_params['operacion']:
        
        # Filtro por texto libre en título, descripción y características
        if search_params['texto_libre']:
            # Normalizamos y separamos las palabras clave
            palabras_clave = re.split(r'\s+', search_params['texto_libre'].lower())
            
            # Creamos un objeto Q por cada palabra clave para buscar en los 3 campos
            query_combinada = Q()
            for palabra in palabras_clave:
                if palabra:
                    query_palabra = (
                        Q(titulo__icontains=palabra) |
                        Q(descripcion__icontains=palabra) |
                        Q(caracteristicas__icontains=palabra)
                    )
                    query_combinada &= query_palabra # Usamos AND (&) para que deba contener todas las palabras
            
            queryset = queryset.filter(query_combinada)

        # Aquí irían los otros filtros (dormitorios, baños, etc.) si los implementamos en la BD
        # Por ahora, nos centramos en la búsqueda de texto
        
    # Si no se envió el formulario, no mostramos nada
    else:
        queryset = Propiedad.objects.none()

    resultados_count = queryset.count()
    
    context = {
        'resultados': queryset, # Pasamos los objetos de la BD directamente
        'resultados_count': resultados_count,
        **search_params
    }
    
    return render(request, 'core/home.html', context)