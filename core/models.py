# core/models.py
from django.db import models

class Propiedad(models.Model):
    # Datos principales que vemos en la lista de resultados
    titulo = models.CharField(max_length=255)
    precio_moneda = models.CharField(max_length=10, default='USD')
    precio_valor = models.IntegerField()
    url_publicacion = models.URLField(unique=True, max_length=500) # unique=True evita duplicados
    url_imagen = models.URLField(max_length=500)
    portal = models.CharField(max_length=50, default='mercadolibre')

    # Datos que obtendremos al visitar cada propiedad (búsqueda profunda)
    descripcion = models.TextField(blank=True, null=True) # blank=True, null=True significa que puede estar vacío
    caracteristicas = models.TextField(blank=True, null=True) # Guardaremos las características como un texto largo

    # Campos de control
    fecha_scrapeo = models.DateTimeField(auto_now=True) # Se actualiza cada vez que se guarda
    
    def __str__(self):
        return self.titulo