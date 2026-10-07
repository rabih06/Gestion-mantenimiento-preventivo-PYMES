"""
Utilidades para el sistema de mantenimiento.
"""
from datetime import timedelta
from django.utils import timezone

from .models import Alerta, User


def notificar(tipo, mensaje, equipo=None, repuesto=None, plan=None, 
              usuarios=None, notificar_admins=True, notificar_tecnicos=False,
              evitar_duplicados_minutos=60):
    """
    Crea una notificación/alerta con destinatarios específicos.
    
    Args:
        tipo: Tipo de alerta (debe estar en Alerta.TIPO_CHOICES)
        mensaje: Texto descriptivo
        equipo/repuesto/plan: Objetos relacionados (opcional)
        usuarios: Lista/queryset de usuarios específicos. Si se da, sobreescribe
                  notificar_admins y notificar_tecnicos.
        notificar_admins: Si True, incluye a todos los admins activos
        notificar_tecnicos: Si True, incluye a todos los técnicos activos
        evitar_duplicados_minutos: Ventana para evitar duplicados
    
    Returns:
        La alerta creada o None si se evitó por duplicado
    """
    # Evitar duplicados en ventana de tiempo
    if evitar_duplicados_minutos > 0:
        filtros = {
            'tipo': tipo,
            'created_at__gte': timezone.now() - timedelta(minutes=evitar_duplicados_minutos),
        }
        if equipo:
            filtros['equipo'] = equipo
        if repuesto:
            filtros['repuesto'] = repuesto
        if plan:
            filtros['plan'] = plan
        
        existe = Alerta.objects.filter(**filtros).exists()
        if existe:
            return None
    
    # Crear alerta
    alerta = Alerta.objects.create(
        tipo=tipo,
        mensaje=mensaje,
        equipo=equipo,
        repuesto=repuesto,
        plan=plan,
    )
    
    # Asignar destinatarios
    if usuarios is not None:
        # Destinatarios específicos (puede ser lista, queryset o un solo usuario)
        if hasattr(usuarios, '__iter__') and not isinstance(usuarios, User):
            alerta.destinatarios.set(usuarios)
        else:
            alerta.destinatarios.set([usuarios])
    else:
        destinatarios = []
        if notificar_admins:
            destinatarios += list(User.objects.filter(
                rol_principal='ADMIN', is_active=True
            ))
        if notificar_tecnicos:
            destinatarios += list(User.objects.filter(
                rol_principal='TECNICO', is_active=True
            ))
        if destinatarios:
            alerta.destinatarios.set(destinatarios)
    
    return alerta


def notificar_operario_responsable(equipo, tipo, mensaje, incluir_admin_tecnico=True):
    """
    Notifica al operario responsable de un equipo (si existe).
    Opcionalmente incluye a admin y técnicos.
    """
    usuarios = []
    
    # Operario responsable
    if equipo.responsable and equipo.responsable.rol_principal == 'OPERARIO':
        usuarios.append(equipo.responsable)
    
    if incluir_admin_tecnico:
        usuarios += list(User.objects.filter(rol_principal='ADMIN', is_active=True))
        usuarios += list(User.objects.filter(rol_principal='TECNICO', is_active=True))
    
    # Quitar duplicados
    usuarios = list(set(usuarios))
    
    if not usuarios:
        return None
    
    return notificar(
        tipo=tipo,
        mensaje=mensaje,
        equipo=equipo,
        usuarios=usuarios,
    )