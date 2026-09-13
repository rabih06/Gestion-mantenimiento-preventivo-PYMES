# 🛠️ Sistema de Gestión de Mantenimiento Preventivo para PYMES

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Descripción

Este proyecto consiste en un **sistema offline** de gestión de mantenimiento preventivo para **Pequeñas y Medianas Empresas (PYMES)**. Permite registrar maquinaria, programar mantenimientos según intervalos del fabricante, gestionar órdenes de trabajo, controlar inventario de repuestos y generar reportes de estado. Está diseñado para funcionar en **redes locales (intranet)** sin necesidad de conexión a Internet, garantizando la disponibilidad incluso en entornos con conectividad limitada.

> **Objetivo principal:** Reducir costos de reparación, minimizar tiempos de inactividad y alargar la vida útil de los activos industriales y comerciales.

## 🚀 Características principales

- ✅ **Registro completo de maquinaria** (marca, modelo, serie, fecha de compra, intervalos de mantenimiento).
- 📅 **Programación automática** de mantenimientos preventivos con alertas de vencimiento.
- 🔧 **Gestión de órdenes de trabajo** (preventivas, correctivas, de emergencia).
- 🧾 **Control de inventario de repuestos** con alertas de stock mínimo.
- 🏢 **Directorio de proveedores** y generación de órdenes de compra.
- 📊 **Panel de indicadores (Dashboard)** con KPIs como MTBF, MTTR y disponibilidad.
- 👥 **Múltiples roles de usuario** (administrador, técnico, operario) con permisos diferenciados.
- 🌐 **Funcionamiento offline** (servidor local en LAN) – sin dependencia de Internet.
- 🖥️ **Interfaz web responsive** accesible desde cualquier navegador en la red local.

## 🧰 Tecnologías utilizadas

| Capa | Tecnología |
|------|------------|
| **Backend** | Python 3.12+, Django 5.0+ |
| **Base de Datos** | PostgreSQL 16+ |
| **Frontend** | HTML5, CSS3, Bootstrap 5 (con plantillas Django) |
| **Servidor** | Gunicorn / Waitress (para producción) |
| **Control de versiones** | Git + GitHub |

## 📋 Requisitos previos

Antes de empezar, asegúrate de tener instalado en tu máquina:

- **Python 3.12 o superior** ([Descargar](https://www.python.org/downloads/))
- **PostgreSQL 16 o superior** ([Descargar](https://www.postgresql.org/download/))
- **Git** (opcional, para clonar el repositorio)
- Un editor de código (recomendado: VS Code, PyCharm)

## 🔧 Instalación y configuración

Sigue estos pasos para tener el entorno de desarrollo funcionando en tu equipo.

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/sistema-mantenimiento-pymes.git
cd sistema-mantenimiento-pymes

2. Crear y activar un entorno virtual
bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
3. Instalar las dependencias
bash
pip install -r requirements.txt
Si no tienes el archivo requirements.txt, créalo con pip freeze > requirements.txt después de instalar Django y psycopg2.

4. Configurar la base de datos PostgreSQL
Abre tu cliente de PostgreSQL (pgAdmin o psql) y crea una base de datos:

sql
CREATE DATABASE mantenimiento_db;
Crea un usuario y asígnale permisos (opcional, pero recomendado):

sql
CREATE USER pymes_user WITH PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE mantenimiento_db TO pymes_user;
5. Configurar las variables de entorno
Crea un archivo .env en la raíz del proyecto (o configura directamente en settings.py) con los siguientes datos:

env
DB_NAME=mantenimiento_db
DB_USER=pymes_user
DB_PASSWORD=tu_contraseña_segura
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=tu_clave_secreta_django
DEBUG=True
Importante: Nunca subas el archivo .env a GitHub; inclúyelo en .gitignore.

6. Actualizar settings.py
Asegúrate de que la configuración de la base de datos en config/settings.py use las variables de entorno (ejemplo con python-dotenv). Si prefieres no usar .env, puedes escribir los valores directamente (no recomendado para producción).

7. Realizar las migraciones
bash
python manage.py makemigrations
python manage.py migrate
8. Crear un superusuario (administrador)
bash
python manage.py createsuperuser
Sigue las instrucciones para ingresar nombre de usuario, correo y contraseña.

9. Ejecutar el servidor de desarrollo
bash
python manage.py runserver
Abre tu navegador y ve a http://127.0.0.1:8000/. ¡El sistema debería estar funcionando!

Para acceder al panel de administración de Django, ingresa a http://127.0.0.1:8000/admin/ con las credenciales del superusuario.

📂 Estructura del proyecto (básica)
text
sistema-mantenimiento-pymes/
├── config/                 # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── maquinas/               # Aplicación principal (gestión de activos)
│   ├── models.py           # Modelos: Maquina, Mantenimiento, Repuesto, etc.
│   ├── views.py            # Lógica de negocio (vistas)
│   ├── admin.py            # Configuración del panel de admin
│   └── templates/          # Plantillas HTML
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
├── media/                  # Archivos subidos por usuarios (opcional)
├── manage.py
├── requirements.txt        # Dependencias del proyecto
├── .env                    # Variables de entorno (no subir a GitHub)
├── .gitignore
└── README.md
🖥️ Uso básico
Registrar maquinaria: Desde el panel de administración o la interfaz personalizada, agrega los equipos con sus datos técnicos.

Programar mantenimientos: Define intervalos (días, horas de uso) y el sistema generará alertas automáticas.

Gestionar órdenes de trabajo: Crea órdenes, asígnalas a técnicos y registra el tiempo y repuestos utilizados.

Controlar inventario: Lleva el stock de repuestos y recibe notificaciones cuando algún repuesto crítico esté por agotarse.

Consultar reportes: Visualiza el dashboard con indicadores de disponibilidad, MTBF y costos acumulados.

🤝 Contribución
Las contribuciones son bienvenidas. Si deseas mejorar el proyecto:

Haz un fork del repositorio.

Crea una rama para tu funcionalidad (git checkout -b feature/nueva-funcionalidad).

Realiza tus cambios y haz commit (git commit -m 'Agrega nueva funcionalidad').

Sube tus cambios (git push origin feature/nueva-funcionalidad).

Abre un Pull Request describiendo tus cambios.

🗺️ Roadmap (Futuras mejoras)
□ Módulo de reportes avanzados con gráficos interactivos.
□ Integración con sensores IoT para mantenimiento predictivo.
□ Sincronización opcional con la nube (modo híbrido).
□ Aplicación móvil nativa para técnicos de campo.
□ Soporte para múltiples empresas (SaaS multi-tenant).
📄 Licencia
Este proyecto está bajo la licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente, siempre que se incluya el aviso de copyright original.

👥 Autores
Rabih Bazi – @rabihbazi

Augusto Vielma – @augustovielma

Daniela Velásquez – @danielavelasquez

Daniel Rodríguez – @danielrodriguez

📧 ¿Preguntas o sugerencias? Abre un issue en el repositorio o contáctanos directamente.
