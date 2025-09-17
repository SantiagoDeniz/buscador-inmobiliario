import concurrent.futures
import os
import unicodedata
from typing import Dict, Any, List
from django.utils import timezone
from core.models import Propiedad, Plataforma, PalabraClave, BusquedaPalabraClave, ResultadoBusqueda, Busqueda
from core.search_manager import (
    normalizar_texto, procesar_keywords, get_or_create_palabra_clave, 
    procesar_propiedad_existente, verificar_coincidencias_keywords, 
    procesar_propiedad_nueva
)
from .url_builder import build_mercadolibre_url, build_infocasas_url
from .mercadolibre import extraer_total_resultados_mercadolibre, scrape_mercadolibre
from .infocasas import extraer_total_resultados_infocasas, scrape_infocasas
from .extractors import scrape_detalle_con_requests, recolectar_urls_de_pagina, scrape_detalle_infocasas_con_requests, recolectar_urls_infocasas_de_pagina
from .progress import send_progress_update
from .utils import stemming_basico, extraer_variantes_keywords, build_keyword_groups


def buscar_en_contenido_almacenado(prop, keyword_groups, keywords_ya_cubiertas=None):
    """
    Busca keywords en el contenido almacenado de una propiedad.
    Si keywords_ya_cubiertas se proporciona, solo busca las faltantes.
    """
    # Construir texto completo de la propiedad desde los datos almacenados
    titulo = prop.titulo or ''
    descripcion = prop.descripcion or ''
    caracteristicas = ''
    
    # Extraer características del metadata si existe
    if prop.metadata and isinstance(prop.metadata, dict):
        caracteristicas = prop.metadata.get('caracteristicas', '')
    
    texto_total = f"{titulo.lower()} {descripcion.lower()} {caracteristicas.lower()}"
    
    # Verificar coincidencia con keyword_groups
    if not keyword_groups:
        return True
    
    def normalizar(texto):
        return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    texto_total_norm = normalizar(texto_total)
    grupos_ok = []
    
    for grupo in keyword_groups:
        # Si ya tenemos keywords cubiertas, verificar si este grupo ya está cubierto
        if keywords_ya_cubiertas:
            grupo_ya_cubierto = False
            for keyword in grupo:
                keyword_norm = normalizar_texto(str(keyword))
                if keyword_norm in keywords_ya_cubiertas:
                    grupo_ya_cubierto = True
                    break
            if grupo_ya_cubierto:
                grupos_ok.append(True)
                continue
        
        # Buscar en contenido almacenado
        variantes_norm = [normalizar(v) for v in grupo]
        any_match = False
        for v in variantes_norm:
            if v in texto_total_norm:
                any_match = True
                break
            # Busqueda con stemming
            v_stem = stemming_basico(v)
            if v_stem and v_stem in texto_total_norm:
                any_match = True
                break
            # Busqueda parcial para palabras largas
            if len(v) > 4 and v[:-2] in texto_total_norm:
                any_match = True
                break
        grupos_ok.append(any_match)
    
    cumple = all(grupos_ok) if grupos_ok else True
    
    if cumple:
        print(f"✅ [CONTENIDO] Coincide en contenido almacenado: {prop.titulo}")
    else:
        print(f"❌ [CONTENIDO] No coincide en contenido almacenado: {prop.titulo}")
    
    return cumple


def run_scraper(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1, busqueda: 'Busqueda' = None, plataformas: list = None, plataforma: str = None):
    """
    Orquestador principal que maneja múltiples plataformas.
    
    Args:
        filters: Filtros de búsqueda
        keywords: Lista de palabras clave
        max_paginas: Máximo de páginas a procesar por plataforma
        workers_fase1: Workers para fase de recolección
        workers_fase2: Workers para fase de detalle
        busqueda: Objeto Busqueda para guardar resultados
        plataformas: Lista de plataformas ['MercadoLibre', 'InfoCasas', 'Todas']
        plataforma: Plataforma individual ('mercadolibre', 'infocasas', 'todas')
    """
    print(f"🚀 [SCRAPER MULTI] Iniciando búsqueda - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    
    # Determinar plataformas a usar (combinar ambos parámetros)
    if plataforma:
        # Convertir string individual a lista
        if plataforma.lower() in ['todas', 'todas las plataformas']:
            plataformas = ['Todas']
        elif plataforma.lower() == 'mercadolibre':
            plataformas = ['MercadoLibre']
        elif plataforma.lower() == 'infocasas':
            plataformas = ['InfoCasas']
        else:
            plataformas = ['MercadoLibre']  # Default
    
    if not plataformas:
        plataformas = ['MercadoLibre']  # Default
    
    if 'Todas' in plataformas or 'Todas las plataformas' in plataformas:
        plataformas_activas = ['MercadoLibre', 'InfoCasas']
    else:
        plataformas_activas = [p for p in plataformas if p in ['MercadoLibre', 'InfoCasas']]
    
    print(f"🎯 [SCRAPER MULTI] Plataformas activas: {plataformas_activas}")
    
    # Procesar cada plataforma
    resultados_totales = []
    
    for i, plataforma in enumerate(plataformas_activas):
        print(f"\n{'='*60}")
        print(f"🏠 [PLATAFORMA {i+1}/{len(plataformas_activas)}] Procesando {plataforma}")
        print(f"{'='*60}")
        
        send_progress_update(current_search_item=f"Procesando plataforma {plataforma} ({i+1}/{len(plataformas_activas)})...")
        
        try:
            if plataforma == 'MercadoLibre':
                resultados_plataforma = run_scraper_mercadolibre(filters, keywords, max_paginas, workers_fase1, workers_fase2, busqueda)
            elif plataforma == 'InfoCasas':
                resultados_plataforma = run_scraper_infocasas(filters, keywords, max_paginas, workers_fase1, workers_fase2, busqueda)
            else:
                print(f"❌ [SCRAPER MULTI] Plataforma no soportada: {plataforma}")
                continue
            
            if resultados_plataforma:
                # Agregar identificador de plataforma a cada resultado
                for resultado in resultados_plataforma:
                    resultado['plataforma'] = plataforma
                
                resultados_totales.extend(resultados_plataforma)
                print(f"✅ [PLATAFORMA] {plataforma}: {len(resultados_plataforma)} resultados")
            else:
                print(f"❌ [PLATAFORMA] {plataforma}: 0 resultados")
        
        except Exception as e:
            print(f"❌ [PLATAFORMA] Error en {plataforma}: {e}")
            send_progress_update(current_search_item=f"Error en plataforma {plataforma}: {str(e)}")
            continue
    
    # Consolidar resultados finales
    print(f"\n🎯 [SCRAPER MULTI] Consolidando {len(resultados_totales)} resultados de {len(plataformas_activas)} plataformas")
    
    # Eliminar duplicados por URL (aunque es poco probable entre plataformas)
    urls_vistas = set()
    resultados_unicos = []
    
    for resultado in resultados_totales:
        url = resultado.get('url', '')
        if url and url not in urls_vistas:
            urls_vistas.add(url)
            resultados_unicos.append(resultado)
    
    total_final = len(resultados_unicos)
    total_coincidentes = len([r for r in resultados_unicos if r.get('coincide', True)])
    
    print(f"📊 [RESUMEN MULTI] Total final: {total_final} | Coincidentes: {total_coincidentes}")
    
    # Mensaje final
    plataformas_str = ', '.join(plataformas_activas)
    send_progress_update(
        final_message=f"✅ Búsqueda completada en {len(plataformas_activas)} plataforma(s): {plataformas_str}. {total_coincidentes} resultados encontrados.",
        matched_publications=resultados_unicos,
        all_matched_properties={'nuevas': resultados_unicos, 'existentes': []}
    )
    
    return resultados_unicos


def run_scraper_mercadolibre(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1, busqueda: 'Busqueda' = None):
    """
    Función específica de scraping para MercadoLibre (función original renombrada).
    """
    print(f"🚀 [SCRAPER] Iniciando búsqueda - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    matched_publications_titles: List[dict] = []

    keywords_filtradas = procesar_keywords(' '.join(keywords)) if keywords else []
    keyword_groups = build_keyword_groups(keywords_filtradas)
    keywords_con_variantes = extraer_variantes_keywords(keywords_filtradas)
    print(f"🔍 [SCRAPER] Keywords filtradas: {keywords_filtradas}")

    USE_THREADS = False
    API_KEY = None
    if USE_THREADS:
        API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
        if not API_KEY:
            print("❌ ERROR: SCRAPINGBEE_API_KEY no definida pero USE_THREADS=True.")
            send_progress_update(final_message="❌ Error: API key no configurada")
            return
        print("🔧 [CONFIG] Modo concurrente activado - usando ScrapingBee")
    else:
        print("🔧 [CONFIG] Modo secuencial activado - usando requests directo")

    cant_propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    urls_a_visitar_final = set()
    titulos_por_url_total = {}

    try:
        url_base_con_filtros = build_mercadolibre_url(filters)
        if url_base_con_filtros.endswith('_NoIndex_True') and 'inmuebles/_NoIndex_True' in url_base_con_filtros:
            print("⚠️ [URL BUILD] URL generada es demasiado genérica, puede indicar problema en filtros")
        send_progress_update(current_search_item=f"🏠 URL generada con filtros: {url_base_con_filtros[:100]}{'...' if len(url_base_con_filtros) > 100 else ''}")
    except Exception as e:
        print(f"❌ [URL BUILD] Error construyendo URL: {e}")
        send_progress_update(final_message=f"❌ Error construyendo URL: {e}")
        return

    send_progress_update(current_search_item="🔍 Extrayendo total de resultados de MercadoLibre...")
    total_ml = extraer_total_resultados_mercadolibre(
        url_base_con_filtros,
        api_key=API_KEY,
        use_scrapingbee=USE_THREADS and bool(API_KEY)
    )
    if total_ml:
        print(f"[Principal] Total de publicaciones en MercadoLibre: {total_ml:,}")
        send_progress_update(total_found=total_ml, current_search_item=f"📊 Total de publicaciones encontradas: {total_ml:,}")
    else:
        print("[Principal] No se pudo extraer el total de MercadoLibre")
        send_progress_update(current_search_item="❌ No se pudo obtener el total de resultados")

    if total_ml:
        paginas_a_buscar = min(max_paginas, (total_ml // 48) + (1 if total_ml % 48 else 0))
    else:
        paginas_a_buscar = max_paginas
    paginas_de_resultados = []
    for i in range(paginas_a_buscar):
        if i == 0:
            page_url = url_base_con_filtros
        else:
            desde = 1 + (i * 48)
            page_url = f"{url_base_con_filtros}_Desde_{desde}"
        paginas_de_resultados.append(page_url)

    modo = 'concurrencia (ScrapingBee)' if USE_THREADS else 'secuencial (requests)'
    print(f"\n--- FASE 1: Se intentarán recolectar {len(paginas_de_resultados)} páginas (modo: {modo}, workers: {workers_fase1 if USE_THREADS else 1}) ---")
    send_progress_update(current_search_item=f"FASE 1: Recolectando URLs de {len(paginas_de_resultados)} páginas ({modo})...")
    urls_recolectadas_bruto = set()
    ubicacion_param = filters.get('ciudad', filters.get('departamento', 'montevideo'))
    if USE_THREADS:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase1) as executor:
            mapa_futuros = {executor.submit(recolectar_urls_de_pagina, url, API_KEY, ubicacion_param, True): url for url in paginas_de_resultados}
            for futuro in concurrent.futures.as_completed(mapa_futuros):
                urls_nuevas, titulos_map = futuro.result()
                urls_recolectadas_bruto.update(urls_nuevas)
                # Merge títulos por URL
                if isinstance(titulos_map, dict):
                    titulos_por_url_total.update({u: t for u, t in titulos_map.items() if u not in titulos_por_url_total})
    else:
        for url in paginas_de_resultados:
            urls_nuevas, titulos_map = recolectar_urls_de_pagina(url, API_KEY, ubicacion_param, False)
            urls_recolectadas_bruto.update(urls_nuevas)
            if isinstance(titulos_map, dict):
                titulos_por_url_total.update({u: t for u, t in titulos_map.items() if u not in titulos_por_url_total})

    print(f"\n[Principal] FASE 1 Recolección Bruta Finalizada. Se obtuvieron {len(urls_recolectadas_bruto)} URLs en total.")
    send_progress_update(current_search_item=f"FASE 1 completada. Se encontraron {len(urls_recolectadas_bruto)} URLs de publicaciones.")

    print("\n[Principal] Iniciando chequeo de duplicados contra la base de datos...")
    send_progress_update(current_search_item="Chequeando publicaciones existentes en la base de datos...")
    existing_publications_titles = []

    if urls_recolectadas_bruto:
        # URLs que ya existen en la BD
        urls_existentes = set(Propiedad.objects.filter(url__in=list(urls_recolectadas_bruto)).values_list('url', flat=True))
        cant_propiedades_omitidas = len(urls_existentes)

        # Inicialmente, visitaremos las URLs que no están en la BD
        urls_a_visitar_final = set(urls_recolectadas_bruto) - set(urls_existentes)

        # Si hay URLs existentes y keywords, usar el nuevo sistema de verificación
        if urls_existentes and keywords_con_variantes:
            print(f"🔍 [NUEVO SISTEMA] Procesando {len(urls_existentes)} propiedades existentes con nuevo sistema keywords")
            
            # Procesar keywords de la búsqueda actual
            keywords_procesadas = procesar_keywords(' '.join(keywords_con_variantes))
            palabras_clave_busqueda = []
            
            for keyword_data in keywords_procesadas:
                palabra_clave = get_or_create_palabra_clave(keyword_data['texto'])
                palabras_clave_busqueda.append(palabra_clave)
            
            # Cargar propiedades existentes
            existing_properties_qs = Propiedad.objects.filter(url__in=urls_existentes)
            
            # Procesar cada propiedad existente
            for prop in existing_properties_qs:
                try:
                    # Usar el nuevo sistema para verificar keywords
                    resultados_keywords = procesar_propiedad_existente(prop, palabras_clave_busqueda)
                    
                    # Verificar si todas las keywords coinciden
                    todas_encontradas = all(resultados_keywords.values())
                    
                    # Agregar todas las propiedades existentes con su estado de coincidencia
                    existing_publications_titles.append({
                        'title': prop.titulo or 'Sin título',
                        'url': prop.url,
                        'coincide': todas_encontradas
                    })
                    
                    # Crear ResultadoBusqueda si se proporciona la búsqueda
                    if busqueda:
                        from core.search_manager import guardar_resultado_busqueda_con_keywords
                        # Usar función que evalúa automáticamente las keywords
                        guardar_resultado_busqueda_con_keywords(busqueda, prop)
                    
                    if todas_encontradas:
                        print(f"✅ [NUEVO SISTEMA] Coincide: {prop.titulo or prop.url}")
                    else:
                        print(f"❌ [NUEVO SISTEMA] No coincide: {prop.titulo or prop.url}")
                        
                except Exception as e:
                    print(f"❌ [ERROR NUEVO SISTEMA] Error procesando {prop.url}: {str(e)}")
                    # Fallback al sistema anterior
                    coincide_propiedad = buscar_en_contenido_almacenado(prop, keyword_groups)
                    existing_publications_titles.append({
                        'title': prop.titulo or 'Sin título',
                        'url': prop.url,
                        'coincide': coincide_propiedad
                    })
                    
                    # Crear ResultadoBusqueda si se proporciona la búsqueda
                    if busqueda:
                        from core.search_manager import guardar_resultado_busqueda_con_keywords
                        # Crear manualmente con el resultado del fallback
                        resultado, created = ResultadoBusqueda.objects.update_or_create(
                            busqueda=busqueda,
                            propiedad=prop,
                            defaults={
                                'coincide': coincide_propiedad,
                                'last_seen_at': timezone.now(),
                            }
                        )

        # URLs que no están en la BD son candidatas para scraping (mantener solo URLs nuevas)
        urls_a_visitar_final = set(urls_recolectadas_bruto) - set(urls_existentes)

        # NOTE: no se contempla el caso "urls_existentes y NO keywords_con_variantes" según la especificación

        # Logs internos y mensaje de estado simplificado para el usuario
        print(f"🆕  [DEDUP] URLs nuevas a procesar: {len(urls_a_visitar_final)}")
        print(f"🗃️  [DEDUP] Coincidentes existentes tras análisis: {len(existing_publications_titles)}")
        # Para el usuario, solo informar cuántas existentes hay
        send_progress_update(current_search_item=f"🗃️ {cant_propiedades_omitidas} URLs existentes analizadas en la base de datos")
    else:
        print("❌ [RECOLECCIÓN] No se obtuvieron URLs")
        send_progress_update(current_search_item="No se encontraron URLs para procesar.")

    # Atajo: si NO hay keywords, no necesitamos FASE 2 (no hay nada que validar en detalle).
    # Devolvemos directamente los links recolectados en FASE 1 como "resultados encontrados".
    if not keywords_con_variantes:
        print("\n⏭️  [ATAJO] Sin keywords: omitiendo FASE 2 y devolviendo enlaces de FASE 1")
        send_progress_update(current_search_item="Sin keywords: devolviendo enlaces de FASE 1 (sin scrapeo de detalle)")

        # Usar todas las URLs recolectadas (incluye existentes y nuevas) como resultados a mostrar/guardar
        resultados_fase1 = [
            {
                'title': titulos_por_url_total.get(u) or 'Publicación',
                'url': u,
                'coincide': True  # Sin keywords, todas coinciden
            }
            for u in sorted(list(urls_recolectadas_bruto))
        ]
        matched_publications_titles = list(resultados_fase1)
        
        # Crear ResultadoBusqueda para todas las URLs si se proporciona búsqueda
        if busqueda:
            for url in urls_recolectadas_bruto:
                # Buscar o crear la propiedad
                propiedad, created = Propiedad.objects.get_or_create(
                    url=url,
                    defaults={
                        'plataforma': Plataforma.objects.get_or_create(nombre='MercadoLibre')[0],
                        'titulo': titulos_por_url_total.get(url) or 'Publicación',
                        'descripcion': '',
                        'metadata': {}
                    }
                )
                
                # Crear ResultadoBusqueda (sin keywords, todas coinciden)
                resultado_busqueda, created = ResultadoBusqueda.objects.update_or_create(
                    busqueda=busqueda,
                    propiedad=propiedad,
                    defaults={
                        'coincide': True,  # Sin keywords, todas coinciden
                        'last_seen_at': timezone.now(),
                    }
                )

        # Para la UI actual: mostrar todo bajo 'nuevas' y no poblar 'existentes'
        all_matched_properties = {
            'nuevas': matched_publications_titles,
            'existentes': []
        }
        total_coincidentes = len(matched_publications_titles)
        print(f"📊 [RESUMEN FINAL] (UI) Nuevas: {total_coincidentes} | Existentes (solo log): 0 | Total: {total_coincidentes}")
        send_progress_update(
            final_message=f"✅ Búsqueda completada (sin keywords). {nuevas_propiedades_guardadas} nuevas propiedades guardadas.",
            matched_publications=matched_publications_titles,
            all_matched_properties=all_matched_properties
        )
        # Retornar lista simple de resultados para flujos sin WebSocket (HTTP fallback/tests)
        return matched_publications_titles

    if urls_a_visitar_final:
        print(f"\n--- FASE 2: Procesamiento de propiedades nuevas con sistema keywords ({len(urls_a_visitar_final)} URLs)... ---")
        send_progress_update(current_search_item=f"FASE 2: Procesando {len(urls_a_visitar_final)} publicaciones nuevas...")
        
        # Obtener plataforma MercadoLibre
        try:
            plataforma_ml = Plataforma.objects.get(nombre='MercadoLibre')
        except Plataforma.DoesNotExist:
            plataforma_ml = Plataforma.objects.create(
                nombre='MercadoLibre',
                url='https://www.mercadolibre.com.uy'
            )
        
        # Procesar keywords de la búsqueda actual
        if keywords_con_variantes:
            keywords_procesadas = procesar_keywords(' '.join(keywords_con_variantes))
            palabras_clave_busqueda = []
            
            for keyword_data in keywords_procesadas:
                palabra_clave = get_or_create_palabra_clave(keyword_data['texto'])
                palabras_clave_busqueda.append(palabra_clave)
        else:
            palabras_clave_busqueda = []
        
        urls_lista = list(urls_a_visitar_final)
        
        # Procesar con ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            
            def procesar_propiedad_wrapper(url):
                """Wrapper para procesar cada URL con el nuevo sistema"""
                try:
                    if palabras_clave_busqueda:
                        # Usar el nuevo sistema para propiedades con keywords
                        propiedad, resultados_keywords = procesar_propiedad_nueva(
                            url, plataforma_ml, palabras_clave_busqueda
                        )
                        
                        # Verificar si todas las keywords coinciden
                        todas_encontradas = all(resultados_keywords.values())
                        
                        return {
                            'success': True,
                            'propiedad': propiedad,
                            'coincide': todas_encontradas,
                            'resultados_keywords': resultados_keywords
                        }
                    else:
                        # Sin keywords, usar el sistema original de scraping
                        datos_propiedad = scrape_detalle_con_requests(url, None, False)
                        
                        if datos_propiedad:
                            # Crear propiedad directamente
                            propiedad = Propiedad.objects.create(
                                url=url,
                                plataforma=plataforma_ml,
                                titulo=datos_propiedad.get('titulo', ''),
                                descripcion=datos_propiedad.get('descripcion', ''),
                                metadata=datos_propiedad.get('caracteristicas', {})
                            )
                            
                            return {
                                'success': True,
                                'propiedad': propiedad,
                                'coincide': True,  # Sin keywords, siempre coincide
                                'resultados_keywords': {}
                            }
                        else:
                            return {'success': False, 'error': 'No se pudieron obtener datos'}
                            
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Enviar tareas al pool
            mapa_futuros = {executor.submit(procesar_propiedad_wrapper, url): url for url in urls_lista}
            
            # Procesar resultados
            for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros)):
                url_original = mapa_futuros[futuro]
                
                try:
                    resultado = futuro.result()
                    
                    if resultado['success']:
                        propiedad = resultado['propiedad']
                        coincide = resultado['coincide']
                        
                        titulo_propiedad = propiedad.titulo or 'Sin título'
                        
                        # Guardar TODAS las propiedades (coincidentes y no coincidentes)
                        nuevas_propiedades_guardadas += 1
                        matched_publications_titles.append({
                            'title': titulo_propiedad,
                            'url': propiedad.url,
                            'coincide': coincide
                        })
                        
                        # Crear ResultadoBusqueda si se proporciona la búsqueda
                        if busqueda:
                            resultado_busqueda, created = ResultadoBusqueda.objects.update_or_create(
                                busqueda=busqueda,
                                propiedad=propiedad,
                                defaults={
                                    'coincide': coincide,
                                    'last_seen_at': timezone.now(),
                                }
                            )
                        
                        if coincide:
                            print(f"✅ [NUEVO SISTEMA] ({i+1}/{len(urls_lista)}) Coincide: {titulo_propiedad}")
                            send_progress_update(
                                current_search_item=f"({i+1}/{len(urls_lista)}) ✅ Coincide: {titulo_propiedad}",
                                matched_publications=matched_publications_titles
                            )
                        else:
                            print(f"❌ [NUEVO SISTEMA] ({i+1}/{len(urls_lista)}) No coincide: {titulo_propiedad}")
                            send_progress_update(
                                current_search_item=f"({i+1}/{len(urls_lista)}) ❌ No coincide: {titulo_propiedad}"
                            )
                    else:
                        print(f"⚠️ [ERROR] ({i+1}/{len(urls_lista)}) Error procesando {url_original}: {resultado['error']}")
                        send_progress_update(
                            current_search_item=f"({i+1}/{len(urls_lista)}) ⚠️ Error procesando URL"
                        )
                        
                except Exception as exc:
                    print(f'❌ [EXCEPCIÓN] URL {url_original[:100]}... generó excepción: {exc}')
                    send_progress_update(
                        current_search_item=f"({i+1}/{len(urls_lista)}) ❌ Excepción procesando URL"
                    )
    print(f"✅ [COMPLETADO] {nuevas_propiedades_guardadas} nuevas propiedades guardadas")
    
    # Filtrar solo las propiedades que coinciden (coincide: True) para mostrar en la UI
    matched_only_new = [p for p in matched_publications_titles if p.get('coincide', True)]
    matched_only_existing = [p for p in existing_publications_titles if p.get('coincide', True)]
    
    # Para la UI actual: mostrar solo coincidentes bajo 'nuevas' y no poblar 'existentes'
    combined_for_ui = matched_only_new + matched_only_existing
    all_matched_properties = {
        'nuevas': combined_for_ui,
        'existentes': []
    }
    total_coincidentes = len(combined_for_ui)
    total_procesadas = len(matched_publications_titles) + len(existing_publications_titles)
    print(f"📊 [RESUMEN FINAL] (UI) Coincidentes: {total_coincidentes} de {total_procesadas} procesadas | Nuevas: {len(matched_only_new)} | Existentes: {len(matched_only_existing)}")
    send_progress_update(
        final_message=f"✅ Búsqueda completada. {nuevas_propiedades_guardadas} nuevas propiedades guardadas, {total_coincidentes} coincidentes mostradas.",
        matched_publications=combined_for_ui,
        all_matched_properties=all_matched_properties
    )
    # Retornar lista simple de resultados para flujos sin WebSocket (HTTP fallback/tests)
    return combined_for_ui


def run_scraper_infocasas(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1, busqueda: 'Busqueda' = None):
    """
    Función específica de scraping para InfoCasas.
    Adaptada del patrón de MercadoLibre pero con las especificidades de InfoCasas.
    """
    print(f"🏠 [INFOCASAS] Iniciando scraping - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    matched_publications_titles: List[dict] = []

    keywords_filtradas = procesar_keywords(' '.join(keywords)) if keywords else []
    keyword_groups = build_keyword_groups(keywords_filtradas)
    keywords_con_variantes = extraer_variantes_keywords(keywords_filtradas)
    print(f"🔍 [INFOCASAS] Keywords filtradas: {keywords_filtradas}")

    USE_THREADS = False
    API_KEY = None
    if USE_THREADS:
        API_KEY = os.getenv('SCRAPINGBEE_API_KEY')
        if not API_KEY:
            print("❌ ERROR: SCRAPINGBEE_API_KEY no definida pero USE_THREADS=True.")
            send_progress_update(final_message="❌ Error: API key no configurada")
            return []
        print("🔧 [CONFIG IC] Modo concurrente activado - usando ScrapingBee")
    else:
        print("🔧 [CONFIG IC] Modo secuencial activado - usando requests directo")

    cant_propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    urls_a_visitar_final = set()
    titulos_por_url_total = {}

    try:
        # Construir URL específica de InfoCasas
        url_base_con_filtros = build_infocasas_url(filters)
        send_progress_update(current_search_item=f"🏠 URL InfoCasas generada: {url_base_con_filtros[:100]}{'...' if len(url_base_con_filtros) > 100 else ''}")
    except Exception as e:
        print(f"❌ [URL BUILD IC] Error construyendo URL: {e}")
        send_progress_update(final_message=f"❌ Error construyendo URL InfoCasas: {e}")
        return []

    send_progress_update(current_search_item="🔍 Extrayendo total de resultados de InfoCasas...")
    total_ic = extraer_total_resultados_infocasas(
        url_base_con_filtros,
        api_key=API_KEY,
        use_scrapingbee=USE_THREADS and bool(API_KEY)
    )
    
    if total_ic:
        print(f"[InfoCasas] Total de publicaciones: {total_ic}")
        send_progress_update(total_found=total_ic, current_search_item=f"📊 Total InfoCasas encontradas: {total_ic}")
    else:
        print("[InfoCasas] No se pudo extraer el total")
        send_progress_update(current_search_item="❌ No se pudo obtener el total de InfoCasas")

    # Definir páginas a procesar (InfoCasas usa numeración de páginas)
    if isinstance(total_ic, int) and total_ic > 0:
        # Estimar páginas basado en aprox 20-30 resultados por página
        paginas_a_buscar = min(max_paginas, (total_ic // 25) + (1 if total_ic % 25 else 0))
    else:
        paginas_a_buscar = max_paginas
    
    paginas_de_resultados = []
    for i in range(paginas_a_buscar):
        if i == 0:
            page_url = url_base_con_filtros
        else:
            # InfoCasas usa parámetro 'pagina'
            separator = '&' if '?' in url_base_con_filtros else '?'
            page_url = f"{url_base_con_filtros}{separator}pagina={i + 1}"
        paginas_de_resultados.append(page_url)

    modo = 'concurrencia (ScrapingBee)' if USE_THREADS else 'secuencial (requests)'
    print(f"\n--- FASE 1 IC: Recolectando {len(paginas_de_resultados)} páginas ({modo}) ---")
    send_progress_update(current_search_item=f"FASE 1 IC: Recolectando URLs de {len(paginas_de_resultados)} páginas...")
    
    urls_recolectadas_bruto = set()
    
    if USE_THREADS:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase1) as executor:
            mapa_futuros = {
                executor.submit(recolectar_urls_infocasas_de_pagina, url, API_KEY, True): url 
                for url in paginas_de_resultados
            }
            for futuro in concurrent.futures.as_completed(mapa_futuros):
                urls_nuevas, titulos_map = futuro.result()
                urls_recolectadas_bruto.update(urls_nuevas)
                if isinstance(titulos_map, dict):
                    titulos_por_url_total.update({u: t for u, t in titulos_map.items() if u not in titulos_por_url_total})
    else:
        for url in paginas_de_resultados:
            urls_nuevas, titulos_map = recolectar_urls_infocasas_de_pagina(url, API_KEY, False)
            urls_recolectadas_bruto.update(urls_nuevas)
            if isinstance(titulos_map, dict):
                titulos_por_url_total.update({u: t for u, t in titulos_map.items() if u not in titulos_por_url_total})

    print(f"\n[InfoCasas] FASE 1 Finalizada. Se obtuvieron {len(urls_recolectadas_bruto)} URLs.")
    send_progress_update(current_search_item=f"FASE 1 IC completada. {len(urls_recolectadas_bruto)} URLs encontradas.")

    print("\n[InfoCasas] Verificando duplicados en base de datos...")
    send_progress_update(current_search_item="Verificando URLs de InfoCasas en base de datos...")
    
    existing_publications_titles = []

    if urls_recolectadas_bruto:
        # URLs que ya existen en la BD (específicamente de InfoCasas)
        try:
            plataforma_ic = Plataforma.objects.get(nombre='InfoCasas')
            urls_existentes = set(
                Propiedad.objects.filter(
                    url__in=list(urls_recolectadas_bruto),
                    plataforma=plataforma_ic
                ).values_list('url', flat=True)
            )
        except Plataforma.DoesNotExist:
            urls_existentes = set()
        
        cant_propiedades_omitidas = len(urls_existentes)
        urls_a_visitar_final = set(urls_recolectadas_bruto) - set(urls_existentes)

        # Procesar propiedades existentes si hay keywords
        if urls_existentes and keywords_con_variantes:
            print(f"🔍 [IC EXISTENTES] Procesando {len(urls_existentes)} propiedades existentes")
            
            keywords_procesadas = procesar_keywords(' '.join(keywords_con_variantes))
            palabras_clave_busqueda = []
            
            for keyword_data in keywords_procesadas:
                palabra_clave = get_or_create_palabra_clave(keyword_data['texto'])
                palabras_clave_busqueda.append(palabra_clave)
            
            existing_properties_qs = Propiedad.objects.filter(
                url__in=urls_existentes,
                plataforma=plataforma_ic
            )
            
            for prop in existing_properties_qs:
                try:
                    resultados_keywords = procesar_propiedad_existente(prop, palabras_clave_busqueda)
                    todas_encontradas = all(resultados_keywords.values())
                    
                    existing_publications_titles.append({
                        'title': prop.titulo or 'Sin título',
                        'url': prop.url,
                        'coincide': todas_encontradas
                    })
                    
                    if busqueda:
                        from core.search_manager import guardar_resultado_busqueda_con_keywords
                        guardar_resultado_busqueda_con_keywords(busqueda, prop)
                    
                    if todas_encontradas:
                        print(f"✅ [IC EXISTENTE] Coincide: {prop.titulo or prop.url}")
                    else:
                        print(f"❌ [IC EXISTENTE] No coincide: {prop.titulo or prop.url}")
                        
                except Exception as e:
                    print(f"❌ [ERROR IC] Error procesando {prop.url}: {str(e)}")
                    # Fallback
                    coincide_propiedad = buscar_en_contenido_almacenado(prop, keyword_groups)
                    existing_publications_titles.append({
                        'title': prop.titulo or 'Sin título',
                        'url': prop.url,
                        'coincide': coincide_propiedad
                    })
                    
                    if busqueda:
                        resultado, created = ResultadoBusqueda.objects.update_or_create(
                            busqueda=busqueda,
                            propiedad=prop,
                            defaults={
                                'coincide': coincide_propiedad,
                                'last_seen_at': timezone.now(),
                            }
                        )

        print(f"🆕 [IC DEDUP] URLs nuevas a procesar: {len(urls_a_visitar_final)}")
        print(f"🗃️ [IC DEDUP] URLs existentes analizadas: {len(existing_publications_titles)}")
        send_progress_update(current_search_item=f"🗃️ {cant_propiedades_omitidas} URLs InfoCasas existentes analizadas")
    
    else:
        print("❌ [IC RECOLECCIÓN] No se obtuvieron URLs")
        send_progress_update(current_search_item="No se encontraron URLs de InfoCasas")

    # Si no hay keywords, devolver directamente los enlaces
    if not keywords_con_variantes:
        print("\n⏭️ [IC ATAJO] Sin keywords: devolviendo enlaces de FASE 1")
        send_progress_update(current_search_item="IC sin keywords: devolviendo enlaces directamente")

        resultados_fase1 = [
            {
                'title': titulos_por_url_total.get(u) or 'Publicación InfoCasas',
                'url': u,
                'coincide': True
            }
            for u in sorted(list(urls_recolectadas_bruto))
        ]
        matched_publications_titles = list(resultados_fase1)
        
        # Crear propiedades básicas si se proporciona búsqueda
        if busqueda:
            try:
                plataforma_ic = Plataforma.objects.get(nombre='InfoCasas')
            except Plataforma.DoesNotExist:
                plataforma_ic = Plataforma.objects.create(
                    nombre='InfoCasas',
                    url='https://www.infocasas.com.uy'
                )
            
            for url in urls_recolectadas_bruto:
                propiedad, created = Propiedad.objects.get_or_create(
                    url=url,
                    defaults={
                        'plataforma': plataforma_ic,
                        'titulo': titulos_por_url_total.get(url) or 'Publicación InfoCasas',
                        'descripcion': '',
                        'metadata': {}
                    }
                )
                
                resultado_busqueda, created = ResultadoBusqueda.objects.update_or_create(
                    busqueda=busqueda,
                    propiedad=propiedad,
                    defaults={
                        'coincide': True,
                        'last_seen_at': timezone.now(),
                    }
                )

        print(f"📊 [IC RESUMEN] URLs finales: {len(matched_publications_titles)}")
        return matched_publications_titles

    # FASE 2: Procesar propiedades nuevas con keywords
    if urls_a_visitar_final:
        print(f"\n--- FASE 2 IC: Procesando {len(urls_a_visitar_final)} propiedades nuevas ---")
        send_progress_update(current_search_item=f"FASE 2 IC: Procesando {len(urls_a_visitar_final)} publicaciones...")
        
        # Obtener plataforma InfoCasas
        try:
            plataforma_ic = Plataforma.objects.get(nombre='InfoCasas')
        except Plataforma.DoesNotExist:
            plataforma_ic = Plataforma.objects.create(
                nombre='InfoCasas',
                url='https://www.infocasas.com.uy'
            )
        
        # Procesar keywords
        if keywords_con_variantes:
            keywords_procesadas = procesar_keywords(' '.join(keywords_con_variantes))
            palabras_clave_busqueda = []
            
            for keyword_data in keywords_procesadas:
                palabra_clave = get_or_create_palabra_clave(keyword_data['texto'])
                palabras_clave_busqueda.append(palabra_clave)
        else:
            palabras_clave_busqueda = []
        
        urls_lista = list(urls_a_visitar_final)
        
        # Procesar con ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            
            def procesar_propiedad_ic_wrapper(url):
                """Wrapper para procesar cada URL de InfoCasas"""
                try:
                    # Extraer datos de la propiedad
                    datos_propiedad = scrape_detalle_infocasas_con_requests(url, API_KEY, USE_THREADS and bool(API_KEY))
                    
                    if not datos_propiedad:
                        return {'success': False, 'error': 'No se pudieron extraer datos'}
                    
                    # Crear propiedad
                    propiedad = Propiedad(
                        url=url,
                        plataforma=plataforma_ic,
                        titulo=datos_propiedad.get('titulo', ''),
                        descripcion=datos_propiedad.get('descripcion', ''),
                        precio=datos_propiedad.get('precio_valor', 0),
                        moneda=datos_propiedad.get('precio_moneda', ''),
                        metadata=datos_propiedad
                    )
                    propiedad.save()
                    
                    # Procesar con sistema de keywords
                    if palabras_clave_busqueda:
                        resultado_keywords = procesar_propiedad_nueva(propiedad, palabras_clave_busqueda)
                        coincide = resultado_keywords.get('coincide_todas', True)
                    else:
                        coincide = True
                    
                    return {
                        'success': True,
                        'propiedad': propiedad,
                        'coincide': coincide
                    }
                
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Ejecutar procesamiento
            futuros = {executor.submit(procesar_propiedad_ic_wrapper, url): url for url in urls_lista}
            
            for i, futuro in enumerate(concurrent.futures.as_completed(futuros)):
                url_original = futuros[futuro]
                
                try:
                    resultado = futuro.result()
                    
                    if resultado['success']:
                        propiedad = resultado['propiedad']
                        coincide = resultado['coincide']
                        
                        titulo_propiedad = propiedad.titulo or 'Sin título'
                        nuevas_propiedades_guardadas += 1
                        
                        matched_publications_titles.append({
                            'title': titulo_propiedad,
                            'url': propiedad.url,
                            'coincide': coincide
                        })
                        
                        # Crear ResultadoBusqueda
                        if busqueda:
                            resultado_busqueda, created = ResultadoBusqueda.objects.update_or_create(
                                busqueda=busqueda,
                                propiedad=propiedad,
                                defaults={
                                    'coincide': coincide,
                                    'last_seen_at': timezone.now(),
                                }
                            )
                        
                        if coincide:
                            print(f"✅ [IC NUEVO] ({i+1}/{len(urls_lista)}) Coincide: {titulo_propiedad}")
                            send_progress_update(
                                current_search_item=f"IC ({i+1}/{len(urls_lista)}) ✅ Coincide: {titulo_propiedad}",
                                matched_publications=matched_publications_titles
                            )
                        else:
                            print(f"❌ [IC NUEVO] ({i+1}/{len(urls_lista)}) No coincide: {titulo_propiedad}")
                            send_progress_update(
                                current_search_item=f"IC ({i+1}/{len(urls_lista)}) ❌ No coincide: {titulo_propiedad}"
                            )
                    else:
                        print(f"⚠️ [IC ERROR] ({i+1}/{len(urls_lista)}) Error: {resultado['error']}")
                        send_progress_update(
                            current_search_item=f"IC ({i+1}/{len(urls_lista)}) ⚠️ Error procesando URL"
                        )
                        
                except Exception as exc:
                    print(f'❌ [IC EXCEPCIÓN] URL {url_original[:100]}... error: {exc}')
                    send_progress_update(
                        current_search_item=f"IC ({i+1}/{len(urls_lista)}) ❌ Excepción"
                    )

    print(f"✅ [IC COMPLETADO] {nuevas_propiedades_guardadas} nuevas propiedades guardadas")
    
    # Filtrar y consolidar resultados
    matched_only_new = [p for p in matched_publications_titles if p.get('coincide', True)]
    matched_only_existing = [p for p in existing_publications_titles if p.get('coincide', True)]
    
    combined_for_ui = matched_only_new + matched_only_existing
    total_coincidentes = len(combined_for_ui)
    total_procesadas = len(matched_publications_titles) + len(existing_publications_titles)
    
    print(f"📊 [IC RESUMEN FINAL] Coincidentes: {total_coincidentes} de {total_procesadas} | Nuevas: {len(matched_only_new)} | Existentes: {len(matched_only_existing)}")
    
    return combined_for_ui
