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
