from .models import Alerta


def alertas_no_leidas(request):
    """Contador global de alertas no leídas PARA EL USUARIO ACTUAL."""
    if not request.user.is_authenticated:
        return {'alertas_count': 0}

    if request.user.rol_principal in ['ADMIN', 'TECNICO']:
        count = Alerta.objects.exclude(leida_por=request.user).count()
    else:
        count = 0

    return {'alertas_count': count}