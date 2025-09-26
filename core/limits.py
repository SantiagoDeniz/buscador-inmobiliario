"""
Sistema de límites y validaciones para búsquedas e inmobiliarias
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from .models import Busqueda
from .plans import TESTING_MODE


def puede_realizar_accion(usuario, tipo_accion, busqueda_id=None):
    """
    Valida si un usuario puede realizar una acción específica
    
    Args:
        usuario: Instancia del modelo Usuario
        tipo_accion: 'nueva_busqueda' | 'actualizar_busqueda'
        busqueda_id: ID de la búsqueda (solo para actualizar_busqueda)
        
    Returns:
        tuple: (puede_realizar: bool, mensaje: str)
    """
    inmobiliaria = usuario.inmobiliaria
    
    # Modo testing por plan
    if inmobiliaria.plan == 'testing':
        return True, "Plan testing - sin límites"
    
    # Modo testing por variable de entorno (para desarrollo)
    if TESTING_MODE:
        return True, "Testing mode - sin límites"
    
    hoy = timezone.now().date()
    
    if tipo_accion == 'actualizar_busqueda':
        # Límite individual: esta búsqueda específica
        if busqueda_id:
            try:
                busqueda = Busqueda.objects.get(id=busqueda_id)
                if busqueda.ultima_revision:
                    tiempo_transcurrido = timezone.now() - busqueda.ultima_revision
                    horas_requeridas = inmobiliaria.intervalo_actualizacion_horas
                    
                    if tiempo_transcurrido < timedelta(hours=horas_requeridas):
                        horas_restantes = horas_requeridas - (tiempo_transcurrido.total_seconds() / 3600)
                        return False, f"Debe esperar {horas_restantes:.1f}h más para actualizar esta búsqueda"
            except Busqueda.DoesNotExist:
                return False, "Búsqueda no encontrada"
        
        # Límite organizacional: actualizaciones hoy
        actualizaciones_hoy = Busqueda.objects.filter(
            usuario__inmobiliaria=inmobiliaria,
            ultima_revision__date=hoy
        ).count()
        
        if actualizaciones_hoy >= inmobiliaria.max_actualizaciones_por_dia:
            return False, f"Límite diario de actualizaciones alcanzado ({inmobiliaria.max_actualizaciones_por_dia})"
    
    elif tipo_accion == 'nueva_busqueda':
        # Límite organizacional: búsquedas nuevas hoy
        busquedas_hoy = Busqueda.objects.filter(
            usuario__inmobiliaria=inmobiliaria,
            created_at__date=hoy
        ).count()
        
        if busquedas_hoy >= inmobiliaria.max_busquedas_nuevas_por_dia:
            return False, f"Límite diario de búsquedas nuevas alcanzado ({inmobiliaria.max_busquedas_nuevas_por_dia})"
    
    return True, "OK"


def get_limites_usuario(usuario):
    """
    Obtiene información sobre los límites actuales del usuario
    
    Returns:
        dict: Información detallada de límites y uso actual
    """
    inmobiliaria = usuario.inmobiliaria
    hoy = timezone.now().date()
    
    # Si está en modo testing, retornar sin límites
    if inmobiliaria.plan == 'testing' or TESTING_MODE:
        return {
            'modo_testing': True,
            'busquedas_nuevas': {'usadas': 0, 'limite': 'ilimitado', 'restantes': 'ilimitado'},
            'actualizaciones': {'usadas': 0, 'limite': 'ilimitado', 'restantes': 'ilimitado'}
        }
    
    # Contadores actuales
    busquedas_hoy = Busqueda.objects.filter(
        usuario__inmobiliaria=inmobiliaria,
        created_at__date=hoy
    ).count()
    
    actualizaciones_hoy = Busqueda.objects.filter(
        usuario__inmobiliaria=inmobiliaria,
        ultima_revision__date=hoy
    ).count()
    
    return {
        'modo_testing': False,
        'busquedas_nuevas': {
            'usadas': busquedas_hoy,
            'limite': inmobiliaria.max_busquedas_nuevas_por_dia,
            'restantes': max(0, inmobiliaria.max_busquedas_nuevas_por_dia - busquedas_hoy)
        },
        'actualizaciones': {
            'usadas': actualizaciones_hoy,
            'limite': inmobiliaria.max_actualizaciones_por_dia,
            'restantes': max(0, inmobiliaria.max_actualizaciones_por_dia - actualizaciones_hoy)
        },
        'intervalo_actualizacion_horas': inmobiliaria.intervalo_actualizacion_horas
    }


def puede_actualizar_busqueda_especifica(busqueda):
    """
    Valida si una búsqueda específica puede ser actualizada
    
    Returns:
        tuple: (puede_actualizar: bool, mensaje: str, tiempo_restante_horas: float|None)
    """
    if not busqueda.usuario:
        return False, "Búsqueda sin usuario asignado", None
    
    inmobiliaria = busqueda.usuario.inmobiliaria
    
    # Modo testing
    if inmobiliaria.plan == 'testing' or TESTING_MODE:
        return True, "OK", None
    
    if not busqueda.ultima_revision:
        return True, "OK", None  # Primera actualización
    
    tiempo_transcurrido = timezone.now() - busqueda.ultima_revision
    horas_requeridas = inmobiliaria.intervalo_actualizacion_horas
    
    if tiempo_transcurrido < timedelta(hours=horas_requeridas):
        horas_restantes = horas_requeridas - (tiempo_transcurrido.total_seconds() / 3600)
        return False, f"Debe esperar {horas_restantes:.1f}h más", horas_restantes
    
    return True, "OK", None