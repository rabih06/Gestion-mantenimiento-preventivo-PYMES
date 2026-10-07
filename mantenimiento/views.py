from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import (
    Equipo, CategoriaEquipo, User, Alerta,
    Repuesto, Proveedor, OrdenTrabajo, Incidencia, PlanMantenimiento,
    MovimientoRepuesto, OrdenRepuesto
)

from .forms import (
    IncidenciaForm, EquipoForm, AtributoEquipoFormSet, RepuestoForm,
    ProveedorForm, PlanMantenimientoForm, RetirarRepuestoForm,
    OrdenTrabajoForm, OrdenRepuestoFormSet
)


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

    # ✅ Alertas NO leídas por el admin actual
    alertas_activas = Alerta.objects.exclude(leida_por=request.user).count()

    # =====================================================
    # KPIs SECUNDARIOS
    # =====================================================
    incidencias_pendientes = Incidencia.objects.filter(estado='PENDIENTE').count()

    repuestos_bajos = sum(1 for rep in Repuesto.objects.all() if rep.stock_bajo)

    # =====================================================
    # DATOS PARA GRÁFICO
    # =====================================================
    equipos_por_estado = Equipo.objects.values('estado_operativo').annotate(
        total=Count('id')
    )

    estados_labels = []
    estados_data = []
    for item in equipos_por_estado:
        estados_labels.append(
            dict(Equipo.ESTADO_CHOICES).get(item['estado_operativo'], item['estado_operativo'])
        )
        estados_data.append(item['total'])

    # =====================================================
    # ÚLTIMAS ÓRDENES Y ALERTAS
    # =====================================================
    ultimas_ordenes = OrdenTrabajo.objects.all().order_by('-fecha_programada')[:5]
    ultimas_alertas = Alerta.objects.exclude(leida_por=request.user).order_by('-created_at')[:5]

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

    # ✅ Alertas no leídas por el técnico actual
    alertas_no_leidas = Alerta.objects.exclude(leida_por=request.user).count()

    ordenes = OrdenTrabajo.objects.filter(
        tecnico=request.user
    ).select_related('equipo', 'incidencia')

    programadas = ordenes.filter(estado='PROGRAMADA').order_by('prioridad', 'fecha_programada')
    en_progreso = ordenes.filter(estado='PROGRESO').order_by('fecha_programada')
    completadas = ordenes.filter(estado='COMPLETADA').order_by('-fecha_fin')[:10]
    canceladas = ordenes.filter(estado='CANCELADA').order_by('-fecha_programada')[:10]

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
        'alertas_no_leidas': alertas_no_leidas,
    }
    return render(request, 'mantenimiento/dashboard_tecnico.html', context)


@login_required
def dashboard_operario(request):
    """Panel del operario (reportar fallas, ver estado de equipos)."""
    if request.user.rol_principal != 'OPERARIO':
        return redirect('mantenimiento:redirigir_por_rol')

    equipos = request.user.equipos_asignados.all()
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


# =====================================================
# ALERTAS
# =====================================================

@login_required
def lista_alertas(request):
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver las alertas.')
        return redirect('mantenimiento:redirigir_por_rol')

    alertas = Alerta.objects.select_related(
        'repuesto', 'equipo', 'plan'
    ).order_by('-created_at')

    tipo_filtro = request.GET.get('tipo', '')
    estado_filtro = request.GET.get('estado', '')

    if tipo_filtro:
        alertas = alertas.filter(tipo=tipo_filtro)

    if estado_filtro == 'leidas':
        alertas = alertas.filter(leida_por=request.user)
    elif estado_filtro == 'no_leidas':
        alertas = alertas.exclude(leida_por=request.user)

    total_alertas = Alerta.objects.count()
    no_leidas = Alerta.objects.exclude(leida_por=request.user).count()
    leidas = Alerta.objects.filter(leida_por=request.user).count()

    context = {
        'alertas': alertas,
        'tipo_filtro': tipo_filtro,
        'estado_filtro': estado_filtro,
        'tipos_alerta': Alerta.TIPO_CHOICES,
        'total_alertas': total_alertas,
        'no_leidas': no_leidas,
        'leidas': leidas,
    }
    return render(request, 'mantenimiento/lista_alertas.html', context)


@login_required
def marcar_alerta_leida(request, alerta_id):
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        return redirect('mantenimiento:redirigir_por_rol')

    alerta = get_object_or_404(Alerta, id=alerta_id)
    alerta.leida_por.add(request.user)
    messages.success(request, 'Alerta marcada como leída.')

    return redirect(request.META.get('HTTP_REFERER', 'mantenimiento:lista_alertas'))


@login_required
def marcar_todas_leidas(request):
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        return redirect('mantenimiento:redirigir_por_rol')

    if request.method == 'POST':
        pendientes = Alerta.objects.exclude(leida_por=request.user)
        cantidad = pendientes.count()
        for alerta in pendientes:
            alerta.leida_por.add(request.user)
        messages.success(request, f'{cantidad} alertas marcadas como leídas.')

    return redirect('mantenimiento:lista_alertas')


@login_required
def eliminar_alerta(request, alerta_id):
    """Elimina una alerta."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        return redirect('mantenimiento:redirigir_por_rol')

    alerta = get_object_or_404(Alerta, id=alerta_id)
    alerta.delete()
    messages.success(request, 'Alerta eliminada.')

    return redirect('mantenimiento:lista_alertas')


# =====================================================
# CRUD DE EQUIPOS
# =====================================================

@login_required
def lista_equipos(request):
    """Lista de equipos con búsqueda, filtros y paginación."""
    equipos = Equipo.objects.select_related('categoria', 'responsable').all()

    if request.user.rol_principal == 'OPERARIO':
        equipos = equipos.filter(
            Q(responsable=request.user) | Q(responsable__isnull=True)
        )

    q = request.GET.get('q', '').strip()
    if q:
        equipos = equipos.filter(
            Q(codigo_interno__icontains=q) |
            Q(nombre__icontains=q) |
            Q(numero_serie__icontains=q) |
            Q(marca__icontains=q)
        )

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        equipos = equipos.filter(estado_operativo=estado_filtro)

    categoria_filtro = request.GET.get('categoria', '')
    if categoria_filtro:
        equipos = equipos.filter(categoria_id=categoria_filtro)

    bloqueado_filtro = request.GET.get('bloqueado', '')
    if bloqueado_filtro == 'si':
        equipos = equipos.filter(bloqueado=True)
    elif bloqueado_filtro == 'no':
        equipos = equipos.filter(bloqueado=False)

    orden = request.GET.get('orden', 'codigo_interno')
    equipos = equipos.order_by(orden)

    paginator = Paginator(equipos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado_filtro,
        'categoria_filtro': categoria_filtro,
        'bloqueado_filtro': bloqueado_filtro,
        'orden': orden,
        'estados': Equipo.ESTADO_CHOICES,
        'categorias': CategoriaEquipo.objects.all(),
        'query_params': query_params.urlencode(),
        'total_equipos': equipos.count(),
    }
    return render(request, 'mantenimiento/equipos/lista_equipos.html', context)


@login_required
def detalle_equipo(request, equipo_id):
    """Vista detallada de un equipo con su historial completo."""
    equipo = get_object_or_404(Equipo, id=equipo_id)

    if request.user.rol_principal == 'OPERARIO':
        if equipo.responsable and equipo.responsable != request.user:
            messages.error(
                request,
                'No tienes permiso para ver este equipo. '
                'Solo puedes consultar los equipos bajo tu responsabilidad.'
            )
            return redirect('mantenimiento:lista_equipos')

    ordenes = equipo.ordenes.select_related('tecnico').order_by('-fecha_programada')[:10]
    incidencias = equipo.incidencias.select_related('operario').order_by('-fecha_reporte')[:10]
    planes = equipo.planes.filter(is_active=True)
    atributos = equipo.atributos.all()
    historial_estados = equipo.historial_estados.order_by('-fecha_cambio')[:10]
    # ✅ Alertas NO leídas por el usuario actual
    alertas = equipo.alertas.exclude(leida_por=request.user).order_by('-created_at')[:5]

    context = {
        'equipo': equipo,
        'ordenes': ordenes,
        'incidencias': incidencias,
        'planes': planes,
        'atributos': atributos,
        'historial_estados': historial_estados,
        'alertas': alertas,
    }
    return render(request, 'mantenimiento/equipos/detalle_equipo.html', context)


@login_required
def crear_equipo(request):
    """Crear un nuevo equipo con sus atributos técnicos (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear equipos.')
        return redirect('mantenimiento:lista_equipos')

    if request.method == 'POST':
        form = EquipoForm(request.POST)
        formset = AtributoEquipoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            equipo = form.save()
            formset.instance = equipo
            formset.save()
            messages.success(request, f'✅ Equipo "{equipo.nombre}" creado correctamente.')
            return redirect('mantenimiento:detalle_equipo', equipo_id=equipo.id)
    else:
        form = EquipoForm()
        formset = AtributoEquipoFormSet()

    return render(request, 'mantenimiento/equipos/form_equipo.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Nuevo Equipo',
        'accion': 'Crear',
    })


@login_required
def editar_equipo(request, equipo_id):
    """Editar un equipo existente (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden editar equipos.')
        return redirect('mantenimiento:lista_equipos')

    equipo = get_object_or_404(Equipo, id=equipo_id)

    if request.method == 'POST':
        form = EquipoForm(request.POST, instance=equipo)
        formset = AtributoEquipoFormSet(request.POST, instance=equipo)

        if form.is_valid() and formset.is_valid():
            equipo = form.save()
            formset.save()
            messages.success(request, f'✅ Equipo "{equipo.nombre}" actualizado.')
            return redirect('mantenimiento:detalle_equipo', equipo_id=equipo.id)
    else:
        form = EquipoForm(instance=equipo)
        formset = AtributoEquipoFormSet(instance=equipo)

    return render(request, 'mantenimiento/equipos/form_equipo.html', {
        'form': form,
        'formset': formset,
        'equipo': equipo,
        'titulo': f'Editar: {equipo.nombre}',
        'accion': 'Guardar Cambios',
    })


@login_required
def eliminar_equipo(request, equipo_id):
    """Eliminar un equipo (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden eliminar equipos.')
        return redirect('mantenimiento:lista_equipos')

    equipo = get_object_or_404(Equipo, id=equipo_id)

    ordenes_activas = equipo.ordenes.filter(estado__in=['PROGRAMADA', 'PROGRESO']).count()
    if ordenes_activas > 0:
        messages.error(
            request,
            f'No se puede eliminar: el equipo tiene {ordenes_activas} orden(es) activa(s).'
        )
        return redirect('mantenimiento:detalle_equipo', equipo_id=equipo.id)

    if request.method == 'POST':
        nombre = equipo.nombre
        equipo.delete()
        messages.success(request, f'Equipo "{nombre}" eliminado correctamente.')
        return redirect('mantenimiento:lista_equipos')

    return render(request, 'mantenimiento/equipos/confirmar_eliminar.html', {'equipo': equipo})


# =====================================================
# CRUD DE REPUESTOS
# =====================================================

@login_required
def lista_repuestos(request):
    """Lista de repuestos con búsqueda, filtros y paginación."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los repuestos.')
        return redirect('mantenimiento:redirigir_por_rol')

    repuestos = Repuesto.objects.select_related('proveedor').all()

    q = request.GET.get('q', '').strip()
    if q:
        repuestos = repuestos.filter(
            Q(codigo_sku__icontains=q) |
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )

    proveedor_filtro = request.GET.get('proveedor', '')
    if proveedor_filtro:
        repuestos = repuestos.filter(proveedor_id=proveedor_filtro)

    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro:
        repuestos = repuestos.filter(tipo=tipo_filtro)  # ✅ FIX: era repuestos_qs

    stock_filtro = request.GET.get('stock', '')
    if stock_filtro == 'bajo':
        repuestos = [r for r in repuestos if r.stock_bajo]
    elif stock_filtro == 'normal':
        repuestos = [r for r in repuestos if not r.stock_bajo]

    orden = request.GET.get('orden', 'nombre')
    if isinstance(repuestos, list):
        repuestos = sorted(repuestos, key=lambda x: getattr(x, orden, ''))
    else:
        repuestos = repuestos.order_by(orden)

    paginator = Paginator(repuestos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_repuestos = Repuesto.objects.count()
    repuestos_criticos = sum(1 for r in Repuesto.objects.all() if r.stock_bajo)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'proveedor_filtro': proveedor_filtro,
        'stock_filtro': stock_filtro,
        'orden': orden,
        'proveedores': Proveedor.objects.filter(is_active=True),
        'query_params': query_params.urlencode(),
        'total_repuestos': total_repuestos,
        'repuestos_criticos': repuestos_criticos,
        'tipo_filtro': tipo_filtro,
        'tipos_repuesto': Repuesto.TIPO_CHOICES,
    }
    return render(request, 'mantenimiento/repuestos/lista_repuestos.html', context)


@login_required
def detalle_repuesto(request, repuesto_id):
    """Vista detallada de un repuesto."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los repuestos.')
        return redirect('mantenimiento:redirigir_por_rol')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)

    usos = repuesto.ordenes_usadas.select_related(
        'orden', 'orden__equipo'
    ).order_by('-created_at')[:20]

    # ✅ FIX: era equipo.alertas → debe ser repuesto.alertas
    alertas = repuesto.alertas.exclude(leida_por=request.user).order_by('-created_at')

    total_usado = sum(u.cantidad_utilizada for u in repuesto.ordenes_usadas.all())

    context = {
        'repuesto': repuesto,
        'usos': usos,
        'alertas': alertas,
        'total_usado': total_usado,
    }
    return render(request, 'mantenimiento/repuestos/detalle_repuesto.html', context)


@login_required
def crear_repuesto(request):
    """Crear un nuevo repuesto (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear repuestos.')
        return redirect('mantenimiento:lista_repuestos')

    if request.method == 'POST':
        form = RepuestoForm(request.POST)
        if form.is_valid():
            repuesto = form.save()
            messages.success(request, f'✅ Repuesto "{repuesto.nombre}" creado correctamente.')
            return redirect('mantenimiento:detalle_repuesto', repuesto_id=repuesto.id)
    else:
        form = RepuestoForm()

    return render(request, 'mantenimiento/repuestos/form_repuesto.html', {
        'form': form,
        'titulo': 'Crear Nuevo Repuesto',
        'accion': 'Crear',
    })


@login_required
def editar_repuesto(request, repuesto_id):
    """Editar un repuesto (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'No tienes permiso para editar repuestos.')
        return redirect('mantenimiento:lista_repuestos')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)

    if request.method == 'POST':
        form = RepuestoForm(request.POST, instance=repuesto)
        if form.is_valid():
            repuesto = form.save()
            messages.success(request, f'✅ Repuesto "{repuesto.nombre}" actualizado.')
            return redirect('mantenimiento:detalle_repuesto', repuesto_id=repuesto.id)
    else:
        form = RepuestoForm(instance=repuesto)

    return render(request, 'mantenimiento/repuestos/form_repuesto.html', {
        'form': form,
        'repuesto': repuesto,
        'titulo': f'Editar: {repuesto.nombre}',
        'accion': 'Guardar Cambios',
    })


@login_required
def eliminar_repuesto(request, repuesto_id):
    """Eliminar un repuesto (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden eliminar repuestos.')
        return redirect('mantenimiento:lista_repuestos')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)

    usos_activos = repuesto.ordenes_usadas.filter(
        orden__estado__in=['PROGRAMADA', 'PROGRESO']
    ).count()
    if usos_activos > 0:
        messages.error(
            request,
            f'No se puede eliminar: el repuesto está en uso en {usos_activos} orden(es) activa(s).'
        )
        return redirect('mantenimiento:detalle_repuesto', repuesto_id=repuesto.id)

    if request.method == 'POST':
        nombre = repuesto.nombre
        repuesto.delete()
        messages.success(request, f'Repuesto "{nombre}" eliminado correctamente.')
        return redirect('mantenimiento:lista_repuestos')

    return render(request, 'mantenimiento/repuestos/confirmar_eliminar.html', {'repuesto': repuesto})


@login_required
def retirar_repuesto(request, repuesto_id):
    """Permite al técnico retirar repuestos del inventario."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para retirar repuestos.')
        return redirect('mantenimiento:redirigir_por_rol')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)

    if request.method == 'POST':
        form = RetirarRepuestoForm(request.POST, repuesto=repuesto)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            motivo = form.cleaned_data.get('motivo', '')
            cantidad_anterior = repuesto.cantidad_actual

            repuesto.cantidad_actual -= cantidad
            repuesto.fecha_ultima_salida = timezone.now()
            repuesto.save()

            MovimientoRepuesto.objects.create(
                repuesto=repuesto,
                tipo='SALIDA',
                cantidad=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=repuesto.cantidad_actual,
                motivo=motivo,
                usuario=request.user,
            )

            messages.success(
                request,
                f'✅ Se retiraron {cantidad} {repuesto.unidad_medida}(s) de "{repuesto.nombre}". '
                f'Stock actual: {repuesto.cantidad_actual}.'
            )
            return redirect('mantenimiento:detalle_repuesto', repuesto_id=repuesto.id)
    else:
        form = RetirarRepuestoForm(repuesto=repuesto)

    context = {'form': form, 'repuesto': repuesto}
    return render(request, 'mantenimiento/repuestos/retirar_repuesto.html', context)


@login_required
def historial_movimientos(request, repuesto_id):
    """Muestra el historial de movimientos de un repuesto (auditoría)."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los movimientos.')
        return redirect('mantenimiento:redirigir_por_rol')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)
    movimientos = repuesto.movimientos.select_related(
        'usuario', 'orden'
    ).order_by('-created_at')

    context = {
        'repuesto': repuesto,
        'movimientos': movimientos,
        'total_movimientos': movimientos.count(),
    }
    return render(request, 'mantenimiento/repuestos/historial_movimientos.html', context)


# =====================================================
# CRUD DE PROVEEDORES (SOLO ADMIN)
# =====================================================

@login_required
def lista_proveedores(request):
    """Lista de proveedores con búsqueda, filtros y paginación. SOLO ADMIN."""
    # ✅ FIX: Técnico ya no puede ver proveedores
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden ver los proveedores.')
        return redirect('mantenimiento:redirigir_por_rol')

    proveedores = Proveedor.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        proveedores = proveedores.filter(
            Q(nombre__icontains=q) |
            Q(contacto__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'activos':
        proveedores = proveedores.filter(is_active=True)
    elif estado_filtro == 'inactivos':
        proveedores = proveedores.filter(is_active=False)

    orden = request.GET.get('orden', 'nombre')
    proveedores = proveedores.order_by(orden)

    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_proveedores = Proveedor.objects.count()
    activos = Proveedor.objects.filter(is_active=True).count()
    inactivos = Proveedor.objects.filter(is_active=False).count()

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado_filtro,
        'orden': orden,
        'query_params': query_params.urlencode(),
        'total_proveedores': total_proveedores,
        'activos': activos,
        'inactivos': inactivos,
    }
    return render(request, 'mantenimiento/proveedores/lista_proveedores.html', context)


@login_required
def detalle_proveedor(request, proveedor_id):
    """Vista detallada de un proveedor. SOLO ADMIN."""
    # ✅ FIX: Técnico ya no puede ver proveedores
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden ver los proveedores.')
        return redirect('mantenimiento:redirigir_por_rol')

    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    repuestos = proveedor.repuestos.all().order_by('nombre')

    total_repuestos = repuestos.count()
    repuestos_stock_bajo = sum(1 for r in repuestos if r.stock_bajo)

    context = {
        'proveedor': proveedor,
        'repuestos': repuestos,
        'total_repuestos': total_repuestos,
        'repuestos_stock_bajo': repuestos_stock_bajo,
    }
    return render(request, 'mantenimiento/proveedores/detalle_proveedor.html', context)


@login_required
def crear_proveedor(request):
    """Crear un nuevo proveedor (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear proveedores.')
        return redirect('mantenimiento:lista_proveedores')

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f'✅ Proveedor "{proveedor.nombre}" creado correctamente.')
            return redirect('mantenimiento:detalle_proveedor', proveedor_id=proveedor.id)
    else:
        form = ProveedorForm()

    return render(request, 'mantenimiento/proveedores/form_proveedor.html', {
        'form': form,
        'titulo': 'Crear Nuevo Proveedor',
        'accion': 'Crear',
    })


@login_required
def editar_proveedor(request, proveedor_id):
    """Editar un proveedor (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden editar proveedores.')
        return redirect('mantenimiento:lista_proveedores')

    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f'✅ Proveedor "{proveedor.nombre}" actualizado.')
            return redirect('mantenimiento:detalle_proveedor', proveedor_id=proveedor.id)
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'mantenimiento/proveedores/form_proveedor.html', {
        'form': form,
        'proveedor': proveedor,
        'titulo': f'Editar: {proveedor.nombre}',
        'accion': 'Guardar Cambios',
    })


@login_required
def eliminar_proveedor(request, proveedor_id):
    """Eliminar un proveedor (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden eliminar proveedores.')
        return redirect('mantenimiento:lista_proveedores')

    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    repuestos_asociados = proveedor.repuestos.count()
    if repuestos_asociados > 0:
        messages.error(
            request,
            f'No se puede eliminar: el proveedor tiene {repuestos_asociados} repuesto(s) asociado(s). '
            f'Reasigna esos repuestos a otro proveedor primero.'
        )
        return redirect('mantenimiento:detalle_proveedor', proveedor_id=proveedor.id)

    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor "{nombre}" eliminado correctamente.')
        return redirect('mantenimiento:lista_proveedores')

    return render(request, 'mantenimiento/proveedores/confirmar_eliminar.html', {'proveedor': proveedor})


# =====================================================
# CRUD DE PLANES DE MANTENIMIENTO
# =====================================================

@login_required
def lista_planes(request):
    """Lista de planes con búsqueda, filtros y paginación."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los planes.')
        return redirect('mantenimiento:redirigir_por_rol')

    planes = PlanMantenimiento.objects.select_related('equipo').all()

    if request.user.rol_principal == 'TECNICO':
        equipos_con_ordenes = OrdenTrabajo.objects.filter(
            tecnico=request.user
        ).values_list('equipo_id', flat=True).distinct()
        planes = planes.filter(equipo_id__in=equipos_con_ordenes)

    q = request.GET.get('q', '').strip()
    if q:
        planes = planes.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(equipo__codigo_interno__icontains=q) |
            Q(equipo__nombre__icontains=q)
        )

    equipo_filtro = request.GET.get('equipo', '')
    if equipo_filtro:
        planes = planes.filter(equipo_id=equipo_filtro)

    tecnico_filtro = request.GET.get('tecnico', '')
    if tecnico_filtro:
        planes = planes.filter(tecnico_asignado_id=tecnico_filtro)

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'activos':
        planes = planes.filter(is_active=True)
    elif estado_filtro == 'inactivos':
        planes = planes.filter(is_active=False)

    vencimiento_filtro = request.GET.get('vencimiento', '')
    if vencimiento_filtro:
        from datetime import timedelta
        hoy = timezone.now()
        if vencimiento_filtro == 'vencidos':
            planes = planes.filter(proxima_ejecucion__lt=hoy, is_active=True)
        elif vencimiento_filtro == 'proximos_7dias':
            planes = planes.filter(
                proxima_ejecucion__gte=hoy,
                proxima_ejecucion__lte=hoy + timedelta(days=7),
                is_active=True,
            )
        elif vencimiento_filtro == 'proximos_30dias':
            planes = planes.filter(
                proxima_ejecucion__gte=hoy,
                proxima_ejecucion__lte=hoy + timedelta(days=30),
                is_active=True,
            )

    orden = request.GET.get('orden', 'proxima_ejecucion')
    planes = planes.order_by(orden)

    paginator = Paginator(planes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    from datetime import timedelta
    hoy = timezone.now()
    total_planes = PlanMantenimiento.objects.count()
    activos = PlanMantenimiento.objects.filter(is_active=True).count()
    vencidos = PlanMantenimiento.objects.filter(
        is_active=True, proxima_ejecucion__lt=hoy
    ).count()
    proximos_7d = PlanMantenimiento.objects.filter(
        is_active=True,
        proxima_ejecucion__gte=hoy,
        proxima_ejecucion__lte=hoy + timedelta(days=7),
    ).count()

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'equipo_filtro': equipo_filtro,
        'estado_filtro': estado_filtro,
        'vencimiento_filtro': vencimiento_filtro,
        'orden': orden,
        'equipos': Equipo.objects.all().order_by('codigo_interno'),
        'query_params': query_params.urlencode(),
        'total_planes': total_planes,
        'activos': activos,
        'vencidos': vencidos,
        'proximos_7d': proximos_7d,
        'tecnico_filtro': tecnico_filtro,
        'tecnicos': User.objects.filter(rol_principal='TECNICO', is_active=True),
    }
    return render(request, 'mantenimiento/planes/lista_planes.html', context)


@login_required
def detalle_plan(request, plan_id):
    """Vista detallada de un plan con su historial de OTs."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los planes.')
        return redirect('mantenimiento:redirigir_por_rol')

    plan = get_object_or_404(PlanMantenimiento, id=plan_id)

    if request.user.rol_principal == 'TECNICO':
        tiene_ordenes = OrdenTrabajo.objects.filter(
            tecnico=request.user, equipo=plan.equipo
        ).exists()
        if not tiene_ordenes:
            messages.error(request, 'No tienes permiso para ver este plan.')
            return redirect('mantenimiento:lista_planes')

    ordenes = plan.ordenes_generadas.select_related('tecnico', 'equipo').order_by('-fecha_programada')

    context = {
        'plan': plan,
        'ordenes': ordenes,
        'total_ordenes': ordenes.count(),
    }
    return render(request, 'mantenimiento/planes/detalle_plan.html', context)


@login_required
def crear_plan(request):
    """Crear un nuevo plan (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear planes.')
        return redirect('mantenimiento:lista_planes')

    equipo_preseleccionado = request.GET.get('equipo', '')

    if request.method == 'POST':
        form = PlanMantenimientoForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'✅ Plan "{plan.nombre}" creado correctamente.')
            return redirect('mantenimiento:detalle_plan', plan_id=plan.id)
    else:
        initial = {}
        if equipo_preseleccionado:
            initial['equipo'] = equipo_preseleccionado
        form = PlanMantenimientoForm(initial=initial)

    return render(request, 'mantenimiento/planes/form_plan.html', {
        'form': form,
        'titulo': 'Crear Nuevo Plan de Mantenimiento',
        'accion': 'Crear',
    })


@login_required
def editar_plan(request, plan_id):
    """Editar un plan (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden editar planes.')
        return redirect('mantenimiento:lista_planes')

    plan = get_object_or_404(PlanMantenimiento, id=plan_id)

    if request.method == 'POST':
        form = PlanMantenimientoForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'✅ Plan "{plan.nombre}" actualizado.')
            return redirect('mantenimiento:detalle_plan', plan_id=plan.id)
    else:
        form = PlanMantenimientoForm(instance=plan)

    return render(request, 'mantenimiento/planes/form_plan.html', {
        'form': form,
        'plan': plan,
        'titulo': f'Editar: {plan.nombre}',
        'accion': 'Guardar Cambios',
    })


@login_required
def eliminar_plan(request, plan_id):
    """Eliminar un plan (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden eliminar planes.')
        return redirect('mantenimiento:lista_planes')

    plan = get_object_or_404(PlanMantenimiento, id=plan_id)

    if request.method == 'POST':
        nombre = plan.nombre
        plan.delete()
        messages.success(request, f'Plan "{nombre}" eliminado correctamente.')
        return redirect('mantenimiento:lista_planes')

    return render(request, 'mantenimiento/planes/confirmar_eliminar.html', {'plan': plan})


@login_required
def aplicar_plan(request, plan_id):
    """Genera una Orden de Trabajo preventiva a partir de un plan."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para aplicar planes.')
        return redirect('mantenimiento:redirigir_por_rol')

    plan = get_object_or_404(PlanMantenimiento, id=plan_id)

    if request.user.rol_principal == 'TECNICO':
        tiene_ordenes = OrdenTrabajo.objects.filter(
            tecnico=request.user, equipo=plan.equipo
        ).exists()
        if not tiene_ordenes:
            messages.error(request, 'No tienes permiso para aplicar este plan.')
            return redirect('mantenimiento:lista_planes')

    if not plan.is_active:
        messages.error(request, 'No puedes aplicar un plan inactivo.')
        return redirect('mantenimiento:detalle_plan', plan_id=plan.id)

    ahora = timezone.now()

    tecnico = None
    if plan.tecnico_asignado:
        tecnico = plan.tecnico_asignado
    elif request.user.rol_principal == 'TECNICO':
        tecnico = request.user

    orden = OrdenTrabajo.objects.create(
        equipo=plan.equipo,
        tecnico=tecnico,
        plan=plan,
        tipo='PREVENTIVO',
        prioridad='MEDIA',
        fecha_programada=ahora,
        descripcion_trabajo=f"[Plan: {plan.nombre}]\n\n{plan.descripcion}",
        estado='PROGRAMADA',
        generada_por_sistema=False,
    )

    plan.ultima_ejecucion = ahora
    plan.save()

    if tecnico:
        mensaje = f'✅ Se creó la OT-{orden.id} y se asignó a {tecnico.get_full_name() or tecnico.username}.'
    else:
        mensaje = f'✅ Se creó la OT-{orden.id} (sin técnico asignado). Asígnalo desde el detalle de la orden.'

    messages.success(request, mensaje)
    return redirect('mantenimiento:detalle_orden', orden_id=orden.id)


# =====================================================
# CRUD DE ÓRDENES DE TRABAJO
# =====================================================

@login_required
def lista_ordenes(request):
    """Lista de órdenes de trabajo con filtros."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver las órdenes.')
        return redirect('mantenimiento:redirigir_por_rol')

    ordenes = OrdenTrabajo.objects.select_related(
        'equipo', 'tecnico', 'incidencia', 'plan'
    ).all()

    if request.user.rol_principal == 'TECNICO':
        ordenes = ordenes.filter(tecnico=request.user)

    q = request.GET.get('q', '').strip()
    if q:
        ordenes = ordenes.filter(
            Q(descripcion_trabajo__icontains=q) |
            Q(equipo__codigo_interno__icontains=q) |
            Q(equipo__nombre__icontains=q) |
            Q(tecnico__first_name__icontains=q) |
            Q(tecnico__last_name__icontains=q)
        )

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        ordenes = ordenes.filter(estado=estado_filtro)

    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro:
        ordenes = ordenes.filter(tipo=tipo_filtro)

    prioridad_filtro = request.GET.get('prioridad', '')
    if prioridad_filtro:
        ordenes = ordenes.filter(prioridad=prioridad_filtro)

    tecnico_filtro = request.GET.get('tecnico', '')
    if tecnico_filtro and request.user.rol_principal == 'ADMIN':
        ordenes = ordenes.filter(tecnico_id=tecnico_filtro)

    equipo_filtro = request.GET.get('equipo', '')
    if equipo_filtro:
        ordenes = ordenes.filter(equipo_id=equipo_filtro)

    orden = request.GET.get('orden', '-fecha_programada')
    ordenes = ordenes.order_by(orden)

    paginator = Paginator(ordenes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    base_qs = OrdenTrabajo.objects.all()
    if request.user.rol_principal == 'TECNICO':
        base_qs = base_qs.filter(tecnico=request.user)

    total_ordenes = base_qs.count()
    programadas = base_qs.filter(estado='PROGRAMADA').count()
    en_progreso = base_qs.filter(estado='PROGRESO').count()
    completadas = base_qs.filter(estado='COMPLETADA').count()

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado_filtro,
        'tipo_filtro': tipo_filtro,
        'prioridad_filtro': prioridad_filtro,
        'tecnico_filtro': tecnico_filtro,
        'equipo_filtro': equipo_filtro,
        'orden': orden,
        'estados': OrdenTrabajo.ESTADO_CHOICES,
        'tipos': OrdenTrabajo.TIPO_CHOICES,
        'prioridades': OrdenTrabajo.PRIORIDAD_CHOICES,
        'tecnicos': User.objects.filter(rol_principal='TECNICO', is_active=True),
        'equipos': Equipo.objects.all().order_by('codigo_interno'),
        'query_params': query_params.urlencode(),
        'total_ordenes': total_ordenes,
        'programadas': programadas,
        'en_progreso': en_progreso,
        'completadas': completadas,
    }
    return render(request, 'mantenimiento/ordenes/lista_ordenes.html', context)


@login_required
def detalle_orden(request, orden_id):
    """Vista detallada de una orden con posibilidad de añadir repuestos."""
    if request.user.rol_principal not in ['TECNICO', 'ADMIN']:
        return redirect('mantenimiento:redirigir_por_rol')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if request.user.rol_principal == 'TECNICO' and orden.tecnico != request.user:
        messages.error(request, 'No tienes permiso para ver esta orden.')
        return redirect('mantenimiento:lista_ordenes')

    puede_editar_repuestos = orden.estado in ['PROGRAMADA', 'PROGRESO']

    if request.method == 'POST' and puede_editar_repuestos:
        formset = OrdenRepuestoFormSet(request.POST, instance=orden)
        if formset.is_valid():
            formset.save()
            messages.success(request, '✅ Repuestos actualizados.')
            return redirect('mantenimiento:detalle_orden', orden_id=orden.id)
    else:
        formset = OrdenRepuestoFormSet(instance=orden)

    repuestos_usados = orden.repuestos_usados.select_related('repuesto')
    repuestos_disponibles = Repuesto.objects.filter(cantidad_actual__gt=0)

    context = {
        'orden': orden,
        'formset': formset,
        'repuestos_usados': repuestos_usados,
        'repuestos_disponibles': repuestos_disponibles,
        'puede_editar_repuestos': puede_editar_repuestos,
    }
    return render(request, 'mantenimiento/ordenes/detalle_orden.html', context)


@login_required
def crear_orden(request):
    """Crear una nueva orden de trabajo (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear órdenes.')
        return redirect('mantenimiento:lista_ordenes')

    if request.method == 'POST':
        form = OrdenTrabajoForm(request.POST)
        if form.is_valid():
            orden = form.save()
            messages.success(request, f'✅ Orden OT-{orden.id} creada correctamente.')
            return redirect('mantenimiento:detalle_orden', orden_id=orden.id)
    else:
        initial = {}
        if request.GET.get('equipo'):
            initial['equipo'] = request.GET.get('equipo')
        if request.GET.get('incidencia'):
            initial['incidencia'] = request.GET.get('incidencia')
        form = OrdenTrabajoForm(initial=initial)

    return render(request, 'mantenimiento/ordenes/form_orden.html', {
        'form': form,
        'titulo': 'Crear Nueva Orden de Trabajo',
        'accion': 'Crear Orden',
    })


@login_required
def editar_orden(request, orden_id):
    """Editar una orden (solo ADMIN, y solo si no está completada/cancelada)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden editar órdenes.')
        return redirect('mantenimiento:lista_ordenes')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if orden.estado in ['COMPLETADA', 'CANCELADA']:
        messages.error(request, f'No puedes editar una orden en estado "{orden.get_estado_display()}".')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    if request.method == 'POST':
        form = OrdenTrabajoForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save()
            messages.success(request, f'✅ Orden OT-{orden.id} actualizada.')
            return redirect('mantenimiento:detalle_orden', orden_id=orden.id)
    else:
        form = OrdenTrabajoForm(instance=orden)

    return render(request, 'mantenimiento/ordenes/form_orden.html', {
        'form': form,
        'orden': orden,
        'titulo': f'Editar: OT-{orden.id}',
        'accion': 'Guardar Cambios',
    })


@login_required
def eliminar_orden(request, orden_id):
    """Eliminar una orden (solo ADMIN y solo si no está completada)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden eliminar órdenes.')
        return redirect('mantenimiento:lista_ordenes')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if orden.estado == 'COMPLETADA':
        messages.error(request, 'No puedes eliminar una orden completada. Es parte del historial.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    if request.method == 'POST':
        orden_id_ant = orden.id
        orden.delete()
        messages.success(request, f'Orden OT-{orden_id_ant} eliminada correctamente.')
        return redirect('mantenimiento:lista_ordenes')

    return render(request, 'mantenimiento/ordenes/confirmar_eliminar.html', {'orden': orden})


@login_required
def cerrar_orden(request, orden_id):
    """Cerrar y aprobar una orden completada (solo ADMIN)."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden cerrar órdenes.')
        return redirect('mantenimiento:lista_ordenes')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if orden.estado != 'COMPLETADA':
        messages.error(request, 'Solo puedes cerrar órdenes que estén completadas.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    if orden.fecha_cierre:
        messages.warning(request, 'Esta orden ya fue cerrada anteriormente.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        orden.fecha_cierre = timezone.now()
        orden.observaciones_cierre = observaciones
        orden.save()
        messages.success(request, f'✅ Orden OT-{orden.id} cerrada y aprobada.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    return render(request, 'mantenimiento/ordenes/cerrar_orden.html', {'orden': orden})


@login_required
def cambiar_estado_orden(request, orden_id, nuevo_estado):
    """Cambia el estado de una orden y aplica la lógica de negocio asociada."""
    if request.user.rol_principal not in ['TECNICO', 'ADMIN']:
        return redirect('mantenimiento:redirigir_por_rol')

    orden = get_object_or_404(OrdenTrabajo, id=orden_id)

    if request.user.rol_principal == 'TECNICO' and orden.tecnico != request.user:
        messages.error(request, 'No tienes permiso para modificar esta orden.')
        return redirect('mantenimiento:dashboard_tecnico')

    estados_validos = ['PROGRAMADA', 'PROGRESO', 'COMPLETADA', 'CANCELADA']
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    ahora = timezone.now()
    equipo = orden.equipo

    if nuevo_estado == 'PROGRESO':
        orden.estado = 'PROGRESO'
        orden.fecha_inicio = ahora
        equipo.estado_operativo = 'MANTENIMIENTO'
        equipo.bloqueado = True
        messages.success(request, f'OT-{orden.id} iniciada. Equipo bloqueado en mantenimiento.')

    elif nuevo_estado == 'COMPLETADA':
        orden.estado = 'COMPLETADA'
        orden.fecha_fin = ahora
        if orden.fecha_inicio:
            delta = ahora - orden.fecha_inicio
            orden.duracion_horas = round(delta.total_seconds() / 3600, 2)
        equipo.estado_operativo = 'ACTIVO'
        equipo.bloqueado = False
        equipo.ultimo_mantenimiento = ahora
        if equipo.intervalo_mantenimiento_dias > 0:
            from datetime import timedelta
            equipo.proximo_mantenimiento = ahora + timedelta(days=equipo.intervalo_mantenimiento_dias)
        messages.success(request, f'OT-{orden.id} completada. Equipo disponible.')

    elif nuevo_estado == 'CANCELADA':
        orden.estado = 'CANCELADA'
        equipo.estado_operativo = 'ACTIVO'
        equipo.bloqueado = False
        messages.warning(request, f'OT-{orden.id} cancelada.')

    orden.save()
    equipo.save()

    return redirect('mantenimiento:dashboard_tecnico')


# =====================================================
# GESTIÓN DE INCIDENCIAS (Admin y Técnico)
# =====================================================

@login_required
def lista_incidencias_admin(request):
    """Lista completa de incidencias para admin y técnicos."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver esta sección.')
        return redirect('mantenimiento:redirigir_por_rol')

    incidencias = Incidencia.objects.select_related('equipo', 'operario').all()

    q = request.GET.get('q', '').strip()
    if q:
        incidencias = incidencias.filter(
            Q(descripcion_falla__icontains=q) |
            Q(equipo__codigo_interno__icontains=q) |
            Q(equipo__nombre__icontains=q) |
            Q(operario__first_name__icontains=q) |
            Q(operario__last_name__icontains=q)
        )

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        incidencias = incidencias.filter(estado=estado_filtro)

    prioridad_filtro = request.GET.get('prioridad', '')
    if prioridad_filtro:
        incidencias = incidencias.filter(prioridad=prioridad_filtro)

    equipo_filtro = request.GET.get('equipo', '')
    if equipo_filtro:
        incidencias = incidencias.filter(equipo_id=equipo_filtro)

    orden = request.GET.get('orden', '-fecha_reporte')
    incidencias = incidencias.order_by(orden)

    paginator = Paginator(incidencias, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total = Incidencia.objects.count()
    pendientes = Incidencia.objects.filter(estado='PENDIENTE').count()
    en_revision = Incidencia.objects.filter(estado='REVISION').count()
    resueltas = Incidencia.objects.filter(estado='RESUELTA').count()

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'q': q,
        'estado_filtro': estado_filtro,
        'prioridad_filtro': prioridad_filtro,
        'equipo_filtro': equipo_filtro,
        'orden': orden,
        'estados': Incidencia.ESTADO_CHOICES,
        'prioridades': Incidencia.PRIORIDAD_CHOICES,
        'equipos': Equipo.objects.all().order_by('codigo_interno'),
        'query_params': query_params.urlencode(),
        'total': total,
        'pendientes': pendientes,
        'en_revision': en_revision,
        'resueltas': resueltas,
    }
    return render(request, 'mantenimiento/incidencias/lista_incidencias_admin.html', context)


@login_required
def detalle_incidencia(request, incidencia_id):
    """Vista detallada de una incidencia con acciones."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver esta incidencia.')
        return redirect('mantenimiento:redirigir_por_rol')

    incidencia = get_object_or_404(Incidencia, id=incidencia_id)
    ordenes = incidencia.ordenes.select_related('tecnico', 'equipo').order_by('-fecha_programada')

    context = {
        'incidencia': incidencia,
        'ordenes': ordenes,
    }
    return render(request, 'mantenimiento/incidencias/detalle_incidencia.html', context)


@login_required
def cambiar_estado_incidencia(request, incidencia_id, nuevo_estado):
    """Cambia el estado de una incidencia con validaciones del flujo."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para modificar incidencias.')
        return redirect('mantenimiento:redirigir_por_rol')

    incidencia = get_object_or_404(Incidencia, id=incidencia_id)

    estados_validos = ['PENDIENTE', 'REVISION', 'RESUELTA', 'RECHAZADA']
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)

    if nuevo_estado == 'RECHAZADA' and request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden rechazar incidencias.')
        return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)

    tiene_orden_activa = incidencia.ordenes.exclude(estado='CANCELADA').exists()

    if nuevo_estado == 'RESUELTA' and tiene_orden_activa:
        messages.error(
            request,
            '❌ Esta incidencia tiene una Orden de Trabajo vinculada. '
            'Se marcará como RESUELTA automáticamente cuando el administrador cierre la OT.'
        )
        return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)

    if nuevo_estado == 'PENDIENTE' and incidencia.estado == 'RESUELTA' and tiene_orden_activa:
        messages.error(
            request,
            '❌ No puedes reabrir una incidencia que tiene una OT activa. '
            'Primero cancela la OT.'
        )
        return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)

    incidencia.estado = nuevo_estado
    incidencia.save()

    messages.success(
        request,
        f'✅ Incidencia #{incidencia.id} cambiada a "{incidencia.get_estado_display()}".'
    )
    return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)


@login_required
def crear_ot_desde_incidencia(request, incidencia_id):
    """Crea una Orden de Trabajo a partir de una incidencia."""
    if request.user.rol_principal != 'ADMIN':
        messages.error(request, 'Solo los administradores pueden crear OTs desde incidencias.')
        return redirect('mantenimiento:lista_incidencias_admin')

    incidencia = get_object_or_404(Incidencia, id=incidencia_id)

    if incidencia.ordenes.exists():
        messages.warning(request, 'Esta incidencia ya tiene una Orden de Trabajo asociada.')
        return redirect('mantenimiento:detalle_incidencia', incidencia_id=incidencia.id)

    if request.method == 'POST':
        tecnico_id = request.POST.get('tecnico', '')
        prioridad = request.POST.get('prioridad', 'MEDIA')
        fecha_programada_str = request.POST.get('fecha_programada', '')
        descripcion = request.POST.get('descripcion', '').strip()

        if not fecha_programada_str:
            messages.error(request, 'Debes indicar una fecha programada.')
            return redirect('mantenimiento:crear_ot_desde_incidencia', incidencia_id=incidencia.id)

        from datetime import datetime
        try:
            fecha_programada = datetime.fromisoformat(fecha_programada_str)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
            return redirect('mantenimiento:crear_ot_desde_incidencia', incidencia_id=incidencia.id)

        tecnico = None
        if tecnico_id:
            try:
                tecnico = User.objects.get(id=tecnico_id, rol_principal='TECNICO')
            except User.DoesNotExist:
                pass

        orden = OrdenTrabajo.objects.create(
            equipo=incidencia.equipo,
            tecnico=tecnico,
            incidencia=incidencia,
            tipo='CORRECTIVO',
            prioridad=prioridad,
            fecha_programada=fecha_programada,
            descripcion_trabajo=descripcion or f"Reparación por incidencia #{incidencia.id}: {incidencia.descripcion_falla}",
            estado='PROGRAMADA',
        )

        incidencia.estado = 'REVISION'
        incidencia.save()

        messages.success(request, f'✅ Se creó la OT-{orden.id} desde la incidencia #{incidencia.id}.')
        return redirect('mantenimiento:detalle_orden', orden_id=orden.id)

    from datetime import timedelta
    context = {
        'incidencia': incidencia,
        'tecnicos': User.objects.filter(rol_principal='TECNICO', is_active=True),
        'prioridades': OrdenTrabajo.PRIORIDAD_CHOICES,
        'fecha_sugerida': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
    }
    return render(request, 'mantenimiento/incidencias/crear_ot_desde_incidencia.html', context)