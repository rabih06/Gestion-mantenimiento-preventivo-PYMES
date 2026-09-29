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
)
from .forms import (
    IncidenciaForm, EquipoForm, AtributoEquipoFormSet, RepuestoForm,
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

from .models import Alerta


@login_required
def lista_alertas(request):
    """Lista todas las alertas con filtros."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver las alertas.')
        return redirect('mantenimiento:redirigir_por_rol')

    alertas = Alerta.objects.select_related('repuesto', 'equipo', 'plan').order_by('-created_at')

    # Filtros por query params
    tipo_filtro = request.GET.get('tipo', '')
    estado_filtro = request.GET.get('estado', '')

    if tipo_filtro:
        alertas = alertas.filter(tipo=tipo_filtro)

    if estado_filtro == 'leidas':
        alertas = alertas.filter(leida=True)
    elif estado_filtro == 'no_leidas':
        alertas = alertas.filter(leida=False)

    # Contadores para las tarjetas de resumen
    total_alertas = Alerta.objects.count()
    no_leidas = Alerta.objects.filter(leida=False).count()
    leidas = Alerta.objects.filter(leida=True).count()

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
    """Marca una alerta como leída."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        return redirect('mantenimiento:redirigir_por_rol')

    alerta = get_object_or_404(Alerta, id=alerta_id)
    alerta.leida = True
    alerta.save()
    messages.success(request, 'Alerta marcada como leída.')

    # Volver a donde estaba el usuario
    return redirect(request.META.get('HTTP_REFERER', 'mantenimiento:lista_alertas'))


@login_required
def marcar_todas_leidas(request):
    """Marca todas las alertas como leídas."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        return redirect('mantenimiento:redirigir_por_rol')

    if request.method == 'POST':
        cantidad = Alerta.objects.filter(leida=False).update(leida=True)
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

    # ✅ FILTRO POR ROL: Operario solo ve sus equipos o los sin responsable
    if request.user.rol_principal == 'OPERARIO':
        equipos = equipos.filter(
            Q(responsable=request.user) | Q(responsable__isnull=True)
        )
    # ADMIN y TECNICO ven todos

    # ... el resto de la función (búsqueda, filtros, paginación) queda igual

    # Búsqueda por texto
    q = request.GET.get('q', '').strip()
    if q:
        equipos = equipos.filter(
            Q(codigo_interno__icontains=q) |
            Q(nombre__icontains=q) |
            Q(numero_serie__icontains=q) |
            Q(marca__icontains=q)
        )

    # Filtros
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

    # Ordenamiento
    orden = request.GET.get('orden', 'codigo_interno')
    equipos = equipos.order_by(orden)

    # Paginación
    paginator = Paginator(equipos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Mantener los filtros al cambiar de página
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

    # ✅ VALIDACIÓN: Operario solo puede ver equipos suyos o sin responsable
    if request.user.rol_principal == 'OPERARIO':
        if equipo.responsable and equipo.responsable != request.user:
            messages.error(
                request,
                'No tienes permiso para ver este equipo. '
                'Solo puedes consultar los equipos bajo tu responsabilidad.'
            )
            return redirect('mantenimiento:lista_equipos')

    # Historiales relacionados
    ordenes = equipo.ordenes.select_related('tecnico').order_by('-fecha_programada')[:10]
    incidencias = equipo.incidencias.select_related('operario').order_by('-fecha_reporte')[:10]
    planes = equipo.planes.filter(is_active=True)
    atributos = equipo.atributos.all()
    historial_estados = equipo.historial_estados.order_by('-fecha_cambio')[:10]
    alertas = equipo.alertas.filter(leida=False).order_by('-created_at')[:5]

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

    # Validar que no tenga órdenes activas
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

    # Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        repuestos = repuestos.filter(
            Q(codigo_sku__icontains=q) |
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )

    # Filtro por proveedor
    proveedor_filtro = request.GET.get('proveedor', '')
    if proveedor_filtro:
        repuestos = repuestos.filter(proveedor_id=proveedor_filtro)

    # Filtro por stock bajo
    stock_filtro = request.GET.get('stock', '')
    if stock_filtro == 'bajo':
        # Filtrar en Python porque el stock_bajo es una property
        repuestos = [r for r in repuestos if r.stock_bajo]
    elif stock_filtro == 'normal':
        repuestos = [r for r in repuestos if not r.stock_bajo]

    # Ordenamiento
    orden = request.GET.get('orden', 'nombre')
    if isinstance(repuestos, list):
        repuestos = sorted(repuestos, key=lambda x: getattr(x, orden, ''))
    else:
        repuestos = repuestos.order_by(orden)

    # Paginación
    paginator = Paginator(repuestos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contadores
    total_repuestos = Repuesto.objects.count()
    repuestos_criticos = sum(1 for r in Repuesto.objects.all() if r.stock_bajo)

    # Query params
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
    }
    return render(request, 'mantenimiento/repuestos/lista_repuestos.html', context)


@login_required
def detalle_repuesto(request, repuesto_id):
    """Vista detallada de un repuesto."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
        messages.error(request, 'No tienes permiso para ver los repuestos.')
        return redirect('mantenimiento:redirigir_por_rol')

    repuesto = get_object_or_404(Repuesto, id=repuesto_id)

    # Órdenes donde se ha usado este repuesto
    usos = repuesto.ordenes_usadas.select_related('orden', 'orden__equipo').order_by('-created_at')[:20]

    # Alertas activas de este repuesto
    alertas = repuesto.alertas.filter(leida=False).order_by('-created_at')

    # Calcular estadísticas
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
    """Editar un repuesto (ADMIN y TECNICO)."""
    if request.user.rol_principal not in ['ADMIN', 'TECNICO']:
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

    # Validar que no esté en uso en órdenes activas
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
