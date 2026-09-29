from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Proveedor, Repuesto, CategoriaEquipo, Equipo,
    PlanMantenimiento, Incidencia, OrdenTrabajo, OrdenRepuesto,
    HistorialEstadoEquipo, Alerta, AtributoEquipo
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol_principal', 'departamento', 'is_staff')
    list_filter = ('rol_principal', 'departamento', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Solo añadimos NUESTROS campos personalizados.
    # 'groups' y 'user_permissions' ya vienen en UserAdmin.fieldsets por defecto.
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('rol_principal', 'telefono', 'departamento'),
            'description': 'El grupo se asigna automáticamente según el rol principal. '
                           'Los permisos individuales extra se gestionan en la sección "Permisos".'
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('rol_principal', 'telefono', 'departamento')
        }),
    )


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'is_active', 'total_repuestos')
    list_filter = ('is_active',)
    search_fields = ('nombre', 'email', 'contacto')
    fieldsets = (
        ('Información de la empresa', {
            'fields': ('nombre', 'direccion', 'is_active')
        }),
        ('Persona de contacto', {
            'fields': ('contacto', 'telefono', 'email'),
            'description': 'Datos de la persona con quien se coordinan los pedidos.'
        }),
    )

    def total_repuestos(self, obj):
        return obj.repuestos.count()
    total_repuestos.short_description = 'Repuestos'


@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('codigo_sku', 'nombre', 'cantidad_actual', 'stock_minimo', 'proveedor', 'stock_bajo')
    list_filter = ('proveedor',)
    search_fields = ('codigo_sku', 'nombre')

    def stock_bajo(self, obj):
        return obj.stock_bajo
    stock_bajo.boolean = True
    stock_bajo.short_description = '¿Stock bajo?'


@admin.register(CategoriaEquipo)
class CategoriaEquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

class AtributoEquipoInline(admin.TabularInline):
    model = AtributoEquipo
    extra = 1
    fields = ('nombre', 'valor', 'unidad')
    verbose_name = 'Atributo técnico'
    verbose_name_plural = 'Atributos técnicos'

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('codigo_interno', 'nombre', 'categoria', 'marca',
                    'estado_operativo', 'bloqueado', 'responsable')
    list_filter = ('estado_operativo', 'bloqueado', 'categoria', 'marca')
    search_fields = ('codigo_interno', 'nombre', 'numero_serie')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AtributoEquipoInline]


@admin.register(PlanMantenimiento)
class PlanMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'equipo', 'frecuencia_dias', 'frecuencia_uso', 'proxima_ejecucion', 'is_active')
    list_filter = ('is_active', 'equipo')
    search_fields = ('nombre', 'equipo__codigo_interno')


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'operario', 'prioridad', 'estado', 'fecha_reporte')
    list_filter = ('estado', 'prioridad', 'fecha_reporte')
    search_fields = ('equipo__codigo_interno', 'descripcion_falla')
    readonly_fields = ('fecha_reporte',)


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'tecnico', 'tipo', 'prioridad', 'estado', 'fecha_programada', 'generada_por_sistema')
    list_filter = ('tipo', 'estado', 'prioridad', 'generada_por_sistema')
    search_fields = ('equipo__codigo_interno', 'descripcion_trabajo')


@admin.register(OrdenRepuesto)
class OrdenRepuestoAdmin(admin.ModelAdmin):
    list_display = ('orden', 'repuesto', 'cantidad_utilizada', 'precio_unitario_momento')
    search_fields = ('orden__id', 'repuesto__nombre')


@admin.register(HistorialEstadoEquipo)
class HistorialEstadoEquipoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'estado_anterior', 'estado_nuevo', 'fecha_cambio', 'orden')
    list_filter = ('estado_nuevo', 'fecha_cambio')
    search_fields = ('equipo__codigo_interno',)
    readonly_fields = ('fecha_cambio',)


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'mensaje_corto', 'leida', 'created_at')
    list_filter = ('tipo', 'leida', 'created_at')
    search_fields = ('mensaje',)
    readonly_fields = ('created_at',)

    def mensaje_corto(self, obj):
        return obj.mensaje[:60]
    mensaje_corto.short_description = 'Mensaje'