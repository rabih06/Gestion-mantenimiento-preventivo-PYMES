from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group

from .models import (
    Repuesto, Equipo, OrdenRepuesto, OrdenTrabajo,
    HistorialEstadoEquipo, Alerta, User, Incidencia
)


# =====================================================
# ALERTAS AUTOMÁTICAS
# =====================================================

@receiver(post_save, sender=Repuesto)
def alerta_stock_bajo(sender, instance, **kwargs):
    """Genera alerta cuando el stock cae por debajo del mínimo."""
    if instance.cantidad_actual <= instance.stock_minimo:
        # ✅ Evitar duplicados en las últimas 24 horas
        existe = Alerta.objects.filter(
            tipo='STOCK_BAJO',
            repuesto=instance,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exists()
        if not existe:
            Alerta.objects.create(
                tipo='STOCK_BAJO',
                mensaje=f"Stock bajo: {instance.nombre} ({instance.cantidad_actual} unidades, mínimo {instance.stock_minimo})",
                repuesto=instance
            )


@receiver(post_save, sender=Incidencia)
def crear_alerta_incidencia(sender, instance, created, **kwargs):
    """Crea una alerta automática cuando se reporta una incidencia crítica o alta."""
    if created and instance.prioridad in ['ALTA', 'CRITICA']:
        Alerta.objects.create(
            tipo='EQUIPO_CRITICO',
            mensaje=f"Incidencia {instance.get_prioridad_display()}: {instance.equipo.codigo_interno} - {instance.descripcion_falla[:80]}",
            equipo=instance.equipo,
        )


@receiver(post_save, sender=Incidencia)
def alerta_incidencia_resuelta(sender, instance, **kwargs):
    """Crea una alerta cuando una incidencia se marca como RESUELTA."""
    if instance.estado == 'RESUELTA' and instance.operario:
        # ✅ Evitar duplicados en las últimas 24 horas
        existe = Alerta.objects.filter(
            tipo='OTRA',
            equipo=instance.equipo,
            mensaje__icontains=f'Incidencia #{instance.id}',
            created_at__gte=timezone.now() - timedelta(hours=24),
        ).exists()
        if not existe:
            Alerta.objects.create(
                tipo='OTRA',
                mensaje=f'✅ Incidencia #{instance.id} resuelta: {instance.equipo.codigo_interno} - {instance.descripcion_falla[:60]}',
                equipo=instance.equipo,
            )


# =====================================================
# LÓGICA DE REPUESTOS EN ÓRDENES
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
    """Rellena el precio_unitario_momento con el precio actual del repuesto si no se especificó."""
    if created and (not instance.precio_unitario_momento or instance.precio_unitario_momento == 0):
        instance.precio_unitario_momento = instance.repuesto.precio_unitario
        instance.save(update_fields=['precio_unitario_momento'])


@receiver([post_save, post_delete], sender=OrdenRepuesto)
def recalcular_costo_orden(sender, instance, **kwargs):
    try:
        instance.orden.recalcular_costo_total()
    except OrdenTrabajo.DoesNotExist:
        pass


# =====================================================
# HISTORIAL DE ESTADOS
# =====================================================

@receiver(pre_save, sender=Equipo)
def registrar_cambio_estado(sender, instance, **kwargs):
    """Registra el cambio de estado del equipo en el historial."""
    if instance.pk:
        try:
            anterior = Equipo.objects.get(pk=instance.pk)
            if anterior.estado_operativo != instance.estado_operativo:
                HistorialEstadoEquipo.objects.create(
                    equipo=instance,
                    estado_anterior=anterior.estado_operativo,
                    estado_nuevo=instance.estado_operativo,
                    motivo="Cambio manual desde admin"
                )
        except Equipo.DoesNotExist:
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

