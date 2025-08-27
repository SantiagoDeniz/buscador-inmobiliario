# Crear usuario administrador
from core.models import Usuario, Inmobiliaria

# Crear inmobiliaria admin si no existe
inmobiliaria, created = Inmobiliaria.objects.get_or_create(
    nombre='Administración',
    defaults={'plan': 'premium'}
)

if created:
    print('✅ Inmobiliaria "Administración" creada')

# Crear usuario admin
usuario, created = Usuario.objects.get_or_create(
    nombre='admin',
    defaults={
        'email': 'admin@buscador.com',
        'inmobiliaria': inmobiliaria
    }
)

if created:
    print('✅ Usuario admin creado exitosamente')
    print(f'📧 Email: {usuario.email}')
    print(f'🏢 Inmobiliaria: {usuario.inmobiliaria.nombre}')
    print(f'🆔 ID: {usuario.id}')
else:
    print('⚠️ Usuario admin ya existe')

print(f'📊 Total usuarios: {Usuario.objects.count()}')
print('🎯 Puedes usar este usuario para acceder al sistema')
