from django import forms
from django.forms import inlineformset_factory, TextInput
from .models import (
    Incidencia, Equipo, User, AtributoEquipo,
    Repuesto, Proveedor,
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