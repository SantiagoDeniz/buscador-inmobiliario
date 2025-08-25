#!/usr/bin/env python
"""
Test directo de Redis sin Django
"""
import redis
import os
from dotenv import load_dotenv

load_dotenv()

def test_redis_direct():
    """Probar conexión directa a Redis"""
    redis_url = os.environ.get('REDIS_URL')
    print(f"🔍 Probando conexión directa a Redis...")
    print(f"📡 Redis URL: {redis_url[:50]}...")
    
    try:
        # Crear conexión Redis directa
        r = redis.from_url(redis_url)
        
        # Hacer ping
        response = r.ping()
        print(f"✅ Ping response: {response}")
        
        # Probar set/get básico
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"✅ Set/Get test: {value}")
        
        # Limpiar
        r.delete('test_key')
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión directa: {e}")
        print(f"❌ Tipo de error: {type(e)}")
        return False

if __name__ == "__main__":
    success = test_redis_direct()
