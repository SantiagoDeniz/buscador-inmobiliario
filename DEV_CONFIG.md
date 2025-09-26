# Configuración del entorno de desarrollo
# Este archivo documenta el setup preferido para este proyecto

## Servidor de desarrollo
SERVIDOR_COMANDO=".\\.venv\\Scripts\\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application"
SERVIDOR_URL="http://localhost:10000"
SERVIDOR_PUERTO=10000

## Razones para usar Daphne
# - Soporte nativo para WebSockets (usado en sistema de progreso)
# - Mejor compatibilidad con Django Channels
# - Configuración específica para este proyecto

## Comandos frecuentes
# Iniciar servidor: .\\.venv\\Scripts\\activate ; daphne -b 0.0.0.0 -p 10000 buscador.asgi:application
# Crear usuario testing: python manage.py create_testing_user
# Tests: python manage.py test core.tests_database -v 2
# Migraciones: python manage.py makemigrations core && python manage.py migrate

## Configuración de Límites
# DESARROLLO: Plan "testing" por defecto (sin límites)
# Usuario: testing@example.com con límites ilimitados
# PRODUCCIÓN: Cambiar a planes reales cuando se solicite específicamente

## Endpoints importantes
# Home: http://localhost:10000
# Verificar límites: http://localhost:10000/verificar_limites/
# Estado actualizaciones: http://localhost:10000/estado_actualizaciones/
# Debug screenshots: http://localhost:10000/debug_screenshots/