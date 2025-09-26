"""
Configuración de planes y límites para inmobiliarias
"""
import os

# Planes disponibles con sus límites
PLANES = {
    'basico': {
        'intervalo_actualizacion_horas': 4,
        'max_actualizaciones_por_dia': 5,
        'max_busquedas_nuevas_por_dia': 3
    },
    'premium': {
        'intervalo_actualizacion_horas': 2,
        'max_actualizaciones_por_dia': 15,
        'max_busquedas_nuevas_por_dia': 10
    },
    'enterprise': {
        'intervalo_actualizacion_horas': 1,
        'max_actualizaciones_por_dia': 50,
        'max_busquedas_nuevas_por_dia': 25
    },
    'testing': {
        'intervalo_actualizacion_horas': 0,
        'max_actualizaciones_por_dia': 99999,
        'max_busquedas_nuevas_por_dia': 99999
    }
}

# Variable de entorno para modo testing
TESTING_MODE = os.environ.get('BUSCADOR_TESTING_MODE', 'False').lower() == 'true'

def aplicar_configuracion_plan(inmobiliaria, plan_nombre):
    """Aplica la configuración de un plan a una inmobiliaria"""
    if plan_nombre not in PLANES:
        raise ValueError(f"Plan '{plan_nombre}' no existe. Planes disponibles: {list(PLANES.keys())}")
    
    config = PLANES[plan_nombre]
    inmobiliaria.plan = plan_nombre
    inmobiliaria.intervalo_actualizacion_horas = config['intervalo_actualizacion_horas']
    inmobiliaria.max_actualizaciones_por_dia = config['max_actualizaciones_por_dia']
    inmobiliaria.max_busquedas_nuevas_por_dia = config['max_busquedas_nuevas_por_dia']
    return inmobiliaria

def get_plan_info(plan_nombre):
    """Obtiene información de un plan"""
    return PLANES.get(plan_nombre, {})