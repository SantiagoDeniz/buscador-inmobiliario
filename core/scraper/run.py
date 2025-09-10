import concurrent.futures
import os
import unicodedata
from typing import Dict, Any, List
from core.models import Propiedad, Plataforma, PalabraClave, BusquedaPalabraClave, ResultadoBusqueda, Busqueda
from .url_builder import build_mercadolibre_url
from .mercadolibre import extraer_total_resultados_mercadolibre
from .extractors import scrape_detalle_con_requests, recolectar_urls_de_pagina
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
                from core.search_manager import normalizar_texto
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


def run_scraper(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1):
    print(f"🚀 [SCRAPER] Iniciando búsqueda - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    matched_publications_titles: List[dict] = []

    from core.search_manager import procesar_keywords
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

        # Si hay URLs existentes y keywords (con variantes), analizar coincidencias
        if urls_existentes and keywords_con_variantes:
            # Cargar propiedades existentes
            existing_properties_qs = Propiedad.objects.filter(url__in=urls_existentes)
            print(f"🔍 [ANALISIS BD] Analizando {existing_properties_qs.count()} propiedades existentes para keywords: {keywords_con_variantes}")

            # Normalizar variantes y buscar PalabraClave que coincidan (texto o sinónimos)
            from core.search_manager import normalizar_texto
            variantes_norm = [normalizar_texto(str(v)) for v in keywords_con_variantes]

            # Recolectar PalabraClave que tengan texto o algún sinónimo en las variantes
            matching_palabras = []
            for pk in PalabraClave.objects.all():
                texto_norm = normalizar_texto(pk.texto)
                if texto_norm in variantes_norm:
                    matching_palabras.append(pk)
                    continue
                for s in pk.sinonimos_list:
                    if normalizar_texto(str(s)) in variantes_norm:
                        matching_palabras.append(pk)
                        break

            if matching_palabras:
                palabra_ids = [p.id for p in matching_palabras]
                # Buscar búsquedas relacionadas a esas palabras clave
                busqueda_ids = list(BusquedaPalabraClave.objects.filter(palabra_clave_id__in=palabra_ids).values_list('busqueda_id', flat=True))
            else:
                busqueda_ids = []

            # Analizar cada propiedad individualmente
            for prop in existing_properties_qs:
                coincide_propiedad = False
                
                if busqueda_ids:
                    # Verificar si esta propiedad tiene resultados relacionados con las búsquedas de keywords coincidentes
                    resultados_relacionados = ResultadoBusqueda.objects.filter(
                        busqueda_id__in=busqueda_ids, 
                        propiedad=prop
                    ).select_related('busqueda')
                    
                    if resultados_relacionados.exists():
                        # Verificar si todas las unidades de keywords están cubiertas por las búsquedas relacionadas
                        keywords_cubiertas = set()
                        for resultado in resultados_relacionados:
                            # Obtener keywords de la búsqueda relacionada
                            busqueda_keywords = BusquedaPalabraClave.objects.filter(
                                busqueda=resultado.busqueda
                            ).select_related('palabra_clave')
                            
                            for bpk in busqueda_keywords:
                                pk = bpk.palabra_clave
                                # Verificar si esta palabra clave coincide con nuestras keywords actuales
                                texto_norm = normalizar_texto(pk.texto)
                                if texto_norm in variantes_norm:
                                    keywords_cubiertas.add(texto_norm)
                                for s in pk.sinonimos_list:
                                    if normalizar_texto(str(s)) in variantes_norm:
                                        keywords_cubiertas.add(normalizar_texto(str(s)))
                        
                        # Verificar si todas las keyword_groups están cubiertas
                        grupos_cubiertos = 0
                        if keyword_groups:
                            for grupo in keyword_groups:
                                grupo_cubierto = False
                                for keyword in grupo:
                                    keyword_norm = normalizar_texto(str(keyword))
                                    if keyword_norm in keywords_cubiertas:
                                        grupo_cubierto = True
                                        break
                                if grupo_cubierto:
                                    grupos_cubiertos += 1
                        
                        # Si todas las unidades están cubiertas, coincide
                        if grupos_cubiertos == len(keyword_groups):
                            coincide_propiedad = True
                            print(f"✅ [BD RELACION] Coincide por búsquedas relacionadas: {prop.titulo}")
                        else:
                            # Hay coincidencia parcial, buscar keywords faltantes en contenido almacenado
                            print(f"🔍 [PARCIAL] Coincidencia parcial ({grupos_cubiertos}/{len(keyword_groups)}) para: {prop.titulo}")
                            coincide_contenido = buscar_en_contenido_almacenado(prop, keyword_groups, keywords_cubiertas)
                            coincide_propiedad = coincide_contenido
                    else:
                        # No hay relación en BD, buscar en contenido almacenado
                        print(f"🔍 [SIN RELACION] Sin relación en BD para: {prop.titulo}")
                        coincide_propiedad = buscar_en_contenido_almacenado(prop, keyword_groups)
                else:
                    # No hay búsquedas relacionadas a las keywords, buscar en contenido almacenado
                    print(f"🔍 [SIN BUSQUEDAS] Sin búsquedas relacionadas para: {prop.titulo}")
                    coincide_propiedad = buscar_en_contenido_almacenado(prop, keyword_groups)
                
                # Agregar resultado según coincidencia
                if coincide_propiedad:
                    existing_publications_titles.append({
                        'title': prop.titulo or 'Sin título',
                        'url': prop.url
                    })
                
                # Nota: No agregamos a urls_a_visitar_final porque nunca re-scrapeamos URLs existentes

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
                'url': u
            }
            for u in sorted(list(urls_recolectadas_bruto))
        ]
        matched_publications_titles = list(resultados_fase1)

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
        print(f"\n--- FASE 2: Scrapeo de detalles en paralelo (hasta {workers_fase2} hilos)... ---")
        send_progress_update(current_search_item=f"FASE 2: Scrapeando detalles de {len(urls_a_visitar_final)} publicaciones...")
        urls_lista = list(urls_a_visitar_final)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_fase2) as executor:
            mapa_futuros = {executor.submit(scrape_detalle_con_requests, url, API_KEY, USE_THREADS): url for url in urls_lista}
            for i, futuro in enumerate(concurrent.futures.as_completed(mapa_futuros)):
                url_original = mapa_futuros[futuro]
                print(f"Procesando resultado {i+1}/{len(urls_lista)}: {url_original}")
                try:
                    if datos_propiedad := futuro.result():
                        titulo_propiedad = datos_propiedad.get('titulo', 'Sin título')
                        descripcion = datos_propiedad.get('descripcion', '').lower()
                        caracteristicas = datos_propiedad.get('caracteristicas_texto', '').lower()
                        texto_total = f"{titulo_propiedad.lower()} {descripcion} {caracteristicas}"
                        cumple = True
                        if keyword_groups:
                            def normalizar(texto):
                                return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
                            texto_total_norm = normalizar(texto_total)
                            grupos_ok = []
                            for grupo in keyword_groups:
                                variantes_norm = [normalizar(v) for v in grupo]
                                any_match = False
                                for v in variantes_norm:
                                    if v in texto_total_norm:
                                        any_match = True
                                        break
                                    v_stem = stemming_basico(v)
                                    if v_stem and v_stem in texto_total_norm:
                                        any_match = True
                                        break
                                    if len(v) > 4 and v[:-2] in texto_total_norm:
                                        any_match = True
                                        break
                                grupos_ok.append(any_match)
                            cumple = all(grupos_ok) if grupos_ok else True
                            if cumple:
                                # print(f"({i+1}/{len(urls_a_visitar_final)}) ✅ Coincide (100% grupos): {titulo_propiedad}")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ✅ Coincide: {titulo_propiedad}")
                            else:
                                # print(f"({i+1}/{len(urls_a_visitar_final)}) ❌ No coincide (grupos incompletos): {titulo_propiedad}")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ❌ No coincide: {titulo_propiedad} \npara: {keyword_groups}\n\n")
                        else:
                            # Sin keywords: mantener mensaje neutro
                            send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: {titulo_propiedad}")

                        if cumple:
                            # Guardar propiedad
                            try:
                                datos_propiedad['operacion'] = filters.get('operacion', 'venta')
                                datos_propiedad['departamento'] = filters.get('departamento', filters.get('ciudad', 'N/A'))
                                if not datos_propiedad.get('tipo_inmueble') or datos_propiedad.get('tipo_inmueble') == 'N/A':
                                    datos_propiedad['tipo_inmueble'] = filters.get('tipo', 'apartamento')
                                if not datos_propiedad.get('titulo'):
                                    print(f"⚠️ [GUARDADO] Advertencia: título vacío para {url_original}")
                                    datos_propiedad['titulo'] = f"Propiedad en {datos_propiedad.get('departamento', 'N/A')}"
                                print(f"📝 [DEBUG] Guardando: {datos_propiedad.get('titulo')} - {datos_propiedad.get('precio_valor')} {datos_propiedad.get('precio_moneda', '')}")
                                def mapear_datos_propiedad(datos):
                                    try:
                                        plataforma_ml = Plataforma.objects.get(nombre='MercadoLibre')
                                    except Plataforma.DoesNotExist:
                                        plataforma_ml = Plataforma.objects.create(
                                            nombre='MercadoLibre',
                                            url='https://www.mercadolibre.com.uy'
                                        )
                                    datos_mapeados = {
                                        'url': datos.get('url'),
                                        'titulo': datos.get('titulo'),
                                        'descripcion': datos.get('descripcion', ''),
                                        'plataforma': plataforma_ml,
                                        'metadata': {
                                            'precio_valor': datos.get('precio_valor'),
                                            'precio_moneda': datos.get('precio_moneda'),
                                            'operacion': datos.get('operacion'),
                                            'tipo_inmueble': datos.get('tipo_inmueble'),
                                            'departamento': datos.get('departamento'),
                                            'caracteristicas': datos.get('caracteristicas_texto', ''),
                                            'dormitorios': datos.get('dormitorios'),
                                            'banos': datos.get('banos'),
                                            'superficie': datos.get('superficie_total'),
                                            'direccion': datos.get('direccion')
                                        }
                                    }
                                    datos_mapeados['metadata'] = {k: v for k, v in datos_mapeados['metadata'].items() if v is not None}
                                    return datos_mapeados
                                datos_mapeados = mapear_datos_propiedad(datos_propiedad)
                                propiedad_creada = Propiedad.objects.create(**datos_mapeados)
                                nuevas_propiedades_guardadas += 1
                                matched_publications_titles.append({
                                    'title': propiedad_creada.titulo,
                                    'url': propiedad_creada.url
                                })
                                print(f"✅ [GUARDADO] Éxito - ID: {propiedad_creada.id}")
                                send_progress_update(matched_publications=matched_publications_titles)
                            except Exception as save_error:
                                print(f"❌ [GUARDADO] Error guardando propiedad: {save_error}")
                                print(f"❌ [GUARDADO] Datos originales: {datos_propiedad}")
                                try:
                                    print(f"❌ [GUARDADO] Datos mapeados: {datos_mapeados}")
                                except Exception:
                                    pass
                    else:
                        print(f"⚠️ [SCRAPING] No se pudieron extraer datos de: {url_original}")
                        send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: Error al procesar")
                except Exception as exc:
                    print(f'❌ [SCRAPER] URL {url_original[:100]}... generó excepción: {exc}')
    print(f"✅ [COMPLETADO] {nuevas_propiedades_guardadas} nuevas propiedades guardadas")
    # Para la UI actual: mostrar todo bajo 'nuevas' y no poblar 'existentes'
    combined_for_ui = matched_publications_titles + existing_publications_titles
    all_matched_properties = {
        'nuevas': combined_for_ui,
        'existentes': []
    }
    total_coincidentes = len(combined_for_ui)
    print(f"📊 [RESUMEN FINAL] (UI) Nuevas: {len(combined_for_ui)} | Existentes (solo log): {len(existing_publications_titles)} | Total: {total_coincidentes}")
    send_progress_update(
        final_message=f"✅ Búsqueda completada. {nuevas_propiedades_guardadas} nuevas propiedades guardadas.",
        matched_publications=combined_for_ui,
        all_matched_properties=all_matched_properties
    )
    # Retornar lista simple de resultados para flujos sin WebSocket (HTTP fallback/tests)
    return combined_for_ui
