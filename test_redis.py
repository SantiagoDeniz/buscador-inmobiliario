#!/usr/bin/env python
"""
Script de prueba para verificar la conexión Redis en Render
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

def test_redis_connection():
    """Probar conexión a Redis"""
    print("🔍 Probando conexión a Redis...")
    
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        redis_url = os.environ.get('REDIS_URL', 'No configurada')
        
        print(f"📡 Redis URL: {redis_url[:50]}...")
        print(f"🔧 Channel Layer: {type(channel_layer)}")
        
        if channel_layer is None:
            print("❌ Channel layer no disponible")
            return False
        
        # Intentar enviar un mensaje de prueba
        async_to_sync(channel_layer.group_send)("test_group", {
            "type": "test_message",
            "message": "Conexión exitosa"
        })
        
        print("✅ Conexión a Redis exitosa!")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
