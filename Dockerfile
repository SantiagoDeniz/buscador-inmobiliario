# Usamos una imagen oficial de Python
FROM python:3.10-slim

# Evita que apt-get pida confirmaciones
ENV DEBIAN_FRONTEND=noninteractive

# Instalamos dependencias del sistema, incluyendo Chrome
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    # Dependencias de Google Chrome
    libu2f-udev \
    libvulkan1 \
    --no-install-recommends

# Descargamos e instalamos Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN rm google-chrome-stable_current_amd64.deb

# Creamos un directorio para la app
WORKDIR /app

# Copiamos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY . .

# Comando para iniciar la aplicación (Render usará el puerto 10000)
CMD ["/bin/sh", "-c", "python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:10000"]