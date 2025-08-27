#!/usr/bin/env python
import os
import sys
import django
import unicodedata

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
django.setup()

from core.search_manager import procesar_keywords

def test_keyword_filtering():
    """Test del filtrado de keywords que usa el scraper"""
    print("🧪 [TEST KEYWORDS] Probando filtrado de palabras clave...\n")
    
    # Keywords de prueba
    test_keywords = ["luminoso", "parrillero", "rambla"]
    
    # Texto de prueba (similar al de una propiedad real)
    titulo_real = "Cordon Pre Venta Apartamento 1 Dormitorio Amenities"
    descripcion_real = """Edificio MET TECH, MUY BUENA UBICACION, EN EL CORAZON DEL BARRIO CORDON SOBRE LA CALLE CONSTITUYENTE, CERCA DE UNIVERSIDADES Y TODOS LOS SERVICIOS / Entrega de unidades:
DICIEMBRE 2025- Edificio con propuestas arquitectónicas innovadoras, finas terminaciones y Amenities Premium! Las unidades se destacan por su luminosidad, sus amplios ventanales, vistas despejadas Living-comedor con salida a terraza al frente Cocina integrada, dispone de buena capacidad de muebles aéreos y bajo mesada- Se entrega con splits de aire acondicionado ya instalados en Living y Dormitorio  BENEFICIOS IMPOSITIVOS por construirse bajo la Ley de Vivienda Promovida AL MOMENTO DE LA COMPRA: * Exoneración del ITP (2% sobre el valor catastral) * Exoneración del IVA del precio de compra POR 10 AÑOS: * Exoneración del Impuesto a la Renta de los Alquileres * Exoneración del Impuesto al Patrimonio  OPORTUNIDADES DE PREVENTA: * Monoambientes desde USD99.213- * 1 Dormitorio desde USD134.120- * 2 Dormitorios desde USD172.838- GARAGES desde USD19.870- BAULERAS: USD4.415-  AMENITIES PREMIUM: * Barbacoa en azotea con Parrillero y área de Solarium con vistas panorámicas a la Rambla * Piscina abierta e nivel de la azotea * Gimnasio * Cowork * Laundry * Bike parking Por consultas y coordinación de visitas favor enviar mensaje vía WhatsApp o llamar al celular de contacto"""
    
    caracteristicas_real = """Superficie total: 49 m²
Área privada: 41 m²
Superficie de balcón: 8 m²
Ambientes: 2
Dormitorios: 1
Baños: 1
Cocheras: 0
Bodegas: 0
Cantidad de pisos: 1
Apartamentos por piso: 2
Número de piso de la unidad: 2
Tipo de departamento: Departamento
Disposición: Frente
Orientación: Sur
Antigüedad: 0 años
Agua corriente: Sí
Aire acondicionado: Sí
Calefacción: Sí
Gimnasio: Sí
Ascensor: Sí
Circuito de cámaras de seguridad: Sí
Placards: No
Baño social: No
Terraza: Sí
Comedor: No
Estudio: No
Living: Sí
Patio: No
Dormitorio en suite: No
Jardín: No
Cocina: Sí
Dormitorio de servicio: No
Con lavadero: Sí
Parrillero: Sí
Piscina: Sí
Admite mascotas: Sí
Depósitos: 0"""
    
    # Probar el procesamiento de keywords
    print("📝 [TEST] Keywords originales:", test_keywords)
    keywords_procesadas = procesar_keywords(' '.join(test_keywords))
    print("📝 [TEST] Keywords procesadas:", keywords_procesadas)
    
    # Simular el texto total que usa el scraper
    texto_total = f"{titulo_real.lower()} {descripcion_real.lower()} {caracteristicas_real.lower()}"
    print(f"\n📄 [TEST] Texto total tiene {len(texto_total)} caracteres")
    
    # Función de normalización (copiada del scraper)
    def normalizar(texto):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    # Probar normalización
    keywords_norm = [normalizar(kw) for kw in keywords_procesadas]
    texto_total_norm = normalizar(texto_total)
    
    print(f"📝 [TEST] Keywords normalizadas: {keywords_norm}")
    print(f"📄 [TEST] Texto normalizado tiene {len(texto_total_norm)} caracteres")
    
    # Verificar cada keyword individualmente
    print(f"\n🔍 [TEST] Verificando cada keyword:")
    for i, kw in enumerate(keywords_norm):
        encontrada = kw in texto_total_norm
        print(f"  - '{kw}': {'✅ ENCONTRADA' if encontrada else '❌ NO ENCONTRADA'}")
        
        if not encontrada:
            # Buscar palabras similares
            palabras_similares = [palabra for palabra in texto_total_norm.split() if kw in palabra or palabra in kw]
            if palabras_similares:
                print(f"    Palabras similares encontradas: {palabras_similares[:5]}")
    
    # Verificar si todas las keywords están presentes (lógica del scraper)
    cumple = all(kw in texto_total_norm for kw in keywords_norm)
    print(f"\n🎯 [TEST] ¿Cumple con todas las keywords? {'✅ SÍ' if cumple else '❌ NO'}")
    
    return cumple

def test_simple_keywords():
    """Test con keywords más simples"""
    print(f"\n🧪 [TEST SIMPLE] Probando con keywords más básicas...\n")
    
    # Keywords que deberían encontrarse fácilmente
    test_keywords = ["dormitorio", "apartamento"]
    titulo_simple = "Apartamento 1 dormitorio en venta"
    
    keywords_procesadas = procesar_keywords(' '.join(test_keywords))
    print("📝 [TEST] Keywords procesadas:", keywords_procesadas)
    
    def normalizar(texto):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    keywords_norm = [normalizar(kw) for kw in keywords_procesadas]
    texto_norm = normalizar(titulo_simple)
    
    print(f"📝 [TEST] Keywords normalizadas: {keywords_norm}")
    print(f"📄 [TEST] Texto: '{texto_norm}'")
    
    for kw in keywords_norm:
        encontrada = kw in texto_norm
        print(f"  - '{kw}': {'✅ ENCONTRADA' if encontrada else '❌ NO ENCONTRADA'}")
    
    cumple = all(kw in texto_norm for kw in keywords_norm)
    print(f"\n🎯 [TEST] ¿Cumple? {'✅ SÍ' if cumple else '❌ NO'}")
    
    return cumple

if __name__ == '__main__':
    print("🚀 [TEST KEYWORDS] Iniciando pruebas de filtrado de keywords...\n")
    
    # Test 1: Keywords complejas
    test1_ok = test_keyword_filtering()
    
    # Test 2: Keywords simples
    test2_ok = test_simple_keywords()
    
    print(f"\n📊 [RESUMEN]")
    print(f"Test keywords complejas: {'✅ OK' if test1_ok else '❌ FALLO'}")
    print(f"Test keywords simples: {'✅ OK' if test2_ok else '❌ FALLO'}")
    
    if not test1_ok and not test2_ok:
        print("⚠️ [CONCLUSIÓN] El filtrado de keywords es muy estricto y podría estar impidiendo que se guarden propiedades")
    elif not test1_ok:
        print("⚠️ [CONCLUSIÓN] El filtrado funciona para keywords simples pero falla con complejas")
    else:
        print("✅ [CONCLUSIÓN] El filtrado de keywords funciona correctamente")
