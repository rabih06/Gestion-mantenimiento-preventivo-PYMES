from .models import Alerta


def alertas_no_leidas(request):
    """Contador de notificaciones no leídas PARA EL USUARIO ACTUAL."""
    if not request.user.is_authenticated:
        return {'alertas_count': 0}

    # Usar el manager personalizado que filtra por visibilidad
    count = (
        Alerta.objects
        .visibles_para(request.user)
        .exclude(leida_por=request.user)
        .count()
    )

    return {'alertas_count': count}