from typing import Dict, Any, List
import re
import unicodedata


def normalizar_para_url(texto: str) -> str:
    if not texto:
        return ''
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sin_tildes = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    return re.sub(r'[\s_]+', '-', texto_sin_tildes).lower()


def build_mercadolibre_url(filters: Dict[str, Any]) -> str:
    base = 'https://listado.mercadolibre.com.uy/inmuebles/'
    path_parts = []
    filter_segments = []

    # 1) Path segments
    if tipo := filters.get('tipo'):
        t = tipo.strip().lower()
        if t == 'apartamento':
            path_parts.append('apartamentos')
        elif t == 'casa':
            path_parts.append('casas')
        elif t == 'depósito y galpón' or t == 'deposito y galpon' or t == 'deposito-galpon' or t == 'depositos y galpones' or t == 'depositos-galpones':
            path_parts.append('depositos-galpones')
        elif t == 'llave de negocio' or t == 'llave-negocio' or t == 'llave negocio' or t == 'llave':
            path_parts.append('llave-negocio')
        elif t == 'otros inmuebles' or t == 'otros':
            path_parts.append('otros')
        else:
            path_parts.append(normalizar_para_url(tipo))

    if operacion := filters.get('operacion'):
        path_parts.append(normalizar_para_url(operacion))

    dormitorios_min = filters.get('dormitorios_min')
    dormitorios_max = filters.get('dormitorios_max')
    if dormitorios_min and dormitorios_max:
        if str(dormitorios_min) == str(dormitorios_max):
            path_parts.append(f'{dormitorios_min}-dormitorios')
        else:
            path_parts.append(f'{dormitorios_min}-a-{dormitorios_max}-dormitorios')
    elif dormitorios_min:
        path_parts.append(f'{dormitorios_min}-o-mas-dormitorios')

    if departamento := filters.get('departamento'):
        path_parts.append(normalizar_para_url(departamento))

    if filters.get('departamento') == 'Montevideo' and (ciudad := filters.get('ciudad')):
        path_parts.append(normalizar_para_url(ciudad))

    # 2) Filter segments (_Clave_Valor)
    def add_range_filter(param_name, min_key, max_key, unit=''):
        min_val = filters.get(min_key, '')
        max_val = filters.get(max_key, '')
        if str(min_val) == '0' and str(max_val) == '0':
            filter_segments.append(f'_{param_name}_0{unit}-0{unit}')
            return
        if min_val != '' or max_val != '':
            min_str = str(min_val) if min_val != '' else '0'
            max_str = str(max_val) if max_val != '' else '0'
            filter_segments.append(f'_{param_name}_{min_str}{unit}-{max_str}{unit}')

    moneda = (filters.get('moneda', 'USD') or 'USD').upper()
    add_range_filter('PriceRange', 'precio_min', 'precio_max', unit=moneda)
    add_range_filter('FULL*BATHROOMS', 'banos_min', 'banos_max')

    if filters.get('amoblado'):
        filter_segments.append('_FURNISHED_242085')
    if filters.get('terraza'):
        filter_segments.append('_HAS*TERRACE_242085')
    if filters.get('aire_acondicionado'):
        filter_segments.append('_HAS*AIR*CONDITIONING_242085')
    if filters.get('piscina'):
        filter_segments.append('_HAS*SWIMMING*POOL_242085')
    if filters.get('jardin'):
        filter_segments.append('_HAS*GARDEN_242085')
    if filters.get('ascensor'):
        filter_segments.append('_HAS*LIFT_242085')

    filter_segments.append('_NoIndex_True')

    add_range_filter('PARKING*LOTS', 'cocheras_min', 'cocheras_max')
    add_range_filter('PROPERTY*AGE', 'antiguedad_min', 'antiguedad_max')
    add_range_filter('TOTAL*AREA', 'superficie_total_min', 'superficie_total_max')
    add_range_filter('COVERED*AREA', 'superficie_cubierta_min', 'superficie_cubierta_max')

    if condicion := filters.get('condicion'):
        if condicion == 'Nuevo':
            filter_segments.append('_ITEM*CONDITION_2230284')
        elif condicion == 'Usado':
            filter_segments.append('_ITEM*CONDITION_2230581')

    path_str = '/'.join(filter(None, path_parts))
    if path_str:
        path_str += '/'

    filter_str = ''.join(filter_segments)

    return base + path_str + filter_str


def build_infocasas_url(filters: Dict[str, Any], keywords: List[str] = None) -> str:
    """
    Construye URL de InfoCasas con filtros específicos.
    Ejemplo: https://www.infocasas.com.uy/venta/apartamentos/montevideo/1-o-mas-dormitorios/1-bano/con-estufa-a-lena-y-con-parrillero-o-barbacoa-y-con-balcon-o-terraza-y-con-gym-y-con-lavanderia-y-con-piscina-y-con-calefaccion/con-garaje/en-pozo/planta-baja/desde-300/hasta-100000/dolares/m2-desde-11/m2-hasta-500/edificados/publicado-ultimos-7-dias?&searchstring=queso-con-salame
    """
    base = 'https://www.infocasas.com.uy/'
    path_parts = []
    query_params = []

    print(f"\n\n\n   Filters para InfoCasas: {filters}\n\n\n")
    print(f"\n\n\n   Keywords para InfoCasas: {keywords}\n\n\n")
    # 1) Operación (requerida)
    operacion = filters.get('operacion', 'venta')
    if operacion.lower() == 'alquiler':
        path_parts.append('alquiler')
    else:
        path_parts.append('venta')

    # 2) Tipo de propiedad
    if tipo := filters.get('tipo'):
        t = tipo.strip().lower()
        if t == 'apartamento':
            path_parts.append('apartamentos')
        elif t == 'casa':
            path_parts.append('casas')
        elif t == 'local comercial' or t == 'local':
            path_parts.append('locales-comerciales')
        elif t == 'terreno':
            path_parts.append('terrenos')
        elif t == 'oficina':
            path_parts.append('oficinas')
        elif t == 'galpón' or t == 'galpon':
            path_parts.append('galpones')
        else:
            path_parts.append(normalizar_para_url(tipo))

    # 3) Ubicación
    if departamento := filters.get('departamento'):
        path_parts.append(normalizar_para_url(departamento))
        
        # Ciudad solo si departamento es Montevideo
        if departamento.lower() == 'montevideo' and (ciudad := filters.get('ciudad')):
            path_parts.append(normalizar_para_url(ciudad))

    # 4) Dormitorios
    dormitorios_min = filters.get('dormitorios_min')
    dormitorios_max = filters.get('dormitorios_max')
    if dormitorios_min and dormitorios_max:
        if str(dormitorios_min) == str(dormitorios_max):
            if dormitorios_min == 0:
                path_parts.append('monoambiente')
            else:
                path_parts.append(f'{dormitorios_min}-dormitorio' if dormitorios_min == 1 else f'{dormitorios_min}-dormitorios')
        else:
            # Rango de dormitorios
            dorm_parts = []
            for i in range(int(dormitorios_min), int(dormitorios_max) + 1):
                if i == 0:
                    dorm_parts.append('monoambiente')
                elif i == 1:
                    dorm_parts.append('1-dormitorio')
                else:
                    dorm_parts.append(f'{i}-dormitorios')
            path_parts.append('-y-'.join(dorm_parts))
    elif dormitorios_min:
        if dormitorios_min == 0:
            path_parts.append('monoambiente')
        elif dormitorios_min == 1:
            path_parts.append('1-o-mas-dormitorios')
        else:
            path_parts.append(f'{dormitorios_min}-o-mas-dormitorios')

    # 5) Baños
    banos_min = filters.get('banos_min')
    banos_max = filters.get('banos_max')
    if banos_min and banos_max:
        if str(banos_min) == str(banos_max):
            path_parts.append(f'{banos_min}-bano' if banos_min == 1 else f'{banos_min}-banos')
        else:
            # Rango de baños
            bano_parts = []
            for i in range(int(banos_min), int(banos_max) + 1):
                bano_parts.append(f'{i}-bano' if i == 1 else f'{i}-banos')
            path_parts.append('-y-'.join(bano_parts))
    elif banos_min:
        path_parts.append(f'{banos_min}-bano' if banos_min == 1 else f'{banos_min}-banos')

    # 6) Filtros booleanos con concatenación
    filtros_booleanos = []
    
    if filters.get('estufa_lena'):
        filtros_booleanos.append('con-estufa-a-lena')
    if filters.get('parrillero'):
        filtros_booleanos.append('con-parrillero-o-barbacoa')
    if filters.get('terraza'):
        filtros_booleanos.append('con-balcon-o-terraza')
    if filters.get('gym'):
        filtros_booleanos.append('con-gym')
    if filters.get('lavanderia'):
        filtros_booleanos.append('con-lavanderia')
    if filters.get('piscina'):
        filtros_booleanos.append('con-piscina')
    if filters.get('calefaccion'):
        filtros_booleanos.append('con-calefaccion')

    if filtros_booleanos:
        path_parts.append('-y-'.join(filtros_booleanos))

    # 7) Garage/Cochera
    if filters.get('garage') or filters.get('cocheras_min'):
        path_parts.append('con-garaje')

    # 8) Estado
    if estado := filters.get('estado'):
        e = estado.lower()
        if e == 'en pozo':
            path_parts.append('en-pozo')
        elif e == 'en construccion' or e == 'en construcción':
            path_parts.append('en-construccion')
        elif e == 'a estrenar':
            path_parts.append('a-estrenar')
        elif e == 'usado' or e == 'usados':
            path_parts.append('usados')

    # 9) Pisos especiales
    if piso := filters.get('piso'):
        if piso.lower() == 'planta baja':
            path_parts.append('planta-baja')
        elif piso.lower() == 'penthouse':
            path_parts.append('penthouse')

    # 10) Rango de precios
    precio_min = filters.get('precio_min')
    precio_max = filters.get('precio_max')
    if precio_min or precio_max:
        if precio_min:
            path_parts.append(f'desde-{precio_min}')
        if precio_max:
            path_parts.append(f'hasta-{precio_max}')
        
        # InfoCasas parece usar solo dólares en la URL
        moneda = filters.get('moneda', 'USD')
        if moneda.upper() == 'USD':
            path_parts.append('dolares')
        else:
            path_parts.append('pesos')

    # 11) Metraje
    superficie_min = filters.get('superficie_total_min') or filters.get('superficie_cubierta_min')
    superficie_max = filters.get('superficie_total_max') or filters.get('superficie_cubierta_max')
    if superficie_min or superficie_max:
        if superficie_min:
            path_parts.append(f'm2-desde-{superficie_min}')
        if superficie_max:
            path_parts.append(f'm2-hasta-{superficie_max}')
        path_parts.append('edificados')

    # 12) Fecha de publicación
    if fecha_pub := filters.get('fecha_publicacion'):
        f = fecha_pub.lower()
        if f == 'hoy':
            path_parts.append('publicado-hoy')
        elif f == 'ayer':
            path_parts.append('publicado-ayer')
        elif f == 'ultima semana' or f == 'última semana':
            path_parts.append('publicado-ultimos-7-dias')
        elif f == 'ultimos 15 dias' or f == 'últimos 15 días':
            path_parts.append('publicado-ultimos-15-dias')
        elif f == 'ultimos 30 dias' or f == 'últimos 30 días':
            path_parts.append('publicado-ultimos-30-dias')
        elif f == 'ultimos 45 dias' or f == 'últimos 45 días':
            path_parts.append('publicado-ultimos-45-dias')

    # 13) Keywords como searchstring
    # Usar keywords del parámetro separado si existe, sino del diccionario filters
    if keywords is not None:
        used_keywords = keywords
    else:
        used_keywords = filters.get('keywords', [])
        
    if used_keywords:
        if isinstance(used_keywords, list):
            searchstring = '-'.join([normalizar_para_url(k) for k in used_keywords])
        else:
            searchstring = normalizar_para_url(str(used_keywords))
        query_params.append(f'searchstring={searchstring}')

    # Construir URL final
    path_str = '/'.join(filter(None, path_parts))
    query_str = '&'.join(query_params)
    
    url = base + path_str
    if query_str:
        url += '?' + ('&' if '?' not in url else '') + query_str
    
    return url
