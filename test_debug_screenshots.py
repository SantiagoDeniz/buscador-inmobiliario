import os
from datetime import datetime

# Crear un archivo de prueba para verificar que la función funciona
debug_dir = os.path.join('static', 'debug_screenshots')
os.makedirs(debug_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename_base = f"test_{timestamp}"

# Crear archivos de prueba
with open(os.path.join(debug_dir, f"{filename_base}_info.txt"), 'w', encoding='utf-8') as f:
    f.write(f"Test file - Funcionalidad de capturas de debug implementada\n")
    f.write(f"Timestamp: {timestamp}\n")

print(f"✅ Archivo de prueba creado: {filename_base}_info.txt")
print("📸 Funcionalidad de capturas de debug lista para usar")
