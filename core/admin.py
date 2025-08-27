# core/admin.py
from django.contrib import admin
from .models import *

@admin.register(Inmobiliaria)
class InmobiliariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plan', 'created_at')
    list_filter = ('plan', 'created_at')
    search_fields = ('nombre',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'inmobiliaria', 'created_at')
    list_filter = ('inmobiliaria', 'created_at')
    search_fields = ('nombre', 'email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'url', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Busqueda)
class BusquedaAdmin(admin.ModelAdmin):
    list_display = ('nombre_busqueda', 'texto_original', 'guardado', 'usuario', 'created_at')
    list_filter = ('guardado', 'usuario', 'created_at')
    search_fields = ('nombre_busqueda', 'texto_original')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(PalabraClave)
class PalabraClaveAdmin(admin.ModelAdmin):
    list_display = ('texto', 'idioma', 'get_sinonimos')
    list_filter = ('idioma',)
    search_fields = ('texto',)
    
    def get_sinonimos(self, obj):
        return ', '.join(obj.sinonimos_list[:3])  # Solo primeros 3
    get_sinonimos.short_description = 'Sinónimos'

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'url', 'plataforma', 'created_at')
    list_filter = ('plataforma', 'created_at')
    search_fields = ('titulo', 'url')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ResultadoBusqueda)
class ResultadoBusquedaAdmin(admin.ModelAdmin):
    list_display = ('busqueda', 'propiedad', 'coincide', 'created_at')
    list_filter = ('coincide', 'created_at')
    search_fields = ('busqueda__nombre_busqueda', 'propiedad__titulo')
    readonly_fields = ('created_at',)

@admin.register(BusquedaPalabraClave)
class BusquedaPalabraClaveAdmin(admin.ModelAdmin):
    list_display = ('busqueda', 'palabra_clave')
    list_filter = ('palabra_clave',)