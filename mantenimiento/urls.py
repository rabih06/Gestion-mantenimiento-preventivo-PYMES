from django.urls import path
from . import views

app_name = 'mantenimiento'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('redirigir/', views.redirigir_por_rol, name='redirigir_por_rol'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('dashboard/operario/', views.dashboard_operario, name='dashboard_operario'),
    #Incidencias (Operario)
    path('incidencias/', views.lista_incidencias, name='lista_incidencias'),
    path('incidencias/reportar/', views.reportar_incidencia, name='reportar_incidencia'),
    #Ordenes de trabajo (Técnico)
    path('ordenes/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
    path('ordenes/<int:orden_id>/cambiar/<str:nuevo_estado>/', views.cambiar_estado_orden, name='cambiar_estado_orden'),
    #Alertas automatizadas
    path('alertas/', views.lista_alertas, name='lista_alertas'),
    path('alertas/<int:alerta_id>/leer/', views.marcar_alerta_leida, name='marcar_alerta_leida'),
    path('alertas/marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('alertas/<int:alerta_id>/eliminar/', views.eliminar_alerta, name='eliminar_alerta'),
    # Equipos
    path('equipos/', views.lista_equipos, name='lista_equipos'),
    path('equipos/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipos/<int:equipo_id>/', views.detalle_equipo, name='detalle_equipo'),
    path('equipos/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipos/<int:equipo_id>/eliminar/', views.eliminar_equipo, name='eliminar_equipo'),
    # Repuestos
    path('repuestos/', views.lista_repuestos, name='lista_repuestos'),
    path('repuestos/crear/', views.crear_repuesto, name='crear_repuesto'),
    path('repuestos/<int:repuesto_id>/', views.detalle_repuesto, name='detalle_repuesto'),
    path('repuestos/<int:repuesto_id>/editar/', views.editar_repuesto, name='editar_repuesto'),
    path('repuestos/<int:repuesto_id>/eliminar/', views.eliminar_repuesto, name='eliminar_repuesto'),
]