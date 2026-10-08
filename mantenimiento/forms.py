from django import forms
from django.forms import inlineformset_factory, TextInput
from .models import (
    Incidencia, Equipo, User, AtributoEquipo,
    Repuesto, Proveedor, PlanMantenimiento,OrdenTrabajo, OrdenRepuesto
)


# =====================================================
# FORMULARIO DE INCIDENCIAS
# =====================================================
class IncidenciaForm(forms.ModelForm):
    """Formulario para que los operarios reporten fallas."""

    class Meta:
        model = Incidencia
        fields = ['equipo', 'descripcion_falla', 'prioridad']
        widgets = {
            'equipo': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'descripcion_falla': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe qué está fallando, qué ruidos extraños escuchas, '
                               'qué comportamiento anormal notas, etc.',
                'required': True,
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'equipo': 'Equipo afectado',
            'descripcion_falla': 'Descripción de la falla',
            'prioridad': 'Prioridad',
        }
        help_texts = {
            'equipo': 'Selecciona el equipo donde detectaste el problema.',
            'prioridad': 'Elige "Crítica" si el equipo está detenido o es peligroso.',
        }

    def clean_descripcion_falla(self):
        descripcion = self.cleaned_data.get('descripcion_falla', '').strip()
        if len(descripcion) < 10:
            raise forms.ValidationError(
                'La descripción es demasiado corta. Mínimo 10 caracteres.'
            )
        return descripcion


# =====================================================
# FORMULARIO DE EQUIPOS
# =====================================================
class EquipoForm(forms.ModelForm):
    """Formulario para crear y editar equipos."""

    class Meta:
        model = Equipo
        fields = [
            'codigo_interno', 'nombre', 'categoria', 'marca', 'modelo',
            'numero_serie', 'fecha_compra', 'fecha_instalacion',
            'intervalo_mantenimiento_dias', 'tipo_intervalo',
            'estado_operativo', 'bloqueado', 'responsable',
        ]
        widgets = {
            'codigo_interno': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_instalacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'intervalo_mantenimiento_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tipo_intervalo': forms.Select(attrs={'class': 'form-select'}),
            'estado_operativo': forms.Select(attrs={'class': 'form-select'}),
            'bloqueado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'codigo_interno': 'Código interno *',
            'nombre': 'Nombre del equipo *',
            'intervalo_mantenimiento_dias': 'Intervalo de mantenimiento',
            'tipo_intervalo': 'Unidad del intervalo',
            'bloqueado': 'Bloqueado (no disponible para uso)',
        }
        help_texts = {
            'codigo_interno': 'Código único para identificar el equipo (ej: MAQ-001).',
            'intervalo_mantenimiento_dias': 'Valor numérico del intervalo (0 = no aplica).',
            'tipo_intervalo': 'Días, horas de uso o kilómetros.',
            'responsable': 'Usuario responsable del equipo (opcional).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar usuarios con rol OPERARIO en el campo responsable
        self.fields['responsable'].queryset = User.objects.filter(
            rol_principal='OPERARIO',
            is_active=True,
        ).order_by('first_name', 'last_name', 'username')
        self.fields['responsable'].required = False

    def clean_intervalo_mantenimiento_dias(self):
        intervalo = self.cleaned_data.get('intervalo_mantenimiento_dias', 0)
        if intervalo < 0:
            raise forms.ValidationError('El intervalo no puede ser negativo.')
        return intervalo

    def clean_codigo_interno(self):
        codigo = self.cleaned_data.get('codigo_interno', '').strip().upper()
        qs = Equipo.objects.filter(codigo_interno=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un equipo con este código.')
        return codigo


# =====================================================
# FORMSET DE ATRIBUTOS TÉCNICOS
# =====================================================
AtributoEquipoFormSet = inlineformset_factory(
    Equipo,
    AtributoEquipo,
    fields=['nombre', 'valor', 'unidad'],
    extra=3,
    can_delete=True,
    widgets={
        'nombre': TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Voltaje'}),
        'valor': TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 220'}),
        'unidad': TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: V'}),
    },
)


# =====================================================
# FORMULARIO DE REPUESTOS
# =====================================================
class RepuestoForm(forms.ModelForm):
    """Formulario para crear y editar repuestos."""

    class Meta:
        model = Repuesto
        fields = [
            'codigo_sku', 'nombre', 'descripcion', 'cantidad_actual',
            'stock_minimo', 'ubicacion_almacen', 'unidad_medida',
            'precio_unitario', 'proveedor',
        ]
        widgets = {
            'codigo_sku': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cantidad_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ubicacion_almacen': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'codigo_sku': 'Código SKU *',
            'nombre': 'Nombre del repuesto *',
            'cantidad_actual': 'Cantidad actual en stock',
            'stock_minimo': 'Stock mínimo',
            'ubicacion_almacen': 'Ubicación en almacén',
            'unidad_medida': 'Unidad de medida',
            'precio_unitario': 'Precio unitario',
        }
        help_texts = {
            'codigo_sku': 'Código único del repuesto (ej: REP-001).',
            'stock_minimo': 'Cuando el stock baje de este valor, se generará una alerta.',
            'unidad_medida': 'Ej: unidad, metro, litro, kg.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(is_active=True).order_by('nombre')
        self.fields['proveedor'].required = False

    def clean_codigo_sku(self):
        codigo = self.cleaned_data.get('codigo_sku', '').strip().upper()
        qs = Repuesto.objects.filter(codigo_sku=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un repuesto con este código SKU.')
        return codigo

    def clean(self):
        cleaned = super().clean()
        cantidad = cleaned.get('cantidad_actual', 0)
        minimo = cleaned.get('stock_minimo', 0)
        if cantidad < 0 or minimo < 0:
            raise forms.ValidationError('Las cantidades no pueden ser negativas.')
        return cleaned

    # =====================================================
# FORMULARIO DE PROVEEDORES
# =====================================================
class ProveedorForm(forms.ModelForm):
    """Formulario para crear y editar proveedores."""

    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la empresa *',
            'contacto': 'Persona de contacto',
            'telefono': 'Teléfono',
            'email': 'Correo electrónico',
            'direccion': 'Dirección',
            'is_active': 'Proveedor activo',
        }
        help_texts = {
            'nombre': 'Nombre comercial de la empresa proveedora.',
            'contacto': 'Nombre del vendedor o persona con quien coordinas los pedidos.',
            'telefono': 'Número de teléfono del contacto.',
            'email': 'Correo para enviar órdenes de compra.',
            'is_active': 'Desmarca si el proveedor ya no está disponible.',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        qs = Proveedor.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un proveedor con este nombre.')
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = Proveedor.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un proveedor con este correo.')
        return email
    
# =====================================================
# FORMULARIO DE PLANES DE MANTENIMIENTO
# =====================================================
class PlanMantenimientoForm(forms.ModelForm):
    """Formulario para crear y editar planes de mantenimiento preventivo."""

    class Meta:
        model = PlanMantenimiento
        fields = [
            'equipo', 'tecnico_asignado', 'nombre', 'descripcion',
            'frecuencia_dias', 'frecuencia_uso',
            'ultima_ejecucion', 'is_active',
        ]
        widgets = {
            'equipo': forms.Select(attrs={'class': 'form-select'}),
            'tecnico_asignado': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'frecuencia_dias': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'frecuencia_uso': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ultima_ejecucion': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'equipo': 'Equipo *',
            'tecnico_asignado': 'Técnico responsable',
            'nombre': 'Nombre del plan *',
            'descripcion': 'Descripción del trabajo a realizar *',
            'frecuencia_dias': 'Frecuencia (días)',
            'frecuencia_uso': 'Frecuencia por uso (horas/km)',
            'ultima_ejecucion': 'Última ejecución',
            'is_active': 'Plan activo',
        }
        help_texts = {
            'equipo': 'Equipo al que aplica este plan.',
            'tecnico_asignado': 'Se le asignará automáticamente al aplicar el plan. Opcional.',
            'nombre': 'Ej: "Cambio de aceite y filtros".',
            'descripcion': 'Detalle las tareas a realizar.',
            'frecuencia_dias': 'Cada cuántos días debe ejecutarse (0 = no aplica).',
            'frecuencia_uso': 'Opcional: cada cuántas horas o km (0 o vacío = no aplica).',
            'ultima_ejecucion': 'Déjalo vacío si es la primera vez. Se usará la fecha actual.',
            'is_active': 'Desmarca para pausar el plan sin eliminarlo.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar técnicos activos en el campo tecnico_asignado
        self.fields['tecnico_asignado'].queryset = User.objects.filter(
            rol_principal='TECNICO',
            is_active=True,
        ).order_by('first_name', 'last_name', 'username')
        self.fields['tecnico_asignado'].required = False

    def clean(self):
        cleaned = super().clean()
        frecuencia_dias = cleaned.get('frecuencia_dias', 0) or 0
        frecuencia_uso = cleaned.get('frecuencia_uso') or 0

        if frecuencia_dias < 0:
            raise forms.ValidationError('La frecuencia en días no puede ser negativa.')
        if frecuencia_uso < 0:
            raise forms.ValidationError('La frecuencia por uso no puede ser negativa.')

        if frecuencia_dias == 0 and frecuencia_uso == 0:
            raise forms.ValidationError(
                'Debes especificar al menos una frecuencia: días o uso.'
            )

        return cleaned

# =====================================================
# FORMULARIO PARA RETIRAR REPUESTOS DEL INVENTARIO
# =====================================================
class RetirarRepuestoForm(forms.Form):
    """Formulario para que técnicos registren la salida de repuestos."""

    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'placeholder': 'Ej: 2',
        }),
        label='Cantidad a retirar *',
    )
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ej: Cambio de aceite en el torno CNC',
        }),
        label='Motivo de la salida',
    )

    def __init__(self, *args, **kwargs):
        self.repuesto = kwargs.pop('repuesto', None)
        super().__init__(*args, **kwargs)

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad', 0)
        if not self.repuesto:
            return cantidad
        if self.repuesto.cantidad_actual == 0:
            raise forms.ValidationError(
                f'❌ No puedes retirar: "{self.repuesto.nombre}" está sin stock.'
            )
        if cantidad > self.repuesto.cantidad_actual:
            raise forms.ValidationError(
                f'❌ Solo hay {self.repuesto.cantidad_actual} {self.repuesto.unidad_medida}(s) disponibles.'
            )
        return cantidad
# =====================================================
# FORMULARIO DE ORDEN DE TRABAJO
# =====================================================
class OrdenTrabajoForm(forms.ModelForm):
    """Formulario para crear y editar órdenes de trabajo."""

    class Meta:
        model = OrdenTrabajo
        fields = [
            'equipo', 'tecnico', 'incidencia', 'plan',
            'tipo', 'prioridad', 'fecha_programada',
            'descripcion_trabajo',
        ]
        widgets = {
            'equipo': forms.Select(attrs={'class': 'form-select'}),
            'tecnico': forms.Select(attrs={'class': 'form-select'}),
            'incidencia': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'fecha_programada': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'descripcion_trabajo': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
        }
        labels = {
            'equipo': 'Equipo *',
            'tecnico': 'Técnico asignado',
            'incidencia': 'Incidencia origen',
            'plan': 'Plan de mantenimiento',
            'tipo': 'Tipo de trabajo *',
            'prioridad': 'Prioridad *',
            'fecha_programada': 'Fecha programada *',
            'descripcion_trabajo': 'Descripción del trabajo *',
        }
        help_texts = {
            'equipo': 'Equipo al que se le realizará el mantenimiento.',
            'tecnico': 'Técnico responsable de ejecutar la orden.',
            'incidencia': 'Si la OT nace de un reporte de falla, selecciónala aquí.',
            'plan': 'Si la OT viene de un plan preventivo, selecciónalo aquí.',
            'descripcion_trabajo': 'Detalla las tareas a realizar.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar técnicos activos
        self.fields['tecnico'].queryset = User.objects.filter(
            rol_principal='TECNICO', is_active=True
        ).order_by('first_name', 'last_name', 'username')
        self.fields['tecnico'].required = False

        # Solo incidencias pendientes o en revisión
        self.fields['incidencia'].queryset = Incidencia.objects.filter(
            estado__in=['PENDIENTE', 'REVISION']
        ).order_by('-fecha_reporte')
        self.fields['incidencia'].required = False

        # Solo planes activos
        self.fields['plan'].queryset = PlanMantenimiento.objects.filter(
            is_active=True
        ).order_by('equipo__codigo_interno', 'nombre')
        self.fields['plan'].required = False

        # Si estamos editando, incluir el técnico actual por si está inactivo
        if self.instance.pk and self.instance.tecnico:
            tecnicos_qs = self.fields['tecnico'].queryset
            self.fields['tecnico'].queryset = (tecnicos_qs | User.objects.filter(pk=self.instance.tecnico.pk)).distinct()

    def clean(self):
        cleaned = super().clean()
        equipo = cleaned.get('equipo')
        incidencia = cleaned.get('incidencia')
        plan = cleaned.get('plan')

        # Validar que la incidencia sea del mismo equipo si se selecciona
        if incidencia and equipo and incidencia.equipo != equipo:
            self.add_error('incidencia', 'La incidencia seleccionada no corresponde al equipo elegido.')

        # Validar que el plan sea del mismo equipo si se selecciona
        if plan and equipo and plan.equipo != equipo:
            self.add_error('plan', 'El plan seleccionado no corresponde al equipo elegido.')

        return cleaned


# =====================================================
# FORMULARIO DE REPUESTO USADO EN ORDEN
# =====================================================
class OrdenRepuestoForm(forms.ModelForm):
    """Formulario individual para añadir un repuesto a una OT."""

    class Meta:
        model = OrdenRepuesto
        fields = ['repuesto', 'cantidad_utilizada']
        widgets = {
            'repuesto': forms.Select(attrs={
                'class': 'form-select select2-searchable',
                'data-placeholder': 'Buscar repuesto por SKU o nombre...',
            }),
            'cantidad_utilizada': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Cantidad',
            }),
        }
        labels = {
            'repuesto': 'Repuesto',
            'cantidad_utilizada': 'Cantidad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Filtrar: solo repuestos con stock > 0 (o el ya seleccionado si edita)
        queryset = Repuesto.objects.filter(cantidad_actual__gt=0)

        # Si estamos editando una OrdenRepuesto existente, incluir su repuesto actual
        if self.instance.pk and self.instance.repuesto:
            from django.db.models import Q
            queryset = Repuesto.objects.filter(
                Q(cantidad_actual__gt=0) | Q(pk=self.instance.repuesto.pk)
            )

        self.fields['repuesto'].queryset = queryset.order_by('nombre')

        # ✅ Personalizar la etiqueta de cada opción: SKU - Nombre (Stock: X)
        self.fields['repuesto'].label_from_instance = lambda obj: (
            f"{obj.codigo_sku} | {obj.nombre} "
            f"(Stock: {obj.cantidad_actual} {obj.unidad_medida})"
        )

        # Hacer el campo no obligatorio si ya está marcado para eliminar
        # (permite guardar formset con filas vacías)


OrdenRepuestoFormSet = inlineformset_factory(
    OrdenTrabajo,
    OrdenRepuesto,
    form=OrdenRepuestoForm,
    extra=1,
    can_delete=True,
)