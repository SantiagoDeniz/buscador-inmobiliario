# 🏠 Buscador Inmobiliario Inteligente

**Automatiza tu búsqueda de propiedades con inteligencia artificial**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.1](https://img.shields.io/badge/django-5.1-green.svg)](https://djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![WebSocket](https://img.shields.io/badge/WebSocket-Tiempo%20Real-orange.svg)]()

---

## 🎯 ¿Qué es?

**Buscador Inmobiliario Inteligente** es una aplicación web que revoluciona la forma de buscar propiedades inmobiliarias. Utiliza inteligencia artificial para interpretar búsquedas en lenguaje natural y automatiza el proceso de scraping de MercadoLibre Uruguay, mostrando resultados organizados en tiempo real.

### ✨ **Características Principales**

- 🤖 **Búsqueda con IA**: Escribe en lenguaje natural y la IA completa automáticamente los filtros
- ⚡ **Tiempo real**: Ve el progreso de tu búsqueda en vivo con WebSockets
- 💾 **Búsquedas guardadas**: Guarda tus búsquedas favoritas y re-ejecútalas cuando quieras
- 🎯 **Filtrado inteligente**: Encuentra propiedades con keywords específicas (luminoso, terraza, garage)
- 📊 **Resultados organizados**: Separación clara entre propiedades nuevas y ya encontradas
- 📱 **Responsive**: Funciona perfectamente en desktop, tablet y móvil

---

## 🚀 Instalación Rápida

### Requisitos Previos
- **Python 3.10+** ([Descargar aquí](https://www.python.org/downloads/))
- **Git** ([Descargar aquí](https://git-scm.com/downloads))

### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/buscador-inmobiliario.git
cd buscador-inmobiliario
```

### 2️⃣ Crear Entorno Virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar Base de Datos
```bash
python manage.py migrate
```

### 5️⃣ Ejecutar la Aplicación
```bash
python manage.py runserver
```

**¡Listo!** Abre tu navegador en **http://localhost:8000**

---

## 🔧 Configuración Opcional

### 🤖 **Búsqueda con IA (Recomendado)**

Para habilitar las búsquedas inteligentes con IA:

1. **Obtén una clave gratuita** de Google AI Studio: https://aistudio.google.com/
2. **Configura la variable de entorno**:
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="tu_clave_aqui"
   
   # Linux/Mac
   export GEMINI_API_KEY="tu_clave_aqui"
   ```
3. **Opcional**: Crea un archivo `.env` en la raíz del proyecto:
   ```
   GEMINI_API_KEY=tu_clave_aqui
   ```

### 📊 **Redis para Mejor Performance (Opcional)**

Para mejor performance en producción:

1. **Instala Redis**:
   - Windows: https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt install redis-server`
   - Mac: `brew install redis`

2. **Configura la variable**:
   ```bash
   # Local
   REDIS_URL=redis://localhost:6379
   
   # Upstash (cloud)
   REDIS_URL=rediss://usuario:password@host:port
   ```

---

## 🎮 Cómo Usar

### 🔍 **Búsqueda Básica**

1. **Escribe tu búsqueda** en lenguaje natural:
   - *"Apartamento 2 dormitorios Pocitos hasta 180 mil dólares"*
   - *"Casa con garage en Punta del Este"*
   - *"Oficina luminosa zona centro"*

2. **La IA completa automáticamente** los filtros

3. **Elige tu acción**:
   - **"Buscar"**: Búsqueda temporal (no se guarda en la lista)
   - **"Buscar y Guardar"**: Se guarda en tu lista de búsquedas

### 📊 **Panel de Progreso**

Mientras se ejecuta la búsqueda, verás:
- ✅ **Fases del proceso**: Análisis IA → Construcción URL → Recolección → Extracción
- 📈 **Métricas en tiempo real**: Propiedades encontradas, nuevas, existentes
- 🎯 **Coincidencias de keywords**: Cuántas palabras clave coinciden
- ⏱️ **Tiempo estimado**: Progreso y tiempo restante

### 🏠 **Resultados**

Los resultados se organizan en:
- **✨ Nuevas Propiedades**: Que no habías visto antes
- **🔄 Encontradas Anteriormente**: Que ya aparecieron en búsquedas pasadas

Cada propiedad muestra:
- 🖼️ Imagen principal
- 🏠 Título y descripción
- 📍 Ubicación (departamento, ciudad, barrio)
- 💰 Precio (USD/UYU)
- 🛏️ Características (dormitorios, baños, superficie)
- 🔗 Enlace directo a MercadoLibre

### 💾 **Búsquedas Guardadas**

En tu lista de búsquedas guardadas puedes:
- 👀 **Ver resultados** de búsquedas anteriores
- 🔄 **Re-ejecutar** la misma búsqueda para encontrar nuevas propiedades
- 🗑️ **Eliminar** búsquedas que ya no necesitas

---

## 🎯 Casos de Uso

### 👤 **Usuario Casual**
- Busca su primera vivienda
- Explora diferentes zonas y precios
- Descubre propiedades que cumplan criterios específicos

### 🏢 **Agente Inmobiliario**
- Gestiona búsquedas para múltiples clientes
- Monitorea nuevas propiedades en el mercado
- Mantiene un portfolio de búsquedas organizadas

### 📊 **Inversor/Analista**
- Analiza tendencias de precios por zona
- Monitorea oportunidades de inversión
- Exporta datos para análisis externos

---

## 🛠️ Troubleshooting

### ❌ **Problemas Comunes**

#### **"La búsqueda no encuentra propiedades"**
- ✅ Revisa que los filtros no sean demasiado restrictivos
- ✅ Prueba con menos keywords específicas
- ✅ Verifica que la zona seleccionada tenga propiedades disponibles

#### **"La IA no funciona"**
- ✅ Verifica que `GEMINI_API_KEY` esté configurada correctamente
- ✅ La búsqueda funciona sin IA, solo sin completado automático

#### **"La búsqueda va muy lenta"**
- ✅ Es normal: el scraping responsable toma 1-3 minutos
- ✅ Puedes detener la búsqueda en cualquier momento
- ✅ Para mayor velocidad, considera configurar Redis

#### **"Error de conexión"**
- ✅ Verifica tu conexión a internet
- ✅ MercadoLibre puede estar temporalmente inaccesible
- ✅ Reinicia la aplicación si persiste el error

### 🔧 **Comandos Útiles**

```bash
# Reiniciar base de datos
python manage.py migrate --run-syncdb

# Ver logs detallados
python manage.py runserver --verbosity=2

# Ejecutar tests
python manage.py test

# Crear usuario administrador
python manage.py createsuperuser
```

---

## 📊 Limitaciones y Consideraciones

### ⚖️ **Legal**
- ✅ Respeta robots.txt de MercadoLibre
- ✅ Implementa delays entre requests
- ✅ Solo extrae datos públicos disponibles
- ⚠️ Úsalo de forma responsable y ética

### 🔒 **Técnicas**
- 📊 **Datos**: Solo propiedades de MercadoLibre Uruguay
- ⏱️ **Velocidad**: 1-3 minutos por búsqueda (scraping responsable)
- 💾 **Almacenamiento**: SQLite local (datos en tu computadora)
- 🌐 **Internet**: Requiere conexión para scraping

---

## 🚀 Para Desarrolladores

¿Quieres contribuir o personalizar el sistema?

- 📚 **[Documentación Técnica](DOCUMENTACION_TECNICA.md)**: Arquitectura y APIs internas
- 🛠️ **[Guía de Contribución](CONTRIBUTING.md)**: Cómo contribuir al proyecto
- 🐳 **[Deployment](DEPLOYMENT.md)**: Guía para producción
- 🔧 **[Funcionalidades](core/Funcionalidades.md)**: Detalles de características

---

## 📝 Licencia

Este proyecto está bajo la **Licencia MIT**. Eres libre de usar, modificar y distribuir el código.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. 🍴 Haz fork del proyecto
2. 🌿 Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push a la rama (`git push origin feature/AmazingFeature`)
5. 🔃 Abre un Pull Request

---

## 📞 Soporte

- 🐛 **Reportar bugs**: Abre un [issue en GitHub](../../issues)
- 💡 **Sugerencias**: Comparte tus ideas en [discussions](../../discussions)
- 📧 **Contacto directo**: [tu-email@ejemplo.com]

---

## 🌟 ¿Te gusta el proyecto?

Si este proyecto te resulta útil, considera:
- ⭐ Darle una estrella en GitHub
- 🔄 Compartirlo con otros desarrolladores
- 💡 Contribuir con mejoras
- 📝 Escribir sobre tu experiencia

---

*Desarrollado con ❤️ para automatizar la búsqueda inmobiliaria*