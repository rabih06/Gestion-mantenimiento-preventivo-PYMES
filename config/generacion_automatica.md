# 🤖 Generación Automática de Órdenes de Trabajo

Este sistema genera automáticamente Órdenes de Trabajo (OTs) preventivas
a partir de los planes de mantenimiento configurados en la aplicación.

## 📋 ¿Cómo funciona?

1. Cada plan de mantenimiento tiene una **frecuencia** (días, uso, etc.) y
   una **próxima ejecución** calculada automáticamente.
2. Cuando la fecha de próxima ejecución se cumple, el sistema crea una OT
   preventiva y asigna el técnico responsable del plan.
3. El plan se reprograma automáticamente para la siguiente fecha.

## 🚀 Ejecución Manual desde la UI

### Preview (sin generar nada)
1. Ir al **Dashboard Admin**.
2. Clic en **Preview** en la tarjeta "Generación Automática de OTs".
3. Ver la lista de planes que se procesarían.
4. Filtrar por días hacia adelante (0, 1, 3, 7, 15, 30).
5. Si todo se ve bien, clic en **"Ejecutar Generación"**.

### Ejecución directa
1. Ir al **Dashboard Admin**.
2. Clic en **"Ejecutar Ahora"** en la tarjeta.
3. Confirmar la acción.

## 💻 Ejecución desde la Terminal

### Comando básico
```bash
python manage.py generar_ots_automaticas