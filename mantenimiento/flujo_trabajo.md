# 📋 Flujo de Trabajo de Incidencias

## Estados

| Estado | Significado |
|--------|-------------|
| **PENDIENTE** | Recién reportada por un operario, sin evaluar |
| **REVISIÓN** | Alguien la está evaluando o tiene una OT en curso |
| **RESUELTA** | El problema se solucionó y fue aprobado por el admin |
| **RECHAZADA** | No es válida (falsa alarma, duplicada, etc.) |

## Diagrama de Flujo
Operario reporta falla
↓
┌─────────────┐
│ PENDIENTE │
└─────────────┘
↓ Admin/Técnico revisa
┌─────────────┐
│ REVISIÓN │ ← Se crea OT desde la incidencia
└─────────────┘
↓ Técnico inicia la OT
┌─────────────┐
│ REVISIÓN │ (sigue igual)
└─────────────┘
↓ Técnico completa la OT
┌─────────────┐
│ REVISIÓN │ (esperando aprobación del admin)
└─────────────┘
↓ Admin cierra la OT (aprobación)
┌─────────────┐
│ RESUELTA │ ✅ Automático
└─────────────┘                                                                                            

## Permisos por Rol

| Acción | Operario | Técnico | Admin |
|--------|:--------:|:-------:|:-----:|
| Crear incidencia | ✅ | ✅ | ✅ |
| Pasar a REVISIÓN | ❌ | ✅ | ✅ |
| Crear OT desde incidencia | ❌ | ❌ | ✅ |
| Marcar como RESUELTA (sin OT) | ❌ | ✅ | ✅ |
| Marcar como RECHAZADA | ❌ | ❌ | ✅ |
| Reabrir (volver a PENDIENTE) | ❌ | ❌ | ✅ |
| Cerrar OT y resolver incidencia | ❌ | ❌ | ✅ |

## Reglas de Negocio

1. **Una incidencia con OT vinculada no puede marcarse RESUELTA manualmente.**
   Se resuelve automáticamente al cerrar la OT.

2. **Solo el admin puede RECHAZAR incidencias.**
   Es una decisión de gestión sensible.

3. **No se puede reabrir una incidencia con OT activa.**
   Primero se debe cancelar la OT.

4. **El ciclo completo se cierra cuando el admin aprueba la OT.**
   Así hay doble verificación: técnico ejecuta + admin valida.

## KPIs derivados

| Métrica | Fórmula |
|---------|---------|
| Tiempo de respuesta | fecha_OT_creada - fecha_incidencia |
| Tiempo de resolución | fecha_cierre_OT - fecha_OT_creada |
| Tasa de rechazo | Incidencias rechazadas / Total incidencias |
| Tasa de conversión | Incidencias con OT / Total incidencias |