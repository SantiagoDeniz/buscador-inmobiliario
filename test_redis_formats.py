#!/usr/bin/env python
"""
Script para probar diferentes formatos de conexión Redis con Upstash
"""

import os
import redis
from urllib.parse import urlparse

def test_redis_formats():
    redis_url = os.getenv('REDIS_URL')
    
    if not redis_url:
        print("❌ REDIS_URL no está configurada")
        print("💡 Para probar, configura REDIS_URL con tu URL de Upstash:")
        print("   $env:REDIS_URL='redis://default:tu_password@tu-host:tu-port'")
        print("   python test_redis_formats.py")
        return False, None
    
    # Parse URL para entender la estructura
    parsed = urlparse(redis_url)
    print(f"📡 URL original: {redis_url[:50]}...")
    print(f"🔍 Host: {parsed.hostname}")
    print(f"🔍 Port: {parsed.port}")
    print(f"🔍 Username: {parsed.username}")
    print(f"🔍 Password: {'*' * len(parsed.password) if parsed.password else None}")
    
    # Intentar diferentes configuraciones para Upstash
    configs_to_try = [
        {
            'name': 'Configuración Original',
            'url': redis_url,
            'ssl_cert_reqs': None,
            'ssl_check_hostname': None,
        },
        {
            'name': 'Con SSL (rediss)',
            'url': redis_url.replace('redis://', 'rediss://'),
            'ssl_cert_reqs': None,
            'ssl_check_hostname': False,
        },
        {
            'name': 'SSL con certificado relajado',
            'url': redis_url.replace('redis://', 'rediss://'),
            'ssl_cert_reqs': 'none',
            'ssl_check_hostname': False,
        },
        {
            'name': 'Conexión directa por host',
            'host': parsed.hostname,
            'port': parsed.port or 6379,
            'username': parsed.username,
            'password': parsed.password,
            'ssl': True,
            'ssl_cert_reqs': None,
            'ssl_check_hostname': False,
        }
    ]
    
    for i, config in enumerate(configs_to_try, 1):
        print(f"\n🔄 Prueba {i}: {config['name']}")
        
        try:
            # Crear cliente según configuración
            if 'url' in config:
                kwargs = {
                    'decode_responses': True,
                    'socket_timeout': 10,
                    'socket_connect_timeout': 10
                }
                
                if config.get('ssl_cert_reqs'):
                    kwargs['ssl_cert_reqs'] = config['ssl_cert_reqs']
                if config.get('ssl_check_hostname') is not None:
                    kwargs['ssl_check_hostname'] = config['ssl_check_hostname']
                    
                r = redis.from_url(config['url'], **kwargs)
            else:
                # Conexión directa
                r = redis.Redis(
                    host=config['host'],
                    port=config['port'],
                    username=config['username'],
                    password=config['password'],
                    ssl=config.get('ssl', False),
                    ssl_cert_reqs=config.get('ssl_cert_reqs'),
                    ssl_check_hostname=config.get('ssl_check_hostname', True),
                    decode_responses=True,
                    socket_timeout=10,
                    socket_connect_timeout=10
                )
            
            # Probar conexión
            print("   🔄 Probando ping...")
            result = r.ping()
            print(f"   ✅ Ping exitoso: {result}")
            
            # Probar set/get
            print("   🔄 Probando set/get...")
            r.set('test_key', 'test_value', ex=30)  # Expira en 30s
            value = r.get('test_key')
            print(f"   ✅ Set/Get funciona: {value}")
            
            # Limpiar
            r.delete('test_key')
            r.close()
            
            print(f"   🎉 ¡Configuración {i} funciona!")
            return True, config  # Si llegamos aquí, funciona
            
        except Exception as e:
            print(f"   ❌ Configuración {i} falló: {e}")
            print(f"   📝 Tipo de error: {type(e).__name__}")
            if hasattr(e, 'errno'):
                print(f"   📝 Error code: {e.errno}")
    
    return False, None

if __name__ == "__main__":
    print("🧪 Probando configuraciones de Redis para Upstash...")
    
    success, working_config = test_redis_formats()
    
    print("\n" + "="*60)
    print("📊 Resultados:")
    if success:
        print(f"✅ ¡Conexión exitosa!")
        print(f"🔧 Configuración que funcionó: {working_config['name']}")
    else:
        print("❌ Ninguna configuración funcionó")
        print("� Verifica:")
        print("   - La URL de Redis está correcta")
        print("   - Las credenciales son válidas") 
        print("   - El servicio de Upstash está activo")
        print("   - No hay restricciones de IP")
