"""
Gestor de búsquedas y resultados basado en base de datos (ORM Django).
Archivo principal: core/search_manager.py
"""
"""
Sistema de gestión de búsquedas basado en base de datos.
Reemplaza el sistema anterior basado en archivos JSON.
"""

import uuid
import json
import re
import unicodedata
from typing import List, Dict, Any, Optional, Set, Tuple
from django.db import transaction
from django.utils import timezone
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
            # Alias de compatibilidad para tests/consumidores antiguos
            'filters': busqueda.filtros,
            'usuario': busqueda.usuario.nombre if busqueda.usuario else None,
            'created_at': busqueda.created_at.isoformat(),
            'palabras_clave': [
                {
                    'texto': rel.palabra_clave.texto,
                    'idioma': rel.palabra_clave.idioma,
                    'sinonimos': rel.palabra_clave.sinonimos_list
                }
                for rel in busqueda.busquedapalabraclave_set.select_related('palabra_clave').all()
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
                for rel in busqueda.busquedapalabraclave_set.select_related('palabra_clave').all()
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
        palabra_clave = get_or_create_palabra_clave(palabra_texto)
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
        palabra_clave.set_sinonimos(sinonimos)
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
        palabras_clave = busqueda.busquedapalabraclave_set.select_related('palabra_clave').all()
        
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
    """Verifica coincidencia con lógica de grupos (OR dentro de sinónimos, AND entre palabras)."""
    texto_propiedad = f"{propiedad_data.get('titulo', '')} {propiedad_data.get('descripcion', '')}"
    texto_normalizado = normalizar_texto(texto_propiedad)

    coincidencias_encontradas = []
    total_palabras = len(palabras_clave_rel)

    grupos_ok = []
    for rel in palabras_clave_rel:
        palabra_clave = rel.palabra_clave
        variantes = [palabra_clave.texto] + (palabra_clave.sinonimos_list or [])
        variantes_norm = [normalizar_texto(v) for v in variantes]
        encontrada = None
        for v, v_norm in zip(variantes, variantes_norm):
            if v_norm in texto_normalizado:
                encontrada = v
                break
            if len(v_norm) > 4 and v_norm[:-2] in texto_normalizado:
                encontrada = v
                break
        grupos_ok.append(bool(encontrada))
        if encontrada:
            coincidencias_encontradas.append({
                'palabra_original': palabra_clave.texto,
                'variante_encontrada': encontrada,
                'sinonimo': encontrada != palabra_clave.texto
            })

    if total_palabras:
        encontrados = sum(1 for x in grupos_ok if x)
        coincide_flag = all(grupos_ok)
        porcentaje = (encontrados / total_palabras) * 100
    else:
        coincide_flag = True
        porcentaje = 100.0

    return {
        'coincide': coincide_flag,
        'porcentaje': porcentaje,
        'palabras_encontradas': coincidencias_encontradas,
        'total_palabras': total_palabras,
        'palabras_coincidentes': sum(1 for x in grupos_ok if x)
    }

def crear_o_actualizar_propiedad(prop_data: Dict) -> Propiedad:
    """Crea o actualiza una propiedad en la base de datos evitando títulos placeholder.

    Reglas:
    - Acepta tanto 'titulo' como 'title' en la entrada.
    - No guarda como título valores placeholder como "Publicación" o "Sin título".
    - No sobreescribe un título existente válido con un placeholder.
    """
    # Obtener plataforma por defecto o crear
    plataforma, _ = Plataforma.objects.get_or_create(
        nombre='MercadoLibre',
        defaults={
            'url': 'https://mercadolibre.com.uy',
            'descripcion': 'Plataforma de clasificados'
        }
    )

    url = prop_data.get('url', '')
    incoming_title = prop_data.get('titulo') or prop_data.get('title') or ''

    def es_placeholder(t: str) -> bool:
        t_norm = normalizar_texto(t or '')
        return t_norm in {'publicacion', 'sin titulo'} or t.strip() == ''

    # Crear o recuperar la propiedad por URL
    propiedad, created = Propiedad.objects.get_or_create(
        url=url,
        defaults={
            'plataforma': plataforma
        }
    )

    # Siempre vincular plataforma y actualizar metadata/descripcion
    propiedad.plataforma = plataforma
    if 'descripcion' in prop_data:
        propiedad.descripcion = prop_data.get('descripcion', '')
    # Guardar metadata completa del resultado
    try:
        propiedad.metadata = prop_data
    except Exception:
        # Si por algún motivo no es serializable, guardamos parcial
        try:
            propiedad.metadata = {
                'titulo': prop_data.get('titulo') or prop_data.get('title'),
                'url': url
            }
        except Exception:
            pass

    # Actualizar título solo si el entrante no es placeholder
    if incoming_title and not es_placeholder(incoming_title):
        # Si es nuevo o el existente es vacío/placeholder, actualizar
        if created or es_placeholder(propiedad.titulo or ''):
            propiedad.titulo = incoming_title

    propiedad.save()
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
        uso_count=Count('busquedapalabraclave')
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

# ================================
# FUNCIONES DE COMPATIBILIDAD
# ================================

def load_results(search_id: str) -> List[Dict]:
    """Carga resultados de búsqueda desde la base de datos (compatibilidad)"""
    try:
        busqueda = Busqueda.objects.get(id=search_id)
        resultados = ResultadoBusqueda.objects.filter(
            busqueda=busqueda, 
            coincide=True
        ).select_related('propiedad').all()
        
        results = []
        for resultado in resultados:
            prop = resultado.propiedad
            result_data = prop.metadata.copy() if prop.metadata else {}
            # Fallback de título: si el campo de modelo está vacío/placeholder, usar metadata['titulo'] o ['title']
            meta_title = (result_data.get('titulo') or result_data.get('title') or '').strip()
            model_title = (prop.titulo or '').strip()
            def _es_placeholder(t: str) -> bool:
                t_norm = normalizar_texto(t or '')
                return t_norm in {'publicacion', 'sin titulo'} or t.strip() == ''
            titulo_final = model_title if model_title and not _es_placeholder(model_title) else (meta_title if meta_title and not _es_placeholder(meta_title) else None)
            
            # Añadir información estándar
            result_data.update({
                'id': str(resultado.id),
                'titulo': titulo_final or prop.titulo or meta_title or 'Sin título',
                'url': prop.url,
                'descripcion': prop.descripcion,
                'plataforma': prop.plataforma.nombre,
                'coincidencias': resultado.metadata if resultado.metadata else {},
                'created_at': resultado.created_at.isoformat()
            })
            
            results.append(result_data)
        
        return results
        
    except Busqueda.DoesNotExist:
        return []

def save_results(search_id: str, results: List[Dict]) -> bool:
    """Guarda resultados de búsqueda en la base de datos (compatibilidad)"""
    try:
        busqueda = Busqueda.objects.get(id=search_id)        
        for result_data in results:
            # Crear o actualizar propiedad
            propiedad = crear_o_actualizar_propiedad(result_data)
            
            # Crear resultado si no existe
            resultado, created = ResultadoBusqueda.objects.get_or_create(
                busqueda=busqueda,
                propiedad=propiedad,
                defaults={
                    'coincide': True,
                    'metadata': result_data,
                    'seen_count': 1,
                    'last_seen_at': timezone.now()
                }
            )
            if not created:
                # Actualizar métricas de visualización sin sobreescribir metadata buena
                try:
                    ResultadoBusqueda.objects.filter(id=resultado.id).update(
                        seen_count=(resultado.seen_count or 0) + 1,
                        last_seen_at=timezone.now()
                    )
                except Exception:
                    pass
        
        return True
        
    except Exception as e:
        print(f"Error guardando resultados: {e}")
        return False

from datetime import datetime

def create_search(search_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una nueva búsqueda (compatibilidad con consumers.py)"""
    # Mapear campos del formato anterior al nuevo
    new_search_data = {
        'nombre_busqueda': search_data.get('name', 'Búsqueda sin nombre'),
        'texto_original': search_data.get('original_text', ''),
        'filtros': search_data.get('filters', {}),
        'palabras_clave': search_data.get('keywords', []),
        'guardado': True
    }
    
    search_id = save_search(new_search_data)
    
    return {
        'id': search_id,
        'name': new_search_data['nombre_busqueda'],
        'created_at': datetime.now().isoformat()
    }

def update_search(search_id: str, data: Dict[str, Any]) -> bool:
    """Actualiza una búsqueda existente (compatibilidad con consumers.py)"""
    try:
        busqueda = Busqueda.objects.get(id=search_id)
        
        # Actualizar campos si se proporcionan
        if 'name' in data:
            busqueda.nombre_busqueda = data['name']
        if 'filters' in data:
            busqueda.filtros = data['filters']
        if 'ultima_revision' in data and data['ultima_revision']:
            # Acepta str o datetime
            try:
                if isinstance(data['ultima_revision'], str):
                    # Parseo la fecha en formato 'YYYY-mm-dd HH:MM:SS' si viene como string
                    from datetime import datetime
                    try:
                        busqueda.ultima_revision = datetime.fromisoformat(data['ultima_revision'])
                    except Exception:
                        busqueda.ultima_revision = timezone.now()
                else:
                    busqueda.ultima_revision = data['ultima_revision']
            except Exception:
                busqueda.ultima_revision = timezone.now()
        if 'results' in data:
            # Guardar resultados usando la función de compatibilidad
            save_results(search_id, data['results'])
        
        busqueda.save()
        return True
        
    except Busqueda.DoesNotExist:
        return False
