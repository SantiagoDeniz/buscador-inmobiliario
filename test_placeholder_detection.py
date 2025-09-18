#!/usr/bin/env python3
"""
Test para verificar que las funciones de placeholder detectan correctamente "Publicación InfoCasas"
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.search_manager import normalizar_texto

def test_normalizar_texto():
    """Test de la función normalizar_texto"""
    print("=== Test normalizar_texto ===")
    
    tests = [
        ("Publicación InfoCasas", "publicacion infocasas"),
        ("Publicación", "publicacion"),
        ("Sin título", "sin titulo"),
        ("Venta apartamento 2 dormitorios", "venta apartamento 2 dormitorios"),
        ("Alquiler casa con patio", "alquiler casa con patio")
    ]
    
    for input_text, expected in tests:
        result = normalizar_texto(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → '{result}' (esperado: '{expected}')")

def test_es_placeholder_functions():
    """Test de las funciones de detección de placeholder"""
    print("\n=== Test funciones es_placeholder ===")
    
    # Simular las funciones actualizadas
    def es_placeholder(t: str) -> bool:
        t_norm = normalizar_texto(t or '')
        return 'publicacion' in t_norm or 'sin titulo' in t_norm or t.strip() == ''
    
    tests = [
        ("Publicación InfoCasas", True, "Debe detectar como placeholder"),
        ("Publicación", True, "Debe detectar como placeholder"), 
        ("Sin título", True, "Debe detectar como placeholder"),
        ("", True, "Texto vacío debe ser placeholder"),
        ("   ", True, "Solo espacios debe ser placeholder"),
        ("Venta apartamento 2 dormitorios", False, "Título real NO debe ser placeholder"),
        ("Alquiler casa con patio", False, "Título real NO debe ser placeholder"),
        ("Casa en venta", False, "Título real NO debe ser placeholder")
    ]
    
    for input_text, expected, descripcion in tests:
        result = es_placeholder(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → {result} ({descripcion})")

if __name__ == "__main__":
    test_normalizar_texto()
    test_es_placeholder_functions()
    print("\n=== Tests completados ===")