# core/models.py
from django.db import models

class Propiedad(models.Model):
    # Campos de Identificación y Precio (sin cambios)
    titulo = models.CharField(max_length=255)
    url_publicacion = models.URLField(unique=True, max_length=500)
    portal = models.CharField(max_length=50, default='mercadolibre')
    precio_moneda = models.CharField(max_length=10, blank=True)
    precio_valor = models.IntegerField(null=True, blank=True)
    
    # Campos Categóricos (sin cambios)
    operacion = models.CharField(max_length=50, blank=True)
    tipo_inmueble = models.CharField(max_length=100, blank=True)
    condicion = models.CharField(max_length=50, blank=True)
    
    # Campos de Ubicación (sin cambios)
    departamento = models.CharField(max_length=100, blank=True)
    ciudad_barrio = models.CharField(max_length=100, blank=True)
    
    # --- CAMPOS NUMÉRICOS REEMPLAZADOS POR RANGOS ---
    dormitorios_min = models.PositiveIntegerField(null=True, blank=True)
    dormitorios_max = models.PositiveIntegerField(null=True, blank=True)
    banos_min = models.PositiveIntegerField(null=True, blank=True)
    banos_max = models.PositiveIntegerField(null=True, blank=True)
    superficie_total_min = models.PositiveIntegerField(null=True, blank=True)
    superficie_total_max = models.PositiveIntegerField(null=True, blank=True)
    superficie_cubierta_min = models.PositiveIntegerField(null=True, blank=True)
    superficie_cubierta_max = models.PositiveIntegerField(null=True, blank=True)
    cocheras_min = models.PositiveIntegerField(null=True, blank=True)
    cocheras_max = models.PositiveIntegerField(null=True, blank=True)
    antiguedad = models.PositiveIntegerField(null=True, blank=True)
    
    # --- Campos Booleanos (sin cambios) ---
    es_amoblado = models.BooleanField(default=False)
    admite_mascotas = models.BooleanField(default=False)
    tiene_piscina = models.BooleanField(default=False)
    tiene_terraza = models.BooleanField(default=False)
    tiene_jardin = models.BooleanField(default=False)
    tiene_tour_virtual = models.BooleanField(default=False)

    # --- Campos de Texto y Control ---
    url_imagen = models.URLField(max_length=500, blank=True)
    descripcion = models.TextField(blank=True)
    caracteristicas_texto = models.TextField(blank=True)
    fecha_scrapeo = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo