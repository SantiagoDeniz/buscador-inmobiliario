#!/usr/bin/env python

def test_nueva_logica_keywords():
    """Test de la nueva lógica de keywords más flexible"""
    print("🧪 [TEST] Probando nueva lógica de keywords flexible...\n")
    
    import unicodedata
    
    def normalizar(texto):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    def stemming_basico(palabra):
        """Stemming básico para español"""
        # Remover sufijos comunes
        sufijos = ['oso', 'osa', 'idad', 'cion', 'sion', 'ero', 'era', 'ado', 'ada']
        for sufijo in sufijos:
            if palabra.endswith(sufijo) and len(palabra) > len(sufijo) + 3:
                return palabra[:-len(sufijo)]
        return palabra
    
    # Test data
    keywords_test = ["luminoso", "parrillero", "rambla"]
    texto_test = "Las unidades se destacan por su luminosidad, sus amplios ventanales, vistas despejadas. Barbacoa en azotea con Parrillero y área de Solarium con vistas panorámicas a la Rambla"
    
    print(f"📝 Keywords: {keywords_test}")
    print(f"📄 Texto: {texto_test[:100]}...")
    
    keywords_norm = [normalizar(kw) for kw in keywords_test]
    texto_total_norm = normalizar(texto_test)
    
    print(f"\n🔍 Verificando con nueva lógica:")
    
    # Verificar cada keyword con múltiples estrategias
    keywords_encontradas = 0
    for kw in keywords_norm:
        encontrada = False
        metodo_usado = ""
        
        # 1. Coincidencia exacta
        if kw in texto_total_norm:
            encontrada = True
            metodo_usado = "exacta"
        
        # 2. Coincidencia con stemming básico
        elif not encontrada:
            kw_stem = stemming_basico(kw)
            if kw_stem in texto_total_norm:
                encontrada = True
                metodo_usado = f"stemming ({kw} -> {kw_stem})"
        
        # 3. Buscar raíz de la keyword en el texto
        elif not encontrada and len(kw) > 4:
            raiz = kw[:len(kw)-2]  # Tomar los primeros n-2 caracteres
            if raiz in texto_total_norm:
                encontrada = True
                metodo_usado = f"raíz ({kw} -> {raiz})"
        
        print(f"  - '{kw}': {'✅' if encontrada else '❌'} {metodo_usado}")
        
        if encontrada:
            keywords_encontradas += 1
    
    # Calcular porcentaje
    porcentaje_requerido = 0.7
    porcentaje_actual = keywords_encontradas / len(keywords_norm)
    cumple = keywords_encontradas >= len(keywords_norm) * porcentaje_requerido
    
    print(f"\n📊 Resultados:")
    print(f"  Keywords encontradas: {keywords_encontradas}/{len(keywords_norm)} ({porcentaje_actual:.1%})")
    print(f"  Porcentaje requerido: {porcentaje_requerido:.1%}")
    print(f"  ¿Cumple? {'✅ SÍ' if cumple else '❌ NO'}")
    
    return cumple

if __name__ == '__main__':
    print("🚀 [TEST] Iniciando prueba de nueva lógica de keywords...\n")
    
    resultado = test_nueva_logica_keywords()
    
    print(f"\n📊 [RESUMEN]")
    print(f"Nueva lógica flexible: {'✅ OK' if resultado else '❌ FALLO'}")
    
    if resultado:
        print("🎉 La nueva lógica debería permitir que se guarden más propiedades")
    else:
        print("⚠️ La nueva lógica aún necesita ajustes")
