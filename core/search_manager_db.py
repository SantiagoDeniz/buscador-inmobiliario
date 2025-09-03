# core/search_manager_db.py
"""
Sistema de gestión de búsquedas basado en base de datos
Reemplaza el sistema anterior basado en archivos JSON
"""

import uuid
import json
import re
import unicodedata
from typing import List, Dict, Any, Optional, Set, Tuple
from django.db import transaction
from django.db.models import Q, Count
from .models import (
    Busqueda, PalabraClave, BusquedaPalabraClave,
    Usuario, Plataforma, Propiedad, ResultadoBusqueda, Inmobiliaria
)

# ================================
# FUNCIONES PRINCIPALES DE BÚSQUEDA
# ================================

def get_all_searches() -> List[Dict[str, Any]]:
    """Obtiene todas las búsquedas del usuario actual"""
    searches = []
    for busqueda in Busqueda.objects.select_related('usuario').all():
        search_dict = {
            'id': str(busqueda.id),
            'nombre_busqueda': busqueda.nombre_busqueda,
            'texto_original': busqueda.texto_original,
            'guardado': busqueda.guardado,
            'filtros': busqueda.filtros,
            'usuario': busqueda.usuario.nombre if busqueda.usuario else None,
            'created_at': busqueda.created_at.isoformat(),
            'palabras_clave': [
                {
                    'texto': rel.palabra_clave.texto,
                    'idioma': rel.palabra_clave.idioma,
                    'sinonimos': rel.palabra_clave.sinonimos_list
                }
                for rel in busqueda.busquedapalabralave_set.select_related('palabra_clave').all()
            ]
        }
        searches.append(search_dict)
    return searches

def get_search(search_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una búsqueda específica por ID"""
    try:
        busqueda = Busqueda.objects.select_related('usuario').get(id=search_id)
        return {
            'id': str(busqueda.id),
            'nombre_busqueda': busqueda.nombre_busqueda,
            'texto_original': busqueda.texto_original,
            'guardado': busqueda.guardado,
            'filtros': busqueda.filtros,
            'usuario': busqueda.usuario.nombre if busqueda.usuario else None,
            'created_at': busqueda.created_at.isoformat(),
            'palabras_clave': [
                {
                    'texto': rel.palabra_clave.texto,
                    'idioma': rel.palabra_clave.idioma,
                    'sinonimos': rel.palabra_clave.sinonimos_list
                }
                for rel in busqueda.busquedapalabralave_set.select_related('palabra_clave').all()
            ]
        }
    except Busqueda.DoesNotExist:
        return None

@transaction.atomic
def save_search(search_data: Dict[str, Any]) -> str:
    """Guarda una nueva búsqueda en la base de datos"""
    # Asegurar una inmobiliaria por defecto (evita FK rota tras flush)
    inmobiliaria_default, _ = Inmobiliaria.objects.get_or_create(
        nombre='Inmobiliaria Default',
        defaults={'plan': 'basico'}
    )

    # Obtener o crear usuario por defecto asociado a la inmobiliaria
    usuario, _ = Usuario.objects.get_or_create(
        email='default@example.com',
        defaults={
            'nombre': 'Usuario Default',
            'password_hash': '!',  # marcador de contraseña no establecida
            'inmobiliaria': inmobiliaria_default,
        }
    )
    
    # Crear la búsqueda
    search_id = str(uuid.uuid4())
    busqueda = Busqueda.objects.create(
        id=search_id,
        nombre_busqueda=search_data.get('nombre_busqueda', 'Búsqueda sin nombre'),
        texto_original=search_data.get('texto_original', ''),
        filtros=search_data.get('filtros', {}),
        guardado=search_data.get('guardado', False),
        usuario=usuario
    )
    
    # Procesar y asociar palabras clave
    palabras_clave_texto = search_data.get('palabras_clave', [])
    if isinstance(palabras_clave_texto, str):
        palabras_clave_texto = [palabras_clave_texto]
    
    for palabra_texto in palabras_clave_texto:
        palabra_clave, created = get_or_create_palabra_clave(palabra_texto)
        BusquedaPalabraClave.objects.create(
            busqueda=busqueda,
            palabra_clave=palabra_clave
        )
    
    return search_id

def delete_search(search_id: str) -> bool:
    """Elimina una búsqueda por ID"""
    try:
        busqueda = Busqueda.objects.get(id=search_id)
        busqueda.delete()
        return True
    except Busqueda.DoesNotExist:
        return False

# ================================
# GESTIÓN DE PALABRAS CLAVE
# ================================

def get_or_create_palabra_clave(texto: str, idioma: str = 'es') -> PalabraClave:
    """Obtiene o crea una palabra clave con sinónimos"""
    texto_normalizado = normalizar_texto(texto)
    
    # Buscar palabra clave existente
    palabra_clave, created = PalabraClave.objects.get_or_create(
        texto=texto_normalizado,
        defaults={'idioma': idioma}
    )
    
    if created:
        # Si es nueva, generar sinónimos
        sinonimos = generar_sinonimos(texto_normalizado)
        palabra_clave.sinonimos_list = sinonimos
        palabra_clave.save()
    
    return palabra_clave

def procesar_keywords(texto_busqueda: str) -> List[Dict[str, Any]]:
    """Procesa el texto de búsqueda y extrae palabras clave con sinónimos"""
    palabras = extraer_palabras(texto_busqueda)
    keywords_data = []
    
    for palabra in palabras:
        palabra_clave = get_or_create_palabra_clave(palabra)
        keywords_data.append({
            'texto': palabra_clave.texto,
            'idioma': palabra_clave.idioma,
            'sinonimos': palabra_clave.sinonimos_list
        })
    
    return keywords_data

# ================================
# PROCESAMIENTO DE TEXTO
# ================================

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para búsquedas"""
    texto = unicodedata.normalize('NFD', texto.lower())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.strip()

def extraer_palabras(texto: str) -> List[str]:
    """Extrae palabras relevantes del texto de búsqueda"""
    texto_normalizado = normalizar_texto(texto)
    palabras = texto_normalizado.split()
    
    # Filtrar palabras muy cortas o comunes
    palabras_filtradas = [
        p for p in palabras 
        if len(p) > 2 and p not in {'que', 'con', 'para', 'por', 'una', 'uno', 'los', 'las', 'del', 'de', 'la', 'el'}
    ]
    
    return palabras_filtradas

def generar_sinonimos(palabra: str) -> List[str]:
    """Genera sinónimos para una palabra usando diccionario predefinido"""
    sinonimos_dict = {
        'apto': ['apartamento', 'depto', 'departamento'],
        'apartamento': ['apto', 'depto', 'departamento'],
        'dorm': ['dormitorio', 'habitacion', 'cuarto'],
        'dormitorio': ['dorm', 'habitacion', 'cuarto'],
        'garage': ['garaje', 'cochera', 'estacionamiento'],
        'garaje': ['garage', 'cochera', 'estacionamiento'],
        'balcon': ['balcón', 'terraza'],
        'balcón': ['balcon', 'terraza'],
        'baño': ['bano', 'sanitario'],
        'bano': ['baño', 'sanitario'],
        'casa': ['casas', 'vivienda', 'hogar'],
        'casas': ['casa', 'vivienda', 'hogar'],
        'ph': ['penthouse', 'duplex'],
        'penthouse': ['ph', 'atico'],
        'monoambiente': ['estudio', 'loft'],
        'jardin': ['jardín', 'patio', 'parque'],
        'jardín': ['jardin', 'patio', 'parque'],
        'esquina': ['esquina', 'corner'],
        'centro': ['centrico', 'downtown'],
        'cordon': ['cordón'],
        'cordón': ['cordon'],
        'pocitos': ['pocitos'],
        'carrasco': ['carrasco'],
        'malvin': ['malvin'],
        'buceo': ['buceo'],
        'nuevo': ['nueva', 'moderno', 'reciente'],
        'nueva': ['nuevo', 'moderno', 'reciente'],
        'lujo': ['lujoso', 'premium', 'exclusivo'],
        'barato': ['barata', 'economico', 'accesible'],
        'equipado': ['amueblado', 'furnished'],
        'amueblado': ['equipado', 'furnished'],
        'vista': ['view', 'panoramica'],
        'frente': ['facing', 'front'],
        'inversion': ['inversión', 'investment'],
        'inversión': ['inversion', 'investment'],
    }
    
    return sinonimos_dict.get(palabra, [])

# ================================
# BÚSQUEDA Y COINCIDENCIAS
# ================================

def buscar_coincidencias(busqueda_id: str, propiedades: List[Dict]) -> List[Dict]:
    """Busca coincidencias entre una búsqueda y propiedades"""
    try:
        busqueda = Busqueda.objects.get(id=busqueda_id)
        palabras_clave = busqueda.busquedapalabralave_set.select_related('palabra_clave').all()
        
        resultados = []
        for prop_data in propiedades:
            coincidencias = verificar_coincidencia(palabras_clave, prop_data)
            if coincidencias['coincide']:
                # Crear o actualizar propiedad en BD
                propiedad = crear_o_actualizar_propiedad(prop_data)
                
                # Guardar resultado
                resultado, created = ResultadoBusqueda.objects.get_or_create(
                    busqueda=busqueda,
                    propiedad=propiedad,
                    defaults={
                        'coincide': True,
                        'metadata': coincidencias
                    }
                )
                
                resultados.append({
                    'propiedad': prop_data,
                    'coincidencias': coincidencias,
                    'resultado_id': resultado.id
                })
        
        return resultados
    
    except Busqueda.DoesNotExist:
        return []

def verificar_coincidencia(palabras_clave_rel, propiedad_data: Dict) -> Dict:
    """Verifica si una propiedad coincide con las palabras clave de búsqueda"""
    texto_propiedad = f"{propiedad_data.get('titulo', '')} {propiedad_data.get('descripcion', '')}"
    texto_normalizado = normalizar_texto(texto_propiedad)
    
    coincidencias_encontradas = []
    total_palabras = len(palabras_clave_rel)
    
    for rel in palabras_clave_rel:
        palabra_clave = rel.palabra_clave
        todas_variantes = [palabra_clave.texto] + palabra_clave.sinonimos_list
        
        for variante in todas_variantes:
            if variante.lower() in texto_normalizado:
                coincidencias_encontradas.append({
                    'palabra_original': palabra_clave.texto,
                    'variante_encontrada': variante,
                    'sinonimo': variante != palabra_clave.texto
                })
                break
    
    porcentaje_coincidencia = (len(coincidencias_encontradas) / max(total_palabras, 1)) * 100
    
    return {
        'coincide': len(coincidencias_encontradas) > 0,
        'porcentaje': porcentaje_coincidencia,
        'palabras_encontradas': coincidencias_encontradas,
        'total_palabras': total_palabras,
        'palabras_coincidentes': len(coincidencias_encontradas)
    }

def crear_o_actualizar_propiedad(prop_data: Dict) -> Propiedad:
    """Crea o actualiza una propiedad en la base de datos"""
    # Obtener plataforma por defecto o crear
    plataforma, _ = Plataforma.objects.get_or_create(
        nombre='MercadoLibre',
        defaults={
            'url': 'https://mercadolibre.com.uy',
            'descripcion': 'Plataforma de clasificados'
        }
    )
    
    propiedad, created = Propiedad.objects.update_or_create(
        url=prop_data.get('url', ''),
        defaults={
            'titulo': prop_data.get('titulo', ''),
            'descripcion': prop_data.get('descripcion', ''),
            'metadata': prop_data,
            'plataforma': plataforma
        }
    )
    
    return propiedad

# ================================
# ESTADÍSTICAS Y REPORTES
# ================================

def get_search_stats() -> Dict[str, Any]:
    """Obtiene estadísticas de las búsquedas"""
    return {
        'total_searches': Busqueda.objects.count(),
        'saved_searches': Busqueda.objects.filter(guardado=True).count(),
        'total_keywords': PalabraClave.objects.count(),
        'total_properties': Propiedad.objects.count(),
        'total_results': ResultadoBusqueda.objects.count(),
        'successful_results': ResultadoBusqueda.objects.filter(coincide=True).count(),
    }

def get_popular_keywords(limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene las palabras clave más utilizadas"""
    keywords = PalabraClave.objects.annotate(
        uso_count=Count('busquedapalabralave')
    ).order_by('-uso_count')[:limit]
    
    return [
        {
            'texto': kw.texto,
            'idioma': kw.idioma,
            'usos': kw.uso_count,
            'sinonimos_count': len(kw.sinonimos_list)
        }
        for kw in keywords
    ]
