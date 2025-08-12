# Test manual para procesar_keywords
from core.search_manager import procesar_keywords

print('Test: "4 dormitorios 3 baños"')
print(procesar_keywords('4 dormitorios 3 baños'))

print('Test: "4 dormitorios, 3 baños"')
print(procesar_keywords('4 dormitorios, 3 baños'))

print('Test: "apartamento 2 dormitorios malvin frente al mar"')
print(procesar_keywords('apartamento 2 dormitorios malvin frente al mar'))
