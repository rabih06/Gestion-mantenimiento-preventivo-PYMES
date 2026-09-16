from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Q
from .models import Equipo, OrdenTrabajo, Alerta, Incidencia, Repuesto


def login_view(request):
    """Vista de login personalizada."""
    if request.user.is_authenticated:
        return redirect('mantenimiento:redirigir_por_rol')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('mantenimiento:redirigir_por_rol')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'mantenimiento/login.html')


@login_required
def redirigir_por_rol(request):
    """Redirige al usuario a su dashboard según su rol principal."""
    rol = getattr(request.user, 'rol_principal', None)

    if rol == 'ADMIN':
        return redirect('mantenimiento:dashboard_admin')
    elif rol == 'TECNICO':
        return redirect('mantenimiento:dashboard_tecnico')
    elif rol == 'OPERARIO':
        return redirect('mantenimiento:dashboard_operario')
    else:
        # Si no tiene rol definido, cerrar sesión por seguridad
        messages.error(request, 'Tu usuario no tiene un rol asignado. Contacta al administrador.')
        return redirect('mantenimiento:login')


@login_required
def dashboard_admin(request):
    """Dashboard del administrador con KPIs y gráficos reales."""
    if request.user.rol_principal != 'ADMIN':
        return redirect('mantenimiento:redirigir_por_rol')

    # =====================================================
    # KPIs PRINCIPALES
    # =====================================================
    total_equipos = Equipo.objects.count()
    
    ordenes_abiertas = OrdenTrabajo.objects.filter(
        estado__in=['PROGRAMADA', 'PROGRESO']
    ).count()
    
    alertas_activas = Alerta.objects.filter(leida=False).count()

    # =====================================================
    # KPIs SECUNDARIOS
    # =====================================================
    incidencias_pendientes = Incidencia.objects.filter(estado='PENDIENTE').count()
    
    repuestos_stock_bajo = Repuesto.objects.filter(
        cantidad_actual__lte=models.F('stock_minimo')
    ).count() if False else 0  # Lo calculamos después sin F()

    # Contar repuestos con stock bajo (sin usar F() aquí para simplificar)
    repuestos_bajos = 0
    for rep in Repuesto.objects.all():
        if rep.stock_bajo:
            repuestos_bajos += 1

    # =====================================================
    # DATOS PARA GRÁFICO (Equipos por estado)
    # =====================================================
    equipos_por_estado = Equipo.objects.values('estado_operativo').annotate(
        total=Count('id')
    )
    
    # Convertir a formato para Chart.js
    estados_labels = []
    estados_data = []
    for item in equipos_por_estado:
        estados_labels.append(dict(Equipo.ESTADO_CHOICES).get(item['estado_operativo'], item['estado_operativo']))
        estados_data.append(item['total'])

    # =====================================================
    # ÚLTIMAS ÓRDENES Y ALERTAS
    # =====================================================
    ultimas_ordenes = OrdenTrabajo.objects.all().order_by('-fecha_programada')[:5]
    ultimas_alertas = Alerta.objects.filter(leida=False).order_by('-created_at')[:5]

    context = {
        'total_equipos': total_equipos,
        'ordenes_abiertas': ordenes_abiertas,
        'alertas_activas': alertas_activas,
        'incidencias_pendientes': incidencias_pendientes,
        'repuestos_bajos': repuestos_bajos,
        'estados_labels': estados_labels,
        'estados_data': estados_data,
        'ultimas_ordenes': ultimas_ordenes,
        'ultimas_alertas': ultimas_alertas,
    }
    return render(request, 'mantenimiento/dashboard_admin.html', context)


@login_required
def dashboard_tecnico(request):
    """Panel del técnico (Kanban de órdenes)."""
    if request.user.rol_principal != 'TECNICO':
        return redirect('mantenimiento:redirigir_por_rol')
    
    # Órdenes asignadas al técnico
    ordenes = request.user.ordenes_asignadas.all().order_by('-fecha_programada')
    
    context = {
        'ordenes': ordenes,
    }
    return render(request, 'mantenimiento/dashboard_tecnico.html', context)


@login_required
def dashboard_operario(request):
    """Panel del operario (reportar fallas, ver estado de equipos)."""
    if request.user.rol_principal != 'OPERARIO':
        return redirect('mantenimiento:redirigir_por_rol')
    
    # Equipos asignados al operario
    equipos = request.user.equipos_asignados.all()
    
    # Incidencias reportadas por el operario
    incidencias = request.user.incidencias_reportadas.all().order_by('-fecha_reporte')[:10]
    
    context = {
        'equipos': equipos,
        'incidencias': incidencias,
    }
    return render(request, 'mantenimiento/dashboard_operario.html', context)
