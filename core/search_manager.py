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
    Busqueda, PalabraClave, BusquedaPalabraClave, PalabraClavePropiedad,
    Usuario, Plataforma, Propiedad, ResultadoBusqueda, Inmobiliaria
)
from .scraper.utils import stemming_basico

# ================================
# FUNCIONES PRINCIPALES DE BÚSQUEDA
# ================================

def get_all_searches() -> List[Dict[str, Any]]:
    """Obtiene todas las búsquedas GUARDADAS del usuario actual (solo guardado=True para la interfaz)"""
    searches = []
    # Filtrar solo las búsquedas que deben aparecer en la interfaz
    for busqueda in Busqueda.objects.select_related('usuario').filter(guardado=True):
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

def get_all_search_history() -> List[Dict[str, Any]]:
    """Obtiene TODAS las búsquedas (guardadas y no guardadas) para análisis/debugging"""
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
                for rel in busqueda.busquedapalabraclave_set.select_related('palabra_clave').all()
            ]
        }
        searches.append(search_dict)
    return searches

def get_search(search_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una búsqueda específica por ID"""
    try:
        # Validar que sea un UUID válido antes de la consulta
        import uuid
        try:
            uuid.UUID(search_id)
        except (ValueError, TypeError):
            print(f"[BÚSQUEDA] UUID inválido: {search_id}")
            return None
        
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
    """Elimina una búsqueda de la lista del usuario
    Nota técnica: Implementa eliminación suave (guardado=False) preservando datos para análisis"""
    try:
        # Validar UUID antes de consulta
        import uuid
        try:
            uuid.UUID(search_id)
        except (ValueError, TypeError):
            print(f"[BÚSQUEDA] UUID inválido: {search_id}")
            return False
            
        busqueda = Busqueda.objects.get(id=search_id, guardado=True)
        busqueda.guardado = False
        busqueda.save()
        print(f"[BÚSQUEDA] Búsqueda {search_id} eliminada de la lista del usuario")
        return True
    except Busqueda.DoesNotExist:
        print(f"[BÚSQUEDA] No se encontró búsqueda con ID {search_id}")
        return False

def delete_search_permanently(search_id: str) -> bool:
    """Elimina una búsqueda físicamente de la base de datos (solo para mantenimiento)
    ⚠️ CUIDADO: Esta operación es irreversible y elimina todos los datos relacionados"""
    try:
        busqueda = Busqueda.objects.get(id=search_id)
        busqueda.delete()
        print(f"[MANTENIMIENTO] Búsqueda {search_id} eliminada permanentemente")
        return True
    except Busqueda.DoesNotExist:
        print(f"[MANTENIMIENTO] No se encontró búsqueda con ID {search_id}")
        return False

def restore_search_from_history(search_id: str) -> bool:
    """Función administrativa: Recupera una búsqueda previamente eliminada por el usuario
    Nota técnica: Cambia guardado=False a guardado=True para mostrarla nuevamente en la interfaz"""
    try:
        busqueda = Busqueda.objects.get(id=search_id, guardado=False)
        busqueda.guardado = True
        busqueda.save()
        print(f"[ADMINISTRACIÓN] Búsqueda {search_id} recuperada y mostrada en la interfaz del usuario")
        return True
    except Busqueda.DoesNotExist:
        print(f"[ADMINISTRACIÓN] No se encontró búsqueda eliminada con ID {search_id}")
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
    if not texto:
        return ""
    texto = unicodedata.normalize('NFD', texto.lower())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.strip()

def extraer_palabras(texto: str) -> List[str]:
    """Extrae palabras relevantes del texto de búsqueda"""
    if not texto:
        return []
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
        return 'publicacion' in t_norm or 'sin titulo' in t_norm or t.strip() == ''

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
                return 'publicacion' in t_norm or 'sin titulo' in t_norm or t.strip() == ''
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
            # Usar el campo coincide del resultado si está disponible, sino True por defecto
            coincide_valor = result_data.get('coincide', True)
            
            resultado, created = ResultadoBusqueda.objects.get_or_create(
                busqueda=busqueda,
                propiedad=propiedad,
                defaults={
                    'coincide': coincide_valor,
                    'metadata': result_data,
                    'seen_count': 1,
                    'last_seen_at': timezone.now()
                }
            )
            if not created:
                # Actualizar métricas de visualización y coincidencia
                try:
                    ResultadoBusqueda.objects.filter(id=resultado.id).update(
                        seen_count=(resultado.seen_count or 0) + 1,
                        last_seen_at=timezone.now(),
                        coincide=coincide_valor  # Actualizar coincidencia también
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


# ================================
# GESTIÓN DE KEYWORDS EN PROPIEDADES
# ================================

def verificar_keywords_en_propiedad(propiedad: Propiedad, palabras_clave: List[PalabraClave]) -> Dict[str, bool]:
    """
    Verifica si cada palabra clave (o sus sinónimos) se encuentra en una propiedad específica.
    
    Args:
        propiedad: Instancia de Propiedad
        palabras_clave: Lista de instancias de PalabraClave
    
    Returns:
        Dict con palabra_clave.texto como key y bool como value indicando si fue encontrada
    """
    # Construir texto completo de la propiedad
    titulo = propiedad.titulo or ''
    descripcion = propiedad.descripcion or ''
    caracteristicas = ''
    
    # Extraer características del metadata si existe
    if propiedad.metadata and isinstance(propiedad.metadata, dict):
        # Intentar usar el nuevo formato primero
        if 'caracteristicas_texto' in propiedad.metadata:
            caracteristicas = propiedad.metadata.get('caracteristicas_texto', '')
        elif 'caracteristicas_dict' in propiedad.metadata:
            # Si solo hay dict, convertir a texto
            carac_dict = propiedad.metadata.get('caracteristicas_dict', {})
            caracteristicas = ' '.join(f"{k}: {v}" for k, v in carac_dict.items())
        else:
            # Formato legacy: buscar en toda la metadata
            caracteristicas = propiedad.metadata.get('caracteristicas', '')
        
        if isinstance(caracteristicas, dict):
            # Si caracteristicas es un dict, extraer todos los valores
            caracteristicas = ' '.join(str(v) for v in caracteristicas.values())
    
    texto_total = f"{titulo} {descripcion} {caracteristicas}".lower()
    texto_normalizado = normalizar_texto(texto_total)
    
    resultados = {}
    
    for palabra_clave in palabras_clave:
        encontrada = False
        
        # Crear lista de variantes a buscar (palabra + sinónimos)
        variantes = [palabra_clave.texto] + palabra_clave.sinonimos_list
        
        # Buscar cada variante en el texto
        for variante in variantes:
            variante_norm = normalizar_texto(variante)
            
            # Búsqueda exacta
            if variante_norm in texto_normalizado:
                encontrada = True
                break
            
            # Búsqueda con stemming básico
            variante_stem = stemming_basico(variante_norm)
            if variante_stem and variante_stem in texto_normalizado:
                encontrada = True
                break
            
            # Búsqueda parcial para palabras largas (>4 caracteres)
            if len(variante_norm) > 4 and variante_norm[:-2] in texto_normalizado:
                encontrada = True
                break
        
        resultados[palabra_clave.texto] = encontrada
        
        # Log para debugging
        estado = "✓" if encontrada else "✗"
        print(f"[KEYWORD] {palabra_clave.texto} {estado} en {propiedad.titulo or propiedad.url}")
    
    return resultados


def actualizar_relaciones_keywords(propiedad: Propiedad, palabras_clave: List[PalabraClave], 
                                 resultados_busqueda: Dict[str, bool] = None) -> Dict[str, bool]:
    """
    Actualiza o crea las relaciones palabra_clave-propiedad con el estado encontrada.
    
    Args:
        propiedad: Instancia de Propiedad
        palabras_clave: Lista de instancias de PalabraClave
        resultados_busqueda: Dict opcional con resultados previos de búsqueda
    
    Returns:
        Dict con palabra_clave.texto como key y bool como value del estado encontrada
    """
    if not resultados_busqueda:
        resultados_busqueda = verificar_keywords_en_propiedad(propiedad, palabras_clave)
    
    resultados_finales = {}
    
    with transaction.atomic():
        for palabra_clave in palabras_clave:
            encontrada = resultados_busqueda.get(palabra_clave.texto, False)
            
            # Crear o actualizar la relación
            relacion, created = PalabraClavePropiedad.objects.update_or_create(
                palabra_clave=palabra_clave,
                propiedad=propiedad,
                defaults={'encontrada': encontrada}
            )
            
            resultados_finales[palabra_clave.texto] = encontrada
            
            # Log para debugging
            accion = "creada" if created else "actualizada"
            estado = "encontrada" if encontrada else "no encontrada"
            print(f"[RELACIÓN] {accion}: {palabra_clave.texto} - {propiedad.titulo or propiedad.url} ({estado})")
    
    return resultados_finales


def verificar_coincidencias_keywords(busqueda: Busqueda, propiedad: Propiedad) -> bool:
    """
    Verifica si todas las palabras clave de una búsqueda tienen encontrada=True para una propiedad.
    
    Args:
        busqueda: Instancia de Busqueda
        propiedad: Instancia de Propiedad
    
    Returns:
        True si todas las keywords de la búsqueda fueron encontradas, False en caso contrario
    """
    # Obtener todas las palabras clave de la búsqueda
    palabras_clave_busqueda = [
        rel.palabra_clave 
        for rel in busqueda.busquedapalabraclave_set.select_related('palabra_clave').all()
    ]
    
    if not palabras_clave_busqueda:
        # Si no hay keywords específicas, consideramos que coincide
        return True
    
    # Verificar que existan relaciones para todas las palabras clave
    for palabra_clave in palabras_clave_busqueda:
        try:
            relacion = PalabraClavePropiedad.objects.get(
                palabra_clave=palabra_clave,
                propiedad=propiedad
            )
            if not relacion.encontrada:
                print(f"[COINCIDENCIA] ✗ {palabra_clave.texto} no encontrada en {propiedad.titulo or propiedad.url}")
                return False
        except PalabraClavePropiedad.DoesNotExist:
            print(f"[COINCIDENCIA] ✗ Sin relación para {palabra_clave.texto} en {propiedad.titulo or propiedad.url}")
            return False
    
    print(f"[COINCIDENCIA] ✓ Todas las keywords encontradas en {propiedad.titulo or propiedad.url}")
    return True


def procesar_propiedad_existente(propiedad: Propiedad, palabras_clave: List[PalabraClave]) -> Dict[str, bool]:
    """
    Procesa una propiedad existente en BD verificando relaciones keywords existentes.
    Solo busca keywords que no tienen relación previa con la propiedad.
    
    Args:
        propiedad: Instancia de Propiedad existente
        palabras_clave: Lista de PalabraClave de la búsqueda actual
    
    Returns:
        Dict con resultados finales de todas las keywords
    """
    print(f"[PROCESANDO] Propiedad existente: {propiedad.titulo or propiedad.url}")
    
    resultados_finales = {}
    palabras_sin_relacion = []
    
    # Verificar qué keywords ya tienen relación
    for palabra_clave in palabras_clave:
        try:
            relacion = PalabraClavePropiedad.objects.get(
                palabra_clave=palabra_clave,
                propiedad=propiedad
            )
            # Ya existe relación, usar el valor almacenado
            resultados_finales[palabra_clave.texto] = relacion.encontrada
            print(f"[RELACIÓN EXISTENTE] {palabra_clave.texto}: {relacion.encontrada}")
        except PalabraClavePropiedad.DoesNotExist:
            # No existe relación, necesita ser procesada
            palabras_sin_relacion.append(palabra_clave)
    
    # Procesar keywords sin relación previa
    if palabras_sin_relacion:
        print(f"[PROCESANDO] {len(palabras_sin_relacion)} keywords sin relación previa")
        resultados_nuevos = actualizar_relaciones_keywords(propiedad, palabras_sin_relacion)
        resultados_finales.update(resultados_nuevos)
    
    return resultados_finales


def procesar_propiedad_nueva(url: str, plataforma: Plataforma, palabras_clave: List[PalabraClave]) -> Tuple[Propiedad, Dict[str, bool]]:
    """
    Procesa una propiedad nueva: scrapea, guarda en BD y crea relaciones keywords.
    
    Args:
        url: URL de la propiedad a scrapear
        plataforma: Instancia de Plataforma
        palabras_clave: Lista de PalabraClave de la búsqueda
    
    Returns:
        Tuple con (Propiedad creada, Dict con resultados keywords)
    """
    print(f"[PROCESANDO] Propiedad nueva: {url}")
    
    # Importar funciones de scraping
    from .scraper.extractors import scrape_detalle_con_requests
    
    try:
        # Scrapear detalles de la propiedad
        detalles = scrape_detalle_con_requests(url)
        
        if not detalles:
            print(f"[ERROR] No se pudieron obtener detalles para {url}")
            # Crear propiedad básica sin detalles
            with transaction.atomic():
                propiedad = Propiedad.objects.create(
                    url=url,
                    plataforma=plataforma,
                    titulo="",
                    descripcion="",
                    metadata={}
                )
                
                # Marcar todas las keywords como no encontradas
                resultados = {palabra.texto: False for palabra in palabras_clave}
                actualizar_relaciones_keywords(propiedad, palabras_clave, resultados)
                
                return propiedad, resultados
        
        # Crear propiedad con detalles scrapeados
        with transaction.atomic():
            # Construir metadata completo con todas las características
            metadata_completo = {
                'caracteristicas_dict': detalles.get('caracteristicas_dict', {}),
                'caracteristicas_texto': detalles.get('caracteristicas_texto', ''),
                'precio_moneda': detalles.get('precio_moneda', ''),
                'precio_valor': detalles.get('precio_valor', 0),
                'url_imagen': detalles.get('url_imagen', ''),
                'tipo_inmueble': detalles.get('tipo_inmueble', ''),
                'condicion': detalles.get('condicion', ''),
                # Características estructurales
                'dormitorios_min': detalles.get('dormitorios_min'),
                'dormitorios_max': detalles.get('dormitorios_max'),
                'banos_min': detalles.get('banos_min'),
                'banos_max': detalles.get('banos_max'),
                'superficie_total_min': detalles.get('superficie_total_min'),
                'superficie_total_max': detalles.get('superficie_total_max'),
                'superficie_cubierta_min': detalles.get('superficie_cubierta_min'),
                'superficie_cubierta_max': detalles.get('superficie_cubierta_max'),
                'cocheras_min': detalles.get('cocheras_min'),
                'cocheras_max': detalles.get('cocheras_max'),
                'antiguedad': detalles.get('antiguedad'),
                # Características booleanas
                'es_amoblado': detalles.get('es_amoblado', False),
                'admite_mascotas': detalles.get('admite_mascotas', False),
                'tiene_piscina': detalles.get('tiene_piscina', False),
                'tiene_terraza': detalles.get('tiene_terraza', False),
                'tiene_jardin': detalles.get('tiene_jardin', False),
            }
            
            propiedad = Propiedad.objects.create(
                url=url,
                plataforma=plataforma,
                titulo=detalles.get('titulo', ''),
                descripcion=detalles.get('descripcion', ''),
                metadata=metadata_completo
            )
            
            print(f"[CREADA] Propiedad: {propiedad.titulo or propiedad.url}")
            
            # Procesar keywords en la nueva propiedad
            resultados = actualizar_relaciones_keywords(propiedad, palabras_clave)
            
            return propiedad, resultados
            
    except Exception as e:
        print(f"[ERROR] Error procesando propiedad nueva {url}: {str(e)}")
        # Crear propiedad básica en caso de error
        with transaction.atomic():
            propiedad = Propiedad.objects.create(
                url=url,
                plataforma=plataforma,
                titulo="",
                descripcion="",
                metadata={}
            )
            
            # Marcar todas las keywords como no encontradas
            resultados = {palabra.texto: False for palabra in palabras_clave}
            actualizar_relaciones_keywords(propiedad, palabras_clave, resultados)
            
            return propiedad, resultados


def guardar_resultado_busqueda_con_keywords(busqueda: Busqueda, propiedad: Propiedad) -> ResultadoBusqueda:
    """
    Guarda un resultado de búsqueda verificando coincidencias de keywords usando el nuevo sistema.
    
    Args:
        busqueda: Instancia de Busqueda
        propiedad: Instancia de Propiedad
    
    Returns:
        Instancia de ResultadoBusqueda creada o actualizada
    """
    # Verificar si todas las keywords de la búsqueda coinciden
    coincide = verificar_coincidencias_keywords(busqueda, propiedad)
    
    # Crear o actualizar el resultado
    resultado, created = ResultadoBusqueda.objects.update_or_create(
        busqueda=busqueda,
        propiedad=propiedad,
        defaults={
            'coincide': coincide,
            'last_seen_at': timezone.now(),
        }
    )
    
    # Incrementar contador si ya existía
    if not created:
        resultado.seen_count += 1
        resultado.save()
    
    accion = "creado" if created else "actualizado"
    estado = "coincide" if coincide else "no coincide"
    print(f"[RESULTADO] {accion}: {busqueda.nombre_busqueda or 'Búsqueda'} - {propiedad.titulo or propiedad.url} ({estado})")
    
    return resultado
