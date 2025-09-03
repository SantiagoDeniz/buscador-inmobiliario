import argparse
from django.core.management.base import BaseCommand, CommandError
from django.core.management import get_commands, load_command_class, call_command


class Command(BaseCommand):
    help = (
        'Herramienta unificada para listar/borrar datos de distintas tablas. '
        'Usa: manage.py dbtool <recurso> -- <flags del recurso>\n'
        'Recursos: propiedades, usuarios, plataformas, inmobiliarias, resultados, palabras.'
    )

    RECURSOS = {
        'propiedades': 'properties',
        'usuarios': 'usuarios',
        'plataformas': 'plataformas',
        'inmobiliarias': 'inmobiliarias',
        'resultados': 'resultados',
        'palabras': 'palabras',
    }

    def add_arguments(self, parser):
        parser.add_argument('recurso', choices=self.RECURSOS.keys(), help='Tabla/ámbito a operar.')
        parser.add_argument('extras', nargs=argparse.REMAINDER,
                            help='Flags del comando específico. Usa "--" para separar.')

    def handle(self, *args, **options):
        recurso = options['recurso']
        extras = options.get('extras') or []
        cmd_name = self.RECURSOS[recurso]

        # Localizar app del comando destino
        commands = get_commands()
        if cmd_name not in commands:
            raise CommandError(f'Comando destino no encontrado: {cmd_name}')
        app_name = commands[cmd_name]

        # Instanciar y crear parser del comando destino
        target_cmd = load_command_class(app_name, cmd_name)
        target_parser = target_cmd.create_parser('manage.py', cmd_name)

        # Si no hay extras o solo piden ayuda, mostrar ayuda del comando destino
        if not extras or any(flag in extras for flag in ('-h', '--help')):
            self.stdout.write(target_parser.format_help())
            return

        # Parsear flags extra usando el parser del comando destino
        try:
            parsed = target_parser.parse_args(extras)
        except SystemExit as e:
            # argparse puede llamar a sys.exit en errores; convertir a CommandError
            raise CommandError('Error al parsear flags del recurso. Revisa la ayuda.') from e

        # Ejecutar el comando destino con las opciones parseadas
        opts_dict = vars(parsed)
        call_command(cmd_name, **opts_dict)
