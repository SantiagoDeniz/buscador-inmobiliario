# core/admin.py
from django.contrib import admin
from .models import Propiedad

# Creamos una clase para personalizar cómo se ve el modelo en el admin
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'ciudad_barrio', 'precio_valor', 'dormitorios', 'banos')
    list_filter = ('departamento', 'operacion', 'portal') # Agregaremos 'operacion' al modelo después
    search_fields = ('titulo', 'descripcion', 'caracteristicas')

admin.site.register(Propiedad, PropiedadAdmin)