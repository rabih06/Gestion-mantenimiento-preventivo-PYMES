from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Repuesto, Equipo, OrdenRepuesto, OrdenTrabajo, HistorialEstadoEquipo, Alerta
from django.contrib.auth.models import Group
from .models import User


@receiver(post_save, sender=Repuesto)
def alerta_stock_bajo(sender, instance, **kwargs):
    """Genera alerta cuando el stock cae por debajo del mínimo."""
    if instance.cantidad_actual <= instance.stock_minimo:
        # Evitar duplicados: solo crear si no hay alerta sin leer para este repuesto
        existe = Alerta.objects.filter(
            tipo='STOCK_BAJO', repuesto=instance, leida=False
        ).exists()
        if not existe:
            Alerta.objects.create(
                tipo='STOCK_BAJO',
                mensaje=f"Stock bajo: {instance.nombre} ({instance.cantidad_actual} unidades, mínimo {instance.stock_minimo})",
                repuesto=instance
            )


@receiver(post_save, sender=OrdenRepuesto)
def descontar_stock(sender, instance, created, **kwargs):
    """Descuenta el stock del repuesto al usarlo en una orden."""
    if created:
        repuesto = instance.repuesto
        repuesto.cantidad_actual -= instance.cantidad_utilizada
        repuesto.fecha_ultima_salida = instance.created_at
        repuesto.save()


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
        return  # El grupo no existe todavía
    
    # Quitar al usuario de otros grupos de rol (por si cambió de rol)
    grupos_rol = Group.objects.filter(
        name__in=['Administradores', 'Técnicos', 'Operarios']
    )
    instance.groups.remove(*grupos_rol)
    
    # Añadirlo al grupo correspondiente
    instance.groups.add(grupo)