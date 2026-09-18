from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Q
from .models import Equipo, OrdenTrabajo, Alerta, Incidencia, Repuesto
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import IncidenciaForm
from .models import Incidencia
from django.utils import timezone



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
    """Panel del técnico con Kanban de órdenes."""
    if request.user.rol_principal != 'TECNICO':
        return redirect('mantenimiento:redirigir_por_rol')

    # Solo las órdenes asignadas al técnico actual
    ordenes = OrdenTrabajo.objects.filter(
        tecnico=request.user
    ).select_related('equipo', 'incidencia')

    # Agrupar por estado para el Kanban
    programadas = ordenes.filter(estado='PROGRAMADA').order_by('prioridad', 'fecha_programada')
    en_progreso = ordenes.filter(estado='PROGRESO').order_by('fecha_programada')
    completadas = ordenes.filter(estado='COMPLETADA').order_by('-fecha_fin')[:10]
    canceladas = ordenes.filter(estado='CANCELADA').order_by('-fecha_programada')[:10]

    # KPIs rápidos
    total_asignadas = ordenes.count()
    total_programadas = programadas.count()
    total_progreso = en_progreso.count()
    total_completadas = ordenes.filter(estado='COMPLETADA').count()

    context = {
        'programadas': programadas,
        'en_progreso': en_progreso,
        'completadas': completadas,
        'canceladas': canceladas,
        'total_asignadas': total_asignadas,
        'total_programadas': total_programadas,
        'total_progreso': total_progreso,
        'total_completadas': total_completadas,
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

@login_required
def reportar_incidencia(request):
    """Permite al operario reportar una falla en un equipo."""
    if request.user.rol_principal != 'OPERARIO':
        messages.error(request, 'Solo los operarios pueden reportar incidencias.')
        return redirect('mantenimiento:redirigir_por_rol')

    if request.method == 'POST':
        form = IncidenciaForm(request.POST)
        if form.is_valid():
            incidencia = form.save(commit=False)
            incidencia.operario = request.user
            incidencia.save()
            messages.success(
                request,
                f'✅ Incidencia #{incidencia.id} reportada correctamente. '
                f'El equipo técnico la revisará pronto.'
            )
            return redirect('mantenimiento:lista_incidencias')
    else:
        form = IncidenciaForm()

    return render(request, 'mantenimiento/reportar_incidencia.html', {'form': form})


@login_required
def lista_incidencias(request):
    """Muestra las incidencias reportadas por el operario actual."""
    if request.user.rol_principal != 'OPERARIO':
        return redirect('mantenimiento:redirigir_por_rol')

    incidencias = Incidencia.objects.filter(
        operario=request.user
    ).order_by('-fecha_reporte')

    context = {
        'incidencias': incidencias,
        'total': incidencias.count(),
        'pendientes': incidencias.filter(estado='PENDIENTE').count(),
        'resueltas': incidencias.filter(estado='RESUELTA').count(),
    }
    return render(request, 'mantenimiento/lista_incidencias.html', context)

@login_required
def detalle_orden(request, orden_id):
    """Vista de detalle de una orden de trabajo."""
    if request.user.rol_principal not in ['TECNICO', 'ADMIN']:
        return redirect('mantenimiento:redirigir_por_rol')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    # Los técnicos solo pueden ver sus propias órdenes
    if request.user.rol_principal == 'TECNICO' and orden.tecnico != request.user:
        messages.error(request, 'No tienes permiso para ver esta orden.')
        return redirect('mantenimiento:dashboard_tecnico')

    # Repuestos disponibles para añadir
    repuestos_disponibles = Repuesto.objects.filter(cantidad_actual__gt=0)
    repuestos_usados = orden.repuestos_usados.select_related('repuesto')

    context = {
        'orden': orden,
        'repuestos_disponibles': repuestos_disponibles,
        'repuestos_usados': repuestos_usados,
    }
    return render(request, 'mantenimiento/detalle_orden.html', context)


@login_required
def cambiar_estado_orden(request, orden_id, nuevo_estado):
    """Cambia el estado de una orden y aplica la lógica de negocio asociada."""
    if request.user.rol_principal not in ['TECNICO', 'ADMIN']:
        return redirect('mantenimiento:redirigir_por_rol')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    # Los técnicos solo pueden cambiar sus propias órdenes
    if request.user.rol_principal == 'TECNICO' and orden.tecnico != request.user:
        messages.error(request, 'No tienes permiso para modificar esta orden.')
        return redirect('mantenimiento:dashboard_tecnico')

    estados_validos = ['PROGRAMADA', 'PROGRESO', 'COMPLETADA', 'CANCELADA']
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    from django.utils import timezone
    ahora = timezone.now()
    equipo = orden.equipo

    # =====================================================
    # LÓGICA DE NEGOCIO SEGÚN EL NUEVO ESTADO
    # =====================================================
    if nuevo_estado == 'PROGRESO':
        # Iniciar trabajo
        orden.estado = 'PROGRESO'
        orden.fecha_inicio = ahora
        equipo.estado_operativo = 'MANTENIMIENTO'
        equipo.bloqueado = True
        messages.success(request, f'OT-{orden.id} iniciada. Equipo bloqueado en mantenimiento.')

    elif nuevo_estado == 'COMPLETADA':
        # Completar trabajo
        orden.estado = 'COMPLETADA'
        orden.fecha_fin = ahora
        # Calcular duración
        if orden.fecha_inicio:
            delta = ahora - orden.fecha_inicio
            orden.duracion_horas = round(delta.total_seconds() / 3600, 2)
        # Actualizar equipo
        equipo.estado_operativo = 'ACTIVO'
        equipo.bloqueado = False
        equipo.ultimo_mantenimiento = ahora
        # Calcular próximo mantenimiento
        if equipo.intervalo_mantenimiento_dias > 0:
            equipo.proximo_mantenimiento = ahora + timezone.timedelta(
                days=equipo.intervalo_mantenimiento_dias
            )
        messages.success(request, f'OT-{orden.id} completada. Equipo disponible.')

    elif nuevo_estado == 'CANCELADA':
        # Cancelar
        orden.estado = 'CANCELADA'
        equipo.estado_operativo = 'ACTIVO'
        equipo.bloqueado = False
        messages.warning(request, f'OT-{orden.id} cancelada.')

    orden.save()
    equipo.save()

    return redirect('mantenimiento:dashboard_tecnico')