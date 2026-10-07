from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group

from .models import (
    Repuesto, Equipo, OrdenRepuesto, OrdenTrabajo,
    HistorialEstadoEquipo, Alerta, User, Incidencia
)
from .utils import notificar, notificar_operario_responsable


# =====================================================
# ALERTAS AUTOMÁTICAS DE STOCK
# =====================================================

@receiver(post_save, sender=Repuesto)
def alerta_stock_bajo(sender, instance, **kwargs):
    """Genera alerta cuando el stock cae por debajo del mínimo."""
    if instance.cantidad_actual <= instance.stock_minimo:
        notificar(
            tipo='STOCK_BAJO',
            mensaje=f"Stock bajo: {instance.nombre} ({instance.cantidad_actual} unidades, mínimo {instance.stock_minimo})",
            repuesto=instance,
            notificar_admins=True,
            notificar_tecnicos=True,
            evitar_duplicados_minutos=60 * 24,  # 24 horas
        )


# =====================================================
# CAMBIO DE ESTADO DE EQUIPO
# =====================================================

@receiver(pre_save, sender=Equipo)
def registrar_cambio_estado(sender, instance, **kwargs):
    """
    Registra el cambio de estado del equipo en el historial y
    genera notificaciones según el nuevo estado.
    """
    if not instance.pk:
        return
    
    try:
        anterior = Equipo.objects.get(pk=instance.pk)
    except Equipo.DoesNotExist:
        return
    
    if anterior.estado_operativo == instance.estado_operativo:
        return
    
    # ✅ Registrar en el historial
    HistorialEstadoEquipo.objects.create(
        equipo=instance,
        estado_anterior=anterior.estado_operativo,
        estado_nuevo=instance.estado_operativo,
        motivo="Cambio de estado",
    )
    
    # ✅ Notificar según el nuevo estado
    estado_display = instance.get_estado_operativo_display()
    
    if instance.estado_operativo == 'MANTENIMIENTO':
        notificar_operario_responsable(
            equipo=instance,
            tipo='EQUIPO_EN_MANTENIMIENTO',
            mensaje=f"El equipo {instance.codigo_interno} ({instance.nombre}) entró en mantenimiento.",
        )
    elif instance.estado_operativo == 'FUERA_SERVICIO':
        notificar_operario_responsable(
            equipo=instance,
            tipo='EQUIPO_FUERA_SERVICIO',
            mensaje=f"⚠️ El equipo {instance.codigo_interno} ({instance.nombre}) está FUERA DE SERVICIO.",
        )
    elif instance.estado_operativo == 'BAJA':
        notificar_operario_responsable(
            equipo=instance,
            tipo='EQUIPO_BAJA',
            mensaje=f"❌ El equipo {instance.codigo_interno} ({instance.nombre}) fue dado de BAJA.",
        )


# =====================================================
# INCIDENCIAS
# =====================================================

@receiver(post_save, sender=Incidencia)
def notificar_nueva_incidencia(sender, instance, created, **kwargs):
    """Notifica al admin (y técnicos) cuando se crea una nueva incidencia."""
    if not created:
        return
    
    prioridad = instance.get_prioridad_display()
    mensaje = (
        f"📢 Nueva incidencia [{prioridad}]: "
        f"{instance.equipo.codigo_interno} - {instance.descripcion_falla[:80]}"
    )
    
    notificar(
        tipo='NUEVA_INCIDENCIA',
        mensaje=mensaje,
        equipo=instance.equipo,
        notificar_admins=True,
        notificar_tecnicos=True,
        evitar_duplicados_minutos=0,  # No evitar duplicados (cada incidencia es única)
    )


@receiver(post_save, sender=Incidencia)
def alerta_incidencia_resuelta(sender, instance, **kwargs):
    """Notifica al operario cuando su incidencia se marca como RESUELTA."""
    if instance.estado != 'RESUELTA' or not instance.operario:
        return
    
    notificar(
        tipo='INCIDENCIA_RESUELTA',
        mensaje=(
            f"✅ Tu incidencia #{instance.id} fue resuelta: "
            f"{instance.equipo.codigo_interno}"
        ),
        equipo=instance.equipo,
        usuarios=[instance.operario],
    )


# =====================================================
# ÓRDENES DE TRABAJO - NOTIFICACIONES AL ADMIN
# =====================================================

@receiver(post_save, sender=OrdenTrabajo)
def notificar_cambio_estado_ot(sender, instance, created, **kwargs):
    """Notifica al admin cuando cambia el estado de una OT."""
    if created:
        return
    
    # Solo notificar en transiciones relevantes
    # Usamos el estado actual para decidir
    tecnico_nombre = instance.tecnico.get_full_name() if instance.tecnico else "Sin asignar"
    
    if instance.estado == 'PROGRESO':
        notificar(
            tipo='OT_INICIADA',
            mensaje=(
                f"🔧 {tecnico_nombre} inició la OT-{instance.id} "
                f"en {instance.equipo.codigo_interno}"
            ),
            equipo=instance.equipo,
            notificar_admins=True,
            evitar_duplicados_minutos=30,
        )
    elif instance.estado == 'COMPLETADA':
        notificar(
            tipo='OT_COMPLETADA',
            mensaje=(
                f"✅ {tecnico_nombre} completó la OT-{instance.id} "
                f"en {instance.equipo.codigo_interno} ({instance.duracion_horas}h)"
            ),
            equipo=instance.equipo,
            notificar_admins=True,
            evitar_duplicados_minutos=30,
        )


# =====================================================
# ÓRDENES DE REPUESTOS - LÓGICA DE PRECIOS Y COSTOS
# =====================================================

@receiver(post_save, sender=OrdenRepuesto)
def descontar_stock(sender, instance, created, **kwargs):
    """Descuenta el stock del repuesto al usarlo en una orden."""
    if created:
        repuesto = instance.repuesto
        repuesto.cantidad_actual -= instance.cantidad_utilizada
        repuesto.fecha_ultima_salida = instance.created_at
        repuesto.save()


@receiver(post_save, sender=OrdenRepuesto)
def rellenar_precio_si_falta(sender, instance, created, **kwargs):
    """Rellena el precio con el valor actual del repuesto si viene en 0."""
    if created and (not instance.precio_unitario_momento or instance.precio_unitario_momento == 0):
        instance.precio_unitario_momento = instance.repuesto.precio_unitario
        instance.save(update_fields=['precio_unitario_momento'])


@receiver([post_save, post_delete], sender=OrdenRepuesto)
def recalcular_costo_orden(sender, instance, **kwargs):
    """Recalcula el costo_total de la OT cuando se modifica un repuesto."""
    try:
        orden = instance.orden
        total = sum(r.subtotal for r in orden.repuestos_usados.all())
        orden.costo_total = total
        orden.save(update_fields=['costo_total'])
    except OrdenTrabajo.DoesNotExist:
        pass


# =====================================================
# ASIGNACIÓN DE GRUPOS POR ROL
# =====================================================

@receiver(post_save, sender=User)
def asignar_grupo_por_rol(sender, instance, **kwargs):
    """Asigna al usuario al grupo correspondiente según su rol_principal."""
    mapa_roles = {
        'ADMIN': 'Administradores',
        'TECNICO': 'Técnicos',
        'OPERARIO': 'Operarios',
    }
    nombre_grupo = mapa_roles.get(instance.rol_principal)
    if not nombre_grupo:
        return
    try:
        grupo = Group.objects.get(name=nombre_grupo)
    except Group.DoesNotExist:
        return
    grupos_rol = Group.objects.filter(
        name__in=['Administradores', 'Técnicos', 'Operarios']
    )
    instance.groups.remove(*grupos_rol)
    instance.groups.add(grupo)


# =====================================================
# SINCRONIZACIÓN INCIDENCIA ↔ ORDEN DE TRABAJO
# =====================================================

@receiver(post_save, sender=OrdenTrabajo)
def actualizar_incidencia_al_cerrar_orden(sender, instance, **kwargs):
    """
    Cuando el admin cierra una OT (fecha_cierre) y esta tiene una incidencia
    vinculada, marcar la incidencia como RESUELTA automáticamente.
    """
    if instance.fecha_cierre and instance.incidencia:
        incidencia = instance.incidencia
        if incidencia.estado != 'RESUELTA':
            incidencia.estado = 'RESUELTA'
            incidencia.save(update_fields=['estado'])

