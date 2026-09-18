from .models import Alerta


def alertas_no_leidas(request):
    """Contador global de alertas no leídas para el navbar."""
    if not request.user.is_authenticated:
        return {'alertas_count': 0}

    # Solo admin y técnicos ven las alertas
    if request.user.rol_principal in ['ADMIN', 'TECNICO']:
        count = Alerta.objects.filter(leida=False).count()
    else:
        count = 0

    return {'alertas_count': count}