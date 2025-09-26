"""
Comando para crear usuario de testing con límites ilimitados
"""
from django.core.management.base import BaseCommand
from core.models import Inmobiliaria, Usuario
from core.plans import aplicar_configuracion_plan


class Command(BaseCommand):
    help = 'Crea un usuario de testing con límites ilimitados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='testing@example.com',
            help='Email del usuario de testing'
        )
        parser.add_argument(
            '--nombre',
            type=str,
            default='Testing User',
            help='Nombre del usuario de testing'
        )
        parser.add_argument(
            '--inmobiliaria',
            type=str,
            default='Testing Corp',
            help='Nombre de la inmobiliaria de testing'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        nombre = options['nombre']
        inmobiliaria_nombre = options['inmobiliaria']
        
        # Crear o actualizar inmobiliaria de testing
        inmobiliaria, created = Inmobiliaria.objects.get_or_create(
            nombre=inmobiliaria_nombre,
            defaults={'plan': 'testing'}
        )
        
        # Aplicar configuración del plan testing
        inmobiliaria = aplicar_configuracion_plan(inmobiliaria, 'testing')
        inmobiliaria.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Inmobiliaria "{inmobiliaria_nombre}" creada con plan testing')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Inmobiliaria "{inmobiliaria_nombre}" ya existía, actualizada a plan testing')
            )
        
        # Crear o actualizar usuario de testing
        usuario, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'nombre': nombre,
                'password_hash': 'testing123',  # Password simple para testing
                'inmobiliaria': inmobiliaria
            }
        )
        
        if not created:
            # Actualizar usuario existente
            usuario.nombre = nombre
            usuario.inmobiliaria = inmobiliaria
            usuario.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario de testing creado: {email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Usuario {email} ya existía, actualizado')
            )
        
        # Mostrar información del usuario creado
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.HTTP_INFO('USUARIO DE TESTING CONFIGURADO'))
        self.stdout.write('='*50)
        self.stdout.write(f'Email: {usuario.email}')
        self.stdout.write(f'Nombre: {usuario.nombre}')
        self.stdout.write(f'Inmobiliaria: {inmobiliaria.nombre}')
        self.stdout.write(f'Plan: {inmobiliaria.plan}')
        self.stdout.write(f'Límites:')
        self.stdout.write(f'  - Intervalo actualización: {inmobiliaria.intervalo_actualizacion_horas}h')
        self.stdout.write(f'  - Max actualizaciones/día: {inmobiliaria.max_actualizaciones_por_dia}')
        self.stdout.write(f'  - Max búsquedas nuevas/día: {inmobiliaria.max_busquedas_nuevas_por_dia}')
        self.stdout.write('='*50)
        
        # Mostrar instrucciones
        self.stdout.write('\n' + self.style.HTTP_INFO('INSTRUCCIONES:'))
        self.stdout.write('1. Usa este usuario para hacer testing sin límites')
        self.stdout.write('2. Alternativamente, configura BUSCADOR_TESTING_MODE=true en el entorno')
        self.stdout.write('3. Para iniciar servidor: .\.venv\Scripts\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application')
        self.stdout.write('4. Accede a: http://localhost:10000')