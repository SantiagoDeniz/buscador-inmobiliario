#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

# Juntar todos los archivos estáticos en la carpeta /staticfiles/
python manage.py collectstatic --noinput

# Iniciar el servidor web
python manage.py runserver 0.0.0.0:10000