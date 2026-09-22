from django import forms
from .models import Incidencia
from .models import Equipo, User
from django.forms import inlineformset_factory, TextInput
from .models import AtributoEquipo


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
        """Validación personalizada: la descripción debe tener al menos 10 caracteres."""
        descripcion = self.cleaned_data.get('descripcion_falla', '').strip()
        if len(descripcion) < 10:
            raise forms.ValidationError(
                'La descripción es demasiado corta. Mínimo 10 caracteres.'
            )
        return descripcion

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

# Formset para atributos técnicos (inline)
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