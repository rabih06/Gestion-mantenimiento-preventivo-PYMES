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

¡Gracias por tu interés en este proyecto! 🚀

text

---

### 🧾 Instrucciones para usar este README

1. **Copia todo el contenido** del bloque de código anterior.
2. **Pégalo** en un archivo llamado `README.md` en la raíz de tu repositorio.
3. **Reemplaza** `tu-usuario` y los enlaces de los autores por los reales.
4. **Ajusta** la sección de instalación si usas otra configuración (por ejemplo, si no usas `.env`).
5. **Sube** el archivo a GitHub junto con el resto del código.

Este README es claro, profesional y cubre todos los aspectos que cualquier desarrollador o evaluador necesita para entender y poner en marcha tu sistema. ¿Te gusta cómo quedó? ¿Quieres que añada o cambie algo? 😊
esto me salio al migrar
El error es claro: Django no encuentra el módulo psycopg2 ni psycopg. Necesita instalar el adaptador de PostgreSQL. Le explicaré cómo solucionarlo.

¡Tranquilo, es un error muy común y fácil de solucionar! Lo que pasa es que Django no encuentra el adaptador de PostgreSQL (psycopg2 o psycopg). Esto significa que no se instaló correctamente en tu entorno virtual.

Vamos a resolverlo paso a paso.

🔍 ¿Por qué pasó esto?
El error dice claramente:

text
ModuleNotFoundError: No module named 'psycopg'
ModuleNotFoundError: No module named 'psycopg2'
django.core.exceptions.ImproperlyConfigured: Error loading psycopg2 or psycopg module
Django intenta conectarse a PostgreSQL, pero no encuentra la librería que hace de "puente" entre Python y PostgreSQL. Esto puede pasar por dos razones:

No instalaste psycopg2 (o lo instalaste fuera del entorno virtual).

Lo instalaste, pero en el Python global, no dentro del venv.

✅ Solución paso a paso
1. Verifica que el entorno virtual esté activado
En tu terminal debe aparecer (venv) al inicio de la línea:

text
(venv) PS C:\Users\lenovo\OneDrive\Desktop\PYMEs\.venv>
✅ Sí está activado. Bien.

2. Instala el adaptador de PostgreSQL
Ejecuta este comando dentro del entorno virtual:

bash
pip install psycopg2-binary
¿Por qué psycopg2-binary y no psycopg2?
La versión -binary ya viene precompilada, así que no necesitas instalar herramientas de compilación de C en Windows. Es la opción recomendada para desarrollo.

Si por alguna razón falla, puedes probar con la versión moderna:

bash
pip install "psycopg[binary]"
3. Verifica que se instaló correctamente
bash
pip list
Busca psycopg2-binary en la lista. Debería aparecer algo así:

text
psycopg2-binary    2.9.9
4. Vuelve a ejecutar la migración
bash
python manage.py migrate
🛠️ Si el error persiste, prueba esto:
Opción A: Reinstalar desde cero
A veces una instalación corrupta causa problemas. Fuerza la reinstalación:

bash
pip uninstall psycopg2-binary -y
pip install psycopg2-binary
Opción B: Verificar que estás usando el Python del venv
A veces el pip que usas no es el del entorno virtual. Verifica con:

bash
where python
where pip
Ambos deben apuntar a la carpeta .venv. Si no, activa el entorno virtual correctamente:

bash
# Desde la raíz del proyecto
.venv\Scripts\activate
Opción C: Instalar psycopg (versión 3, la moderna)
Django 5.x soporta la versión 3 de psycopg. Si psycopg2-binary te da problemas, prueba:

bash
pip install "psycopg[binary]"
Y en tu settings.py, deja el engine igual:

python
'ENGINE': 'django.db.backends.postgresql',
Django detectará automáticamente psycopg (v3) o psycopg2.

📌 Resumen rápido
Paso	Comando
1. Activar venv	.venv\Scripts\activate
2. Instalar adaptador	pip install psycopg2-binary
3. Verificar	pip list
4. Migrar	python manage.py migrate
💡 Recomendación adicional
Para evitar que esto vuelva a pasar, crea un archivo requirements.txt con todas las dependencias:

bash
pip freeze > requirements.txt
Así, si otro integrante del equipo clona el repositorio, solo tiene que ejecutar:

bash
pip install -r requirements.txt
Y tendrá exactamente las mismas librerías que tú.

Prueba con pip install psycopg2-binary y cuéntame si la migración funciona. Si sale otro error, pásame el mensaje y lo resolvemos. 💪

2026-09-11 15:09:43.187 [error] Error refreshing packages Error spawning python: spawn c:\Users\lenovo\OneDrive\Desktop\PYMEs\venv\Scripts\python.exe ENOENT me salio este error al descargar la libreria
The user has an error in VS Code when trying to refresh packages: "Error spawning python: spawn c:\Users\lenovo\OneDrive\Desktop\PYMEs\venv\Scripts\python.exe ENOENT"

This means the venv path is wrong. Earlier the terminal showed .venv (with a dot), but this error references venv (without the dot). So VS Code is looking in the wrong folder.

Let me explain this clearly.

¡Ah, ese error es distinto pero muy fácil de explicar! El problema es que VS Code está buscando el entorno virtual en la carpeta equivocada.

🔍 ¿Qué significa este error?
text
Error spawning python: spawn c:\Users\lenovo\OneDrive\Desktop\PYMEs\venv\Scripts\python.exe ENOENT
ENOENT significa "Error NO ENTry" → "No existe esa ruta/archivo".

VS Code está buscando el Python del entorno virtual en:

text
C:\Users\lenovo\OneDrive\Desktop\PYMEs\venv\Scripts\python.exe
Pero tu entorno virtual está en:

text
C:\Users\lenovo\OneDrive\Desktop\PYMEs\.venv\Scripts\python.exe
👉 Fíjate en el detalle: VS Code busca venv (sin punto), pero tú creaste .venv (con punto al inicio).

Además, hay otro problema: tu venv está DENTRO de la carpeta .venv, lo cual es un error de estructura. Debería estar en la raíz del proyecto.

✅ Solución paso a paso
1. Verifica la estructura de tu proyecto
Abre una terminal y ejecuta:

bash
cd C:\Users\lenovo\OneDrive\Desktop\PYMEs
dir
Deberías ver algo así (estructura correcta):

text
manage.py
config\
.venv\
Pero según tu error, probablemente tienes algo así (estructura incorrecta):

text
.venv\
    manage.py
    venv\        ← ❌ Aquí está el problema
    config\
2. La solución más limpia: recrear el entorno virtual
Te recomiendo empezar de cero con la estructura correcta. Sigue estos pasos en orden:

Paso A: Sal del entorno virtual actual
bash
deactivate
Paso B: Elimina la carpeta .venv actual
Desde la raíz del proyecto:

bash
cd C:\Users\lenovo\OneDrive\Desktop\PYMEs
rmdir /s /q .venv
Si tienes manage.py dentro de .venv, muévelo primero a la raíz del proyecto.

Paso C: Verifica que manage.py esté en la raíz
Tu estructura debe verse así antes de crear el venv:

text
PYMEs\
├── manage.py       ← Aquí
├── config\
│   ├── settings.py
│   ├── urls.py
│   └── ...
Paso D: Crea el nuevo entorno virtual (en la raíz)
bash
python -m venv .venv
Paso E: Actívalo
bash
.venv\Scripts\activate
Deberías ver (.venv) al inicio:

text
(.venv) PS C:\Users\lenovo\OneDrive\Desktop\PYMEs>
Paso F: Instala las dependencias
bash
pip install django psycopg2-binary
3. Configurar VS Code para que use el entorno correcto
Una vez recreado el venv, haz esto en VS Code:

Presiona Ctrl + Shift + P para abrir la paleta de comandos.

Escribe Python: Select Interpreter y presiona Enter.

Aparecerá una lista. Busca y selecciona la que tenga la ruta:

text
.\.venv\Scripts\python.exe
Si no aparece, haz clic en "Enter interpreter path..." y navega manualmente hasta:

text
C:\Users\lenovo\OneDrive\Desktop\PYMEs\.venv\Scripts\python.exe
4. (Opcional) Configurar VS Code con un archivo de settings
Para que VS Code siempre use el entorno correcto, crea o edita el archivo .vscode/settings.json en la raíz de tu proyecto:

json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
    "python.terminal.activateEnvironment": true
}
Esto le dice a VS Code dónde está el intérprete y que lo active automáticamente en la terminal.

📌 Resumen visual de la estructura correcta
text
PYMEs\                          ← Raíz del proyecto
├── .venv\                      ← Entorno virtual (oculto, con punto)
│   ├── Scripts\
│   │   └── python.exe
│   └── Lib\
├── config\                     ← Configuración de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py                   ← En la raíz
├── requirements.txt
└── README.md
🎯 Pasos concretos para AHORA
Ejecuta estos comandos uno por uno en tu terminal:

bash
# 1. Ir a la carpeta raíz
cd C:\Users\lenovo\OneDrive\Desktop\PYMEs

# 2. Desactivar el venv actual (si está activo)
deactivate

# 3. Borrar la carpeta venv incorrecta
rmdir /s /q venv

# 4. Borrar también la .venv si está mal ubicada
rmdir /s /q .venv

# 5. Verificar que manage.py esté aquí
dir

# 6. Crear nuevo entorno virtual
python -m venv .venv

# 7. Activarlo
.venv\Scripts\activate

# 8. Instalar dependencias
pip install django psycopg2-binary

# 9. Verificar
pip list

# 10. Migrar
python manage.py migrate
🆘 Si algo no sale
Si al ejecutar dir ves que manage.py está dentro de .venv, primero muévelo manualmente con el Explorador de Windows a la raíz PYMEs\. Luego continúa con los pasos.

Cuéntame cómo te va con estos pasos. Si aparece otro error, pásame el mensaje completo y lo resolvemos. 💪

voy a borrar desde el explorador de windows todo y vuelvo a recrear el entorno virtual
We need to respond to the user's decision to delete everything from Windows Explorer and recreate the virtual environment. They want to start fresh. We should acknowledge, give them a clear step-by-step guide for a clean re-setup, ensuring proper structure and avoiding previous mistakes. Also, since they are using Windows, we can provide commands and tips. The user said "voy a borrar desde el explorador de windows todo y vuelvo a recrear el entorno virtual". So they are going to manually delete files. We need to guide them on what to delete exactly and how to recreate. Also, they might need to recreate the Django project? Possibly they want to keep the project files (manage.py, config folder) but delete the venv. Or they might want to start completely from scratch. They didn't specify. But likely they want to delete the faulty venv and maybe the whole project? We should clarify or give a robust plan: backup any important files, then delete everything in the project folder, then recreate the Django project and venv properly. But since they already have a Django project (manage.py, config), they might not want to lose that. However, the error was about venv location; the project itself is probably fine. So they can keep manage.py and config, just delete the .venv and any venv folder. But they said "borrar desde el explorador de windows todo" meaning delete everything. That could be risky. We should advise them to keep the project files if they want to avoid redoing the Django setup. But if they prefer a totally clean slate, we can guide them to recreate everything from scratch. We'll provide two options: Option A: Keep project files, just delete venv and recreate. Option B: Start completely from scratch (delete everything, create new project). We'll ask them to confirm, but also give clear steps for both. Since they already decided to delete everything, we can assume they want to start from zero. So we'll give a complete step-by-step to recreate from scratch: delete folder, create new folder, create venv, install Django, start project, configure settings, etc. But that might be overkill. Let's provide a comprehensive guide for a clean setup, including how to create the Django project properly. Also remind them to install PostgreSQL if not already, and create the database. We'll also mention that they can reuse the README they already have. And we'll include a checklist. The tone should be supportive and clear. We'll structure it as: 1. Backup anything important. 2. Delete the entire project folder from Windows Explorer. 3. Create a new folder. 4. Open terminal in that folder. 5. Create and activate venv. 6. Install Django and psycopg2-binary. 7. Create Django project. 8. Configure database. 9. Run migrations. 10. Create superuser. 11. Run server. Also mention setting up VS Code interpreter. We'll also include a note about requirements.txt. And maybe a quick verification. We'll end with encouragement. We'll write in Spanish.

¡Perfecto! Empezar de cero es a veces la mejor decisión para evitar arrastrar errores. Te voy a guiar paso a paso para que dejes todo funcionando correctamente desde el principio.

🧹 Paso 1: Borrar todo desde el Explorador de Windows
Cierra VS Code y cualquier terminal que esté abierta.

Abre el Explorador de Windows y navega hasta:

text
C:\Users\lenovo\OneDrive\Desktop\
Busca la carpeta PYMEs (o como la hayas llamado).

Bórrala por completo (Shift + Supr para que no quede en la papelera, o simplemente eliminar).

⚠️ Asegúrate de no tener nada importante dentro. Si tenías algún archivo que quieras conservar (como el README o apuntes), cópialo antes a otro lugar.

🆕 Paso 2: Crear la carpeta del proyecto desde cero
En el Escritorio, crea una nueva carpeta llamada PYMEs (o el nombre que prefieras).

Ábrela.

Haz clic derecho en un espacio vacío y selecciona "Abrir en Terminal" (o "Abrir en PowerShell").

Si no aparece esa opción, abre la terminal manualmente y navega con cd:

bash
cd C:\Users\lenovo\OneDrive\Desktop\PYMEs
🐍 Paso 3: Crear y activar el entorno virtual
Dentro de la terminal, ejecuta:

bash
python -m venv .venv
Luego actívalo:

bash
.venv\Scripts\activate
Deberías ver (.venv) al inicio de la línea de comandos:

text
(.venv) PS C:\Users\lenovo\OneDrive\Desktop\PYMEs>
✅ Importante: El punto antes de venv (.venv) es una convención para que la carpeta quede oculta y no se confunda con otras. Puedes usar venv sin punto si prefieres, pero mantén la consistencia.

📦 Paso 4: Instalar Django y el adaptador de PostgreSQL
Con el entorno virtual activado, ejecuta:

bash
pip install django psycopg2-binary
Espera a que termine. Luego verifica que se instalaron:

bash
pip list
Debes ver Django y psycopg2-binary en la lista.

🏗️ Paso 5: Crear el proyecto Django
Ahora crea la estructura base de Django. Ejecuta:

bash
django-admin startproject config .
Ojo: El punto . al final es clave. Le dice a Django que cree los archivos en la carpeta actual, no en una subcarpeta.

Tu estructura debe verse así:

text
PYMEs\
├── .venv\
├── manage.py
└── config\
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
🗄️ Paso 6: Configurar la base de datos PostgreSQL
6.1 Crear la base de datos en PostgreSQL
Abre pgAdmin o la terminal de PostgreSQL (psql) y ejecuta:

sql
CREATE DATABASE mantenimiento_db;
Si quieres crear un usuario dedicado (opcional pero recomendado):

sql
CREATE USER pymes_user WITH PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE mantenimiento_db TO pymes_user;
6.2 Editar config/settings.py
Abre el archivo config/settings.py con VS Code (o tu editor). Busca la sección DATABASES y reemplázala con:

python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mantenimiento_db',
        'USER': 'pymes_user',          # O 'postgres' si usas el usuario por defecto
        'PASSWORD': 'tu_contraseña_segura',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
🔐 Seguridad: No dejes la contraseña escrita directamente en el código si vas a subir esto a GitHub. Más adelante podemos usar variables de entorno.

🚀 Paso 7: Migrar y crear superusuario
Ejecuta las migraciones para crear las tablas iniciales:

bash
python manage.py migrate
Si todo va bien, verás algo como:

text
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  ...
Ahora crea un superusuario para el panel de administración:

bash
python manage.py createsuperuser
Ingresa un nombre de usuario, correo (opcional) y contraseña.

🖥️ Paso 8: Ejecutar el servidor
bash
python manage.py runserver
Abre tu navegador y ve a:

http://127.0.0.1:8000/ → Página de bienvenida de Django.

http://127.0.0.1:8000/admin/ → Panel de administración (inicia sesión con el superusuario).

⚙️ Paso 9: Configurar VS Code (para que no vuelva a fallar)
Abre VS Code en la carpeta del proyecto:

bash
code .
Presiona Ctrl + Shift + P → escribe Python: Select Interpreter → selecciona:

text
.\.venv\Scripts\python.exe
Crea un archivo .vscode/settings.json en la raíz del proyecto con:

json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
    "python.terminal.activateEnvironment": true
}
📝 Paso 10: Crear requirements.txt
Para que otros puedan instalar las mismas dependencias, ejecuta:

bash
pip freeze > requirements.txt
Esto generará un archivo con las versiones exactas de Django y psycopg2.

✅ Resumen de comandos (todo junto)
bash
# 1. Ir a la carpeta del proyecto
cd C:\Users\lenovo\OneDrive\Desktop\PYMEs

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
pip install django psycopg2-binary

# 4. Crear proyecto Django
django-admin startproject config .

# 5. Configurar base de datos en config/settings.py (manual)

# 6. Migrar
python manage.py migrate

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Ejecutar servidor
python manage.py runserver
🎯 Siguiente paso después de esto
Una vez que el servidor corra sin errores, el siguiente paso será crear tu primera aplicación para gestionar las máquinas:

bash
python manage.py startapp maquinas
Y luego definir los modelos (tablas) en maquinas/models.py.
