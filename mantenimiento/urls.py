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
]