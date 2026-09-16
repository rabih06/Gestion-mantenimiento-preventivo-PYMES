from django.db import migrations
from django.contrib.auth.models import Group, Permission


def crear_grupos(apps, schema_editor):
    """Crea los grupos predefinidos con sus permisos base."""
    
    # =====================================================
    # GRUPO: ADMINISTRADORES (todos los permisos de la app)
    # =====================================================
    admin_group, _ = Group.objects.get_or_create(name='Administradores')
    permisos_admin = Permission.objects.filter(
        content_type__app_label='mantenimiento'
    )
    admin_group.permissions.set(permisos_admin)

    # =====================================================
    # GRUPO: TÉCNICOS
    # =====================================================
    tecnicos_group, _ = Group.objects.get_or_create(name='Técnicos')
    permisos_tecnicos = Permission.objects.filter(
        content_type__app_label='mantenimiento',
        codename__in=[
            'view_equipo', 'change_equipo',
            'view_repuesto', 'change_repuesto',
            'view_planmantenimiento', 'change_planmantenimiento',
            'view_incidencia', 'change_incidencia',
            'view_ordentrabajo', 'change_ordentrabajo',
            'add_ordenrepuesto', 'view_ordenrepuesto', 'change_ordenrepuesto',
            'view_historialestadoequipo',
            'view_alerta',
            'view_atributoequipo', 'change_atributoequipo',
        ]
    )
    tecnicos_group.permissions.set(permisos_tecnicos)

    # =====================================================
    # GRUPO: OPERARIOS
    # =====================================================
    operarios_group, _ = Group.objects.get_or_create(name='Operarios')
    permisos_operarios = Permission.objects.filter(
        content_type__app_label='mantenimiento',
        codename__in=[
            'add_incidencia', 'view_incidencia',
            'view_equipo',
        ]
    )
    operarios_group.permissions.set(permisos_operarios)


def eliminar_grupos(apps, schema_editor):
    """Revierte la creación de los grupos (por si se hace rollback)."""
    Group.objects.filter(
        name__in=['Administradores', 'Técnicos', 'Operarios']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mantenimiento', '0001_initial'),  # ← Ajusta al nombre real de tu migración inicial
        ('auth', '0012_alter_user_first_name_max_length'),  # ← Ajusta si tu versión es distinta
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
