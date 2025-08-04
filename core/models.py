# core/models.py
from django.db import models

class Propiedad(models.Model):
    # Datos principales
    titulo = models.CharField(max_length=255)
    precio_moneda = models.CharField(max_length=10, default='USD')
    precio_valor = models.IntegerField()
    url_publicacion = models.URLField(unique=True, max_length=500)
    url_imagen = models.URLField(max_length=500)
    portal = models.CharField(max_length=50, default='mercadolibre')
    operacion = models.CharField(max_length=50, blank=True)

    # Datos estructurados
    departamento = models.CharField(max_length=100, blank=True)
    ciudad_barrio = models.CharField(max_length=100, blank=True)
    dormitorios = models.IntegerField(null=True, blank=True)
    banos = models.IntegerField(null=True, blank=True)
    
    # --- NUEVOS CAMPOS AÑADIDOS ---
    superficie_total = models.IntegerField(null=True, blank=True)
    superficie_cubierta = models.IntegerField(null=True, blank=True)
    cocheras = models.IntegerField(null=True, blank=True)
    antiguedad = models.CharField(max_length=50, blank=True) # Texto para "A estrenar", "5 años", etc.
    
    # Datos de texto para búsqueda libre
    descripcion = models.TextField(blank=True, null=True)
    caracteristicas = models.TextField(blank=True, null=True)

    # Campos de control
    fecha_scrapeo = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo