from django.contrib import admin
from .models import Proveedor, Repuesto, Equipo, Incidencia, OrdenTrabajo, OrdenRepuesto

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'is_active')
    search_fields = ('nombre', 'email')

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_sku', 'cantidad_actual', 'stock_minimo', 'proveedor')
    list_filter = ('proveedor',)
    search_fields = ('nombre', 'codigo_sku')

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('codigo_interno', 'nombre', 'marca', 'estado_operativo', 'responsable')
    list_filter = ('estado_operativo', 'marca')
    search_fields = ('codigo_interno', 'nombre', 'numero_serie')

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'operario', 'estado', 'fecha_reporte')
    list_filter = ('estado', 'fecha_reporte')
    search_fields = ('equipo__nombre', 'descripcion_falla')

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'tecnico', 'tipo', 'prioridad', 'estado', 'fecha_programada')
    list_filter = ('tipo', 'estado', 'prioridad')
    search_fields = ('equipo__nombre', 'descripcion_trabajo')

@admin.register(OrdenRepuesto)
class OrdenRepuestoAdmin(admin.ModelAdmin):
    list_display = ('orden', 'repuesto', 'cantidad_utilizada')
    search_fields = ('orden__id', 'repuesto__nombre')