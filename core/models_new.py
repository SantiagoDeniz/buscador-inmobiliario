from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
import uuid

class Inmobiliaria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    plan = models.CharField(max_length=100)  # 'basico', 'premium', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inmobiliaria'
        verbose_name = 'Inmobiliaria'
        verbose_name_plural = 'Inmobiliarias'
    
    def __str__(self):
        return self.nombre

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    inmobiliaria = models.ForeignKey(Inmobiliaria, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nombre} ({self.email})"

class Plataforma(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plataforma'
        verbose_name = 'Plataforma'
        verbose_name_plural = 'Plataformas'
    
    def __str__(self):
        return self.nombre

class Busqueda(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_busqueda = models.CharField(max_length=255, blank=True, null=True)
    texto_original = models.TextField()
    filtros = JSONField(default=dict)  # Guardamos todos los filtros como JSON
    guardado = models.BooleanField(default=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'busqueda'
        verbose_name = 'Búsqueda'
        verbose_name_plural = 'Búsquedas'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.nombre_busqueda or f"Búsqueda {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class PalabraClave(models.Model):
    id = models.AutoField(primary_key=True)
    texto = models.CharField(max_length=100, unique=True)
    idioma = models.CharField(max_length=10, default='es')
    sinonimos = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    
    class Meta:
        db_table = 'palabra_clave'
        verbose_name = 'Palabra Clave'
        verbose_name_plural = 'Palabras Clave'
    
    def __str__(self):
        return self.texto

class BusquedaPalabraClave(models.Model):
    busqueda = models.ForeignKey(Busqueda, on_delete=models.CASCADE)
    palabra_clave = models.ForeignKey(PalabraClave, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'busqueda_palabra_clave'
        unique_together = ('busqueda', 'palabra_clave')
        verbose_name = 'Búsqueda - Palabra Clave'
        verbose_name_plural = 'Búsquedas - Palabras Clave'

class Propiedad(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.URLField(unique=True)
    titulo = models.CharField(max_length=500, blank=True, null=True)
    plataforma = models.ForeignKey(Plataforma, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'propiedad'
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.titulo or self.url

class ResultadoBusqueda(models.Model):
    id = models.AutoField(primary_key=True)
    busqueda = models.ForeignKey(Busqueda, on_delete=models.CASCADE)
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    coincide = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resultado_busqueda'
        unique_together = ('busqueda', 'propiedad')
        verbose_name = 'Resultado de Búsqueda'
        verbose_name_plural = 'Resultados de Búsqueda'
