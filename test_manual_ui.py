#!/usr/bin/env python
"""
Script para probar manualmente el envío de datos del formulario web
"""

import webbrowser
import time

def main():
    """
    Abre el navegador y proporciona instrucciones para probar manualmente
    """
    print("🌐 Script de Prueba Manual - InfoCasas Integration")
    print("=" * 60)
    
    print("📋 INSTRUCCIONES DE PRUEBA:")
    print("-" * 30)
    print("1. Se abrirá el navegador con la aplicación")
    print("2. Probará diferentes combinaciones de plataformas:")
    print("   • Solo MercadoLibre")
    print("   • Solo InfoCasas")  
    print("   • Todas las plataformas")
    print("3. Verificar que los resultados aparecen correctamente")
    
    print("\n🔍 CASOS DE PRUEBA RECOMENDADOS:")
    print("-" * 35)
    print("CASO 1 - Solo MercadoLibre:")
    print("  • Plataforma: MercadoLibre")
    print("  • Keywords: apartamento")
    print("  • Operación: Alquiler")
    print("  • Tipo: Apartamento")
    
    print("\nCASO 2 - Solo InfoCasas:")
    print("  • Plataforma: InfoCasas")
    print("  • Keywords: casa")
    print("  • Operación: Venta")
    print("  • Tipo: Casa")
    
    print("\nCASO 3 - Todas las plataformas:")
    print("  • Plataforma: Todas las plataformas")
    print("  • Keywords: piscina")
    print("  • Operación: Alquiler")
    print("  • Precio: 500-1500 USD")
    
    print("\n⚠️  PUNTOS A VERIFICAR:")
    print("-" * 25)
    print("✓ El selector de plataforma aparece en el formulario")
    print("✓ Las búsquedas se procesan sin errores")
    print("✓ Los resultados aparecen con las plataformas correctas")
    print("✓ El progreso WebSocket funciona correctamente")
    print("✓ Los mensajes de progreso mencionan las plataformas")
    
    # Abrir navegador
    print(f"\n🚀 Abriendo navegador en http://localhost:10000...")
    
    try:
        webbrowser.open("http://localhost:10000")
        print("✅ Navegador abierto")
    except Exception as e:
        print(f"❌ Error abriendo navegador: {e}")
        print("💡 Abre manualmente: http://localhost:10000")
    
    print("\n⏰ Presiona Enter cuando hayas terminado las pruebas...")
    input()
    print("✅ Pruebas manuales completadas!")
    
    print("\n📊 RESULTADOS ESPERADOS:")
    print("-" * 28)
    print("• MercadoLibre: ~40-50 resultados para apartamentos/casas")
    print("• InfoCasas: ~20-30 resultados para apartamentos/casas")
    print("• Todas: suma de ambas plataformas (~60-80 total)")
    print("• Progreso debe mostrar 'Procesando plataforma X'")
    print("• Sin errores en consola del navegador")

if __name__ == "__main__":
    main()