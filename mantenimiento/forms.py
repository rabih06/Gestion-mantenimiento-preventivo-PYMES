from django import forms
from .models import Incidencia


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