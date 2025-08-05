# core/admin.py
from django.contrib import admin
from .models import Propiedad

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    # Mostramos los rangos para que sea más claro
    list_display = (
        'titulo', 
        'departamento', 
        'ciudad_barrio', 
        'precio_valor', 
        'dormitorios_min', 
        'dormitorios_max', 
        'banos_min',
        'banos_max'
    )
    list_filter = ('departamento', 'operacion', 'portal', 'tipo_inmueble')
    search_fields = ('titulo', 'descripcion', 'caracteristicas_texto')