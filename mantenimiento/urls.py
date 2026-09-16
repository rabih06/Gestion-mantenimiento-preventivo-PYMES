from django.urls import path
from . import views

app_name = 'mantenimiento'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('redirigir/', views.redirigir_por_rol, name='redirigir_por_rol'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('dashboard/operario/', views.dashboard_operario, name='dashboard_operario'),
]