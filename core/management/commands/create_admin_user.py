# core/management/commands/create_admin_user.py
"""
Comando para crear un usuario administrador usando el modelo personalizado Usuario
"""

from django.core.management.base import BaseCommand
from core.models import Usuario, Inmobiliaria
import getpass


class Command(BaseCommand):
    help = 'Crea un usuario administrador'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=str,
            help='Nombre del usuario administrador',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email del usuario administrador',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔐 Creando usuario administrador...')
        
        # Obtener o crear inmobiliaria por defecto
        inmobiliaria, created = Inmobiliaria.objects.get_or_create(
            nombre='Administración',
            defaults={'plan': 'premium'}
        )
        
        if created:
            self.stdout.write('✅ Inmobiliaria "Administración" creada')
        
        # Obtener datos del usuario
        nombre = options['nombre']
        if not nombre:
            nombre = input('Nombre de usuario: ')
        
        email = options['email'] 
        if not email:
            email = input('Email: ')
        
        # Verificar si ya existe
        if Usuario.objects.filter(nombre=nombre).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ El usuario "{nombre}" ya existe')
            )
            return
        
        if Usuario.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ El email "{email}" ya está en uso')
            )
            return
        
        # Crear usuario
        try:
            usuario = Usuario.objects.create(
                nombre=nombre,
                email=email,
                inmobiliaria=inmobiliaria
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario administrador "{nombre}" creado exitosamente')
            )
            
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🏢 Inmobiliaria: {inmobiliaria.nombre}')
            self.stdout.write(f'🆔 ID: {usuario.id}')
            
            # Mostrar estadísticas
            total_usuarios = Usuario.objects.count()
            self.stdout.write(f'\n📊 Total de usuarios en el sistema: {total_usuarios}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando usuario: {e}')
            )
