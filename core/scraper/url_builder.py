from typing import Dict, Any
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
