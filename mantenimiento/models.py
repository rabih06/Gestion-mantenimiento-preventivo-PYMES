# apps/core/models.py (o apps/maintenance/models.py)

from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings

class User(AbstractUser):
    telefono = models.CharField(max_length=20, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    # roles via groups

class Proveedor(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    direccion = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Repuesto(models.Model):
    nombre = models.CharField(max_length=150)
    codigo_sku = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cantidad_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    ubicacion_almacen = models.CharField(max_length=100, blank=True, null=True)
    unidad_medida = models.CharField(max_length=20, default='unidad')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, related_name='repuestos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Equipo(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('FUERA_SERVICIO', 'Fuera de Servicio'),
        ('BAJA', 'Dado de Baja'),
    ]
    codigo_interno = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    fecha_compra = models.DateField(blank=True, null=True)
    fecha_instalacion = models.DateField(blank=True, null=True)
    intervalo_mantenimiento_dias = models.IntegerField(default=0)
    estado_operativo = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    especificaciones_tecnicas = models.JSONField(default=dict, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_asignados')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Incidencia(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('REVISION', 'En Revisión'),
        ('RESUELTA', 'Resuelta'),
        ('RECHAZADA', 'Rechazada'),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='incidencias')
    operario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='incidencias_reportadas')
    descripcion_falla = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrdenTrabajo(models.Model):
    TIPO_CHOICES = [
        ('PREVENTIVO', 'Preventivo'),
        ('CORRECTIVO', 'Correctivo'),
        ('EMERGENCIA', 'Emergencia'),
    ]
    ESTADO_CHOICES = [
        ('PROGRAMADA', 'Programada'),
        ('PROGRESO', 'En Progreso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='ordenes')
    tecnico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ordenes_asignadas')
    incidencia = models.ForeignKey(Incidencia, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    fecha_programada = models.DateTimeField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    duracion_horas = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    descripcion_trabajo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADA')
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generada_por_sistema = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrdenRepuesto(models.Model):
    orden = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='repuestos_usados')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='ordenes_usadas')
    cantidad_utilizada = models.IntegerField()
    precio_unitario_momento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('orden', 'repuesto'),)

