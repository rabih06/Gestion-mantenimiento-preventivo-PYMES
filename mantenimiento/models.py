from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator


# =====================================================
# USUARIO PERSONALIZADO
# =====================================================
class User(AbstractUser):
    ROL_CHOICES = [
        ('ADMIN', 'Administrador / Gerente'),
        ('TECNICO', 'Técnico de Mantenimiento'),
        ('OPERARIO', 'Operario / Trabajador'),
    ]
    rol_principal = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='OPERARIO',
        help_text="Rol principal para redirección de login"
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_principal_display()})"


# =====================================================
# PROVEEDORES
# =====================================================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    direccion = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# =====================================================
# REPUESTOS
# =====================================================
class Repuesto(models.Model):
    nombre = models.CharField(max_length=150)
    codigo_sku = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cantidad_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    ubicacion_almacen = models.CharField(max_length=100, blank=True, null=True)
    unidad_medida = models.CharField(max_length=20, default='unidad')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ultima_entrada = models.DateTimeField(null=True, blank=True)
    fecha_ultima_salida = models.DateTimeField(null=True, blank=True)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repuestos'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'repuestos'
        verbose_name = 'Repuesto'
        verbose_name_plural = 'Repuestos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo_sku} - {self.nombre}"

    @property
    def stock_bajo(self):
        return self.cantidad_actual <= self.stock_minimo


# =====================================================
# CATEGORÍA DE EQUIPOS
# =====================================================
class CategoriaEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'categorias_equipo'
        verbose_name = 'Categoría de Equipo'
        verbose_name_plural = 'Categorías de Equipos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# =====================================================
# EQUIPOS / MAQUINARIA
# =====================================================
class Equipo(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('FUERA_SERVICIO', 'Fuera de Servicio'),
        ('BAJA', 'Dado de Baja'),
    ]
    
    # ✅ NUEVO: Tipo de intervalo
    TIPO_INTERVALO_CHOICES = [
        ('DIAS', 'Días'),
        ('HORAS', 'Horas de uso'),
        ('KILOMETROS', 'Kilómetros'),
    ]

    # ✅ Renombramos para que sea más genérico
    intervalo_mantenimiento = models.IntegerField(
        default=0,
        help_text="Valor del intervalo (interpretado según el tipo)"
    )
    tipo_intervalo = models.CharField(
        max_length=15,
        choices=TIPO_INTERVALO_CHOICES,
        default='DIAS',
        help_text="Unidad del intervalo de mantenimiento"
    )

    codigo_interno = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    categoria = models.ForeignKey(
        CategoriaEquipo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipos'
    )
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    fecha_compra = models.DateField(blank=True, null=True)
    fecha_instalacion = models.DateField(blank=True, null=True)
    intervalo_mantenimiento_dias = models.IntegerField(default=0)
    estado_operativo = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVO'
    )
    bloqueado = models.BooleanField(
        default=False,
        help_text="Si está bloqueado, no se puede usar (ej. en mantenimiento)"
    )
    ultimo_mantenimiento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha del último mantenimiento completado"
    )
    proximo_mantenimiento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha programada del próximo mantenimiento preventivo"
    )
  
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipos_asignados'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
    # Solo calcular fecha próxima si el intervalo es en DÍAS
        if self.tipo_intervalo == 'DIAS' and self.ultimo_mantenimiento and self.intervalo_mantenimiento > 0:
            from datetime import timedelta
            self.proximo_mantenimiento = self.ultimo_mantenimiento + timedelta(days=self.intervalo_mantenimiento)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'equipos'
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['codigo_interno']

    def __str__(self):
        return f"{self.codigo_interno} - {self.nombre}"


# =====================================================
# PLANES DE MANTENIMIENTO PREVENTIVO
# =====================================================
class PlanMantenimiento(models.Model):
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='planes'
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    frecuencia_dias = models.IntegerField(
        help_text="Cada cuántos días debe ejecutarse (0 si solo se usa frecuencia por uso)"
    )
    frecuencia_uso = models.IntegerField(
        null=True,
        blank=True,
        help_text="Opcional: cada cuántas horas/km (según especificaciones del equipo)"
    )
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    proxima_ejecucion = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'planes_mantenimiento'
        verbose_name = 'Plan de Mantenimiento'
        verbose_name_plural = 'Planes de Mantenimiento'
        ordering = ['equipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.equipo.codigo_interno})"


# =====================================================
# INCIDENCIAS (Reportes de operarios)
# =====================================================
class Incidencia(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('REVISION', 'En Revisión'),
        ('RESUELTA', 'Resuelta'),
        ('RECHAZADA', 'Rechazada'),
    ]
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='incidencias')
    operario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='incidencias_reportadas'
    )
    descripcion_falla = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'incidencias'
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f"Incidencia #{self.id} - {self.equipo.codigo_interno} ({self.get_estado_display()})"


# =====================================================
# ÓRDENES DE TRABAJO
# =====================================================
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
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_asignadas'
    )
    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes'
    )
    plan = models.ForeignKey(
        PlanMantenimiento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_generadas',
        help_text="Plan de mantenimiento que originó esta orden (si aplica)"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    fecha_programada = models.DateTimeField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que el gerente aprobó el cierre"
    )
    duracion_horas = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    descripcion_trabajo = models.TextField()
    observaciones_cierre = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADA')
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generada_por_sistema = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ordenes_trabajo'
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Órdenes de Trabajo'
        ordering = ['-fecha_programada']

    def __str__(self):
        return f"OT-{self.id} ({self.equipo.codigo_interno}) - {self.get_estado_display()}"


# =====================================================
# DETALLE DE REPUESTOS USADOS EN UNA ORDEN
# =====================================================
class OrdenRepuesto(models.Model):
    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name='repuestos_usados'
    )
    repuesto = models.ForeignKey(
        Repuesto,
        on_delete=models.CASCADE,
        related_name='ordenes_usadas'
    )
    cantidad_utilizada = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario_momento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orden_repuestos'
        verbose_name = 'Repuesto usado en Orden'
        verbose_name_plural = 'Repuestos usados en Órdenes'
        unique_together = (('orden', 'repuesto'),)

    def __str__(self):
        return f"{self.orden} - {self.repuesto.nombre} x{self.cantidad_utilizada}"


# =====================================================
# HISTORIAL DE ESTADOS DE EQUIPO
# =====================================================
class HistorialEstadoEquipo(models.Model):
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    motivo = models.TextField(blank=True, null=True)
    orden = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cambios_estado'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_estados_equipo'
        verbose_name = 'Historial de Estado de Equipo'
        verbose_name_plural = 'Historial de Estados de Equipos'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.equipo.codigo_interno}: {self.estado_anterior} → {self.estado_nuevo} ({self.fecha_cambio:%Y-%m-%d %H:%M})"


# =====================================================
# ALERTAS GENERADAS POR EL SISTEMA AUTOMÁTICO
# =====================================================
class Alerta(models.Model):
    TIPO_CHOICES = [
        ('STOCK_BAJO', 'Stock bajo'),
        ('MANTENIMIENTO_PROXIMO', 'Mantenimiento próximo'),
        ('MANTENIMIENTO_VENCIDO', 'Mantenimiento vencido'),
        ('EQUIPO_CRITICO', 'Equipo en estado crítico'),
        ('OTRA', 'Otra'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    repuesto = models.ForeignKey(
        Repuesto,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    plan = models.ForeignKey(
        PlanMantenimiento,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alertas'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.mensaje[:50]}"

# =====================================================
# ATRIBUTOS DINÁMICOS DE EQUIPO (clave-valor)
# =====================================================
class AtributoEquipo(models.Model):
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='atributos'
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Ej: Voltaje, RPM, Kilometraje, Presión"
    )
    valor = models.CharField(
        max_length=255,
        help_text="Ej: 220, 3000, 120000, 150"
    )
    unidad = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Ej: V, rpm, km, psi"
    )

    class Meta:
        db_table = 'atributos_equipo'
        verbose_name = 'Atributo de Equipo'
        verbose_name_plural = 'Atributos de Equipo'
        unique_together = (('equipo', 'nombre'),)
        ordering = ['equipo', 'nombre']

    def __str__(self):
        return f"{self.equipo.codigo_interno} - {self.nombre}: {self.valor} {self.unidad or ''}"
