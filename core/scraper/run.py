import concurrent.futures
import os
import unicodedata
from typing import Dict, Any, List
from core.models import Propiedad, Plataforma
from .url_builder import build_mercadolibre_url
from .mercadolibre import extraer_total_resultados_mercadolibre
from .extractors import scrape_detalle_con_requests, recolectar_urls_de_pagina
from .progress import send_progress_update
from .utils import stemming_basico, extraer_variantes_keywords


def run_scraper(filters: dict, keywords: list = None, max_paginas: int = 3, workers_fase1: int = 1, workers_fase2: int = 1):
    print(f"🚀 [SCRAPER] Iniciando búsqueda - Filtros: {len(filters)} | Keywords: {len(keywords) if keywords else 0}")
    matched_publications_titles: List[dict] = []

    from core.search_manager import procesar_keywords
    keywords_filtradas = procesar_keywords(' '.join(keywords)) if keywords else []
    keywords_variantes = extraer_variantes_keywords(keywords_filtradas)
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

    propiedades_omitidas = 0
    nuevas_propiedades_guardadas = 0
    urls_a_visitar_final = set()

    try:
        url_base_con_filtros = build_mercadolibre_url(filters)
        print(f"🔗 [URL GENERADA] {url_base_con_filtros}")
        if url_base_con_filtros.endswith('_NoIndex_True') and 'inmuebles/_NoIndex_True' in url_base_con_filtros:
            print("⚠️ [URL BUILD] URL generada es demasiado genérica, puede indicar problema en filtros")
        send_progress_update(current_search_item=f"🏠 URL generada con filtros: {url_base_con_filtros[:100]}{'...' if len(url_base_con_filtros) > 100 else ''}")
    except Exception as e:
        print(f"❌ [URL BUILD] Error construyendo URL: {e}")
        send_progress_update(final_message=f"❌ Error construyendo URL: {e}")
        return

    print("\n[Principal] Extrayendo total de resultados desde MercadoLibre...")
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
                urls_nuevas, _ = futuro.result()
                urls_recolectadas_bruto.update(urls_nuevas)
    else:
        for url in paginas_de_resultados:
            urls_nuevas, _ = recolectar_urls_de_pagina(url, API_KEY, ubicacion_param, False)
            urls_recolectadas_bruto.update(urls_nuevas)

    print(f"\n[Principal] FASE 1 Recolección Bruta Finalizada. Se obtuvieron {len(urls_recolectadas_bruto)} URLs en total.")
    send_progress_update(current_search_item=f"FASE 1 completada. Se encontraron {len(urls_recolectadas_bruto)} URLs de publicaciones.")

    print("\n[Principal] Iniciando chequeo de duplicados contra la base de datos...")
    send_progress_update(current_search_item="Chequeando publicaciones existentes en la base de datos...")
    existing_publications_titles = []

    if urls_recolectadas_bruto:
        urls_existentes = set(Propiedad.objects.filter(url__in=list(urls_recolectadas_bruto)).values_list('url', flat=True))
        propiedades_omitidas = len(urls_existentes)
        urls_a_visitar_final = urls_recolectadas_bruto - urls_existentes

        if urls_existentes and keywords_variantes:
            existing_properties = Propiedad.objects.filter(url__in=urls_existentes)

            def normalizar(texto):
                return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()

            keywords_norm = [normalizar(kw) for kw in keywords_variantes]

            for prop in existing_properties:
                titulo_propiedad = prop.titulo or ''
                descripcion = prop.descripcion or ''
                meta = prop.metadata or {}
                caracteristicas = meta.get('caracteristicas', '') or meta.get('caracteristicas_texto', '') or ''
                texto_total = f"{titulo_propiedad.lower()} {descripcion.lower()} {caracteristicas.lower()}"
                texto_total_norm = normalizar(texto_total)

                keywords_encontradas = 0
                for kw in keywords_norm:
                    encontrada = False
                    if kw in texto_total_norm:
                        encontrada = True
                    elif not encontrada:
                        kw_stem = stemming_basico(kw)
                        if kw_stem in texto_total_norm:
                            encontrada = True
                    elif not encontrada and len(kw) > 4:
                        raiz = kw[:len(kw)-2]
                        if raiz in texto_total_norm:
                            encontrada = True
                    if encontrada:
                        keywords_encontradas += 1
                porcentaje_requerido = 0.7
                if keywords_encontradas >= len(keywords_norm) * porcentaje_requerido:
                    existing_publications_titles.append({
                        'title': titulo_propiedad,
                        'url': prop.url
                    })
        elif urls_existentes and not keywords_variantes:
            existing_properties = Propiedad.objects.filter(url__in=urls_existentes)
            for prop in existing_properties:
                existing_publications_titles.append({
                    'title': prop.titulo or 'Sin título',
                    'url': prop.url
                })

        print(f"🗃️  [DEDUP] Existentes: {propiedades_omitidas} | Nuevas: {len(urls_a_visitar_final)}")
        print(f"🗃️  [DEDUP] Coincidentes existentes: {len(existing_publications_titles)}")
        send_progress_update(current_search_item=f"Existentes: {propiedades_omitidas} | Nuevas: {len(urls_a_visitar_final)}")
    else:
        print("❌ [RECOLECCIÓN] No se obtuvieron URLs")
        send_progress_update(current_search_item="No se encontraron URLs para procesar.")

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
                        if keywords_variantes:
                            def normalizar(texto):
                                return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
                            keywords_norm = [normalizar(kw) for kw in keywords_variantes]
                            texto_total_norm = normalizar(texto_total)
                            keywords_encontradas = 0
                            for kw in keywords_norm:
                                encontrada = False
                                if kw in texto_total_norm:
                                    encontrada = True
                                elif not encontrada:
                                    kw_stem = stemming_basico(kw)
                                    if kw_stem in texto_total_norm:
                                        encontrada = True
                                elif not encontrada and len(kw) > 4:
                                    raiz = kw[:len(kw)-2]
                                    if raiz in texto_total_norm:
                                        encontrada = True
                                if encontrada:
                                    keywords_encontradas += 1
                            porcentaje_requerido = 0.7
                            cumple = keywords_encontradas >= len(keywords_norm) * porcentaje_requerido
                            if cumple:
                                print(f"({i+1}/{len(urls_a_visitar_final)}) ✅ Coincide: {titulo_propiedad} ({keywords_encontradas}/{len(keywords_norm)} keywords)")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ✅ Coincide: {titulo_propiedad}")
                            else:
                                print(f"({i+1}/{len(urls_a_visitar_final)}) ❌ No coincide: {titulo_propiedad} ({keywords_encontradas}/{len(keywords_norm)} keywords)")
                                send_progress_update(current_search_item=f"({i+1}/{len(mapa_futuros)}) ❌ No coincide: {titulo_propiedad}")
                        else:
                            send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: {titulo_propiedad}")
                        if cumple:
                            print(f"✅ [GUARDADO] {titulo_propiedad[:60]}...")
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
                                print(f"❌ [GUARDADO] Datos mapeados: {datos_mapeados}")
                    else:
                        print(f"⚠️ [SCRAPING] No se pudieron extraer datos de: {url_original}")
                        send_progress_update(current_search_item=f"Procesando publicación {i+1}/{len(urls_lista)}: Error al procesar")
                except Exception as exc:
                    print(f'❌ [SCRAPER] URL {url_original[:100]}... generó excepción: {exc}')
    print(f"✅ [COMPLETADO] {nuevas_propiedades_guardadas} nuevas propiedades guardadas")
    all_matched_properties = {
        'nuevas': matched_publications_titles,
        'existentes': existing_publications_titles
    }
    total_coincidentes = len(matched_publications_titles) + len(existing_publications_titles)
    print(f"📊 [RESUMEN FINAL] Nuevas: {len(matched_publications_titles)} | Existentes: {len(existing_publications_titles)} | Total: {total_coincidentes}")
    send_progress_update(
        final_message=f"✅ Búsqueda completada. {nuevas_propiedades_guardadas} nuevas propiedades guardadas.",
        matched_publications=matched_publications_titles,
        all_matched_properties=all_matched_properties
    )
