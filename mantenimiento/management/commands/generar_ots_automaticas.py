"""
Management command para generar automáticamente Órdenes de Trabajo
a partir de planes de mantenimiento vencidos.

Uso:
    python manage.py generar_ots_automaticas
    python manage.py generar_ots_automaticas --dry-run
    python manage.py generar_ots_automaticas --dias-adelante 3
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from mantenimiento.models import (
    PlanMantenimiento, OrdenTrabajo, User, Alerta
)
from mantenimiento.utils import notificar


class Command(BaseCommand):
    help = 'Genera Órdenes de Trabajo automáticamente desde planes de mantenimiento vencidos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la generación sin crear OTs (útil para pruebas).',
        )
        parser.add_argument(
            '--dias-adelante',
            type=int,
            default=0,
            help='Generar también para planes que vencen en N días (default: 0 = solo vencidos).',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar detalle de cada OT generada.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dias_adelante = options['dias_adelante']
        verbose = options['verbose']

        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('  GENERACIÓN AUTOMÁTICA DE ÓRDENES DE TRABAJO'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN: No se crearán OTs'))
            self.stdout.write('')

        # Fecha límite
        hoy = timezone.now()
        fecha_limite = hoy + timedelta(days=dias_adelante)

        # Buscar planes activos con próxima ejecución vencida
        planes_vencidos = PlanMantenimiento.objects.filter(
            is_active=True,
            proxima_ejecucion__lte=fecha_limite,
            proxima_ejecucion__isnull=False,
        ).select_related('equipo', 'tecnico_asignado').order_by('proxima_ejecucion')

        total_planes = planes_vencidos.count()

        if total_planes == 0:
            self.stdout.write(self.style.SUCCESS('✅ No hay planes vencidos para procesar.'))
            return

        self.stdout.write(f'📋 Planes vencidos encontrados: {total_planes}')
        self.stdout.write('')

        creadas = 0
        omitidas_por_duplicado = 0
        errores = 0

        for plan in planes_vencidos:
            # ✅ Validar que no exista ya una OT activa para este plan
            ot_existente = OrdenTrabajo.objects.filter(
                plan=plan,
                estado__in=['PROGRAMADA', 'PROGRESO']
            ).exists()

            if ot_existente:
                omitidas_por_duplicado += 1
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⏭️  Omitida: {plan.nombre} ({plan.equipo.codigo_interno}) '
                            f'ya tiene OT activa'
                        )
                    )
                continue

            # ✅ Determinar el técnico a asignar
            tecnico = plan.tecnico_asignado  # Puede ser None

            # ✅ Crear la OT
            if not dry_run:
                try:
                    with transaction.atomic():
                        orden = OrdenTrabajo.objects.create(
                            equipo=plan.equipo,
                            tecnico=tecnico,
                            plan=plan,
                            tipo='PREVENTIVO',
                            prioridad='MEDIA',
                            fecha_programada=hoy,
                            descripcion_trabajo=(
                                f"[Plan Automático: {plan.nombre}]\n\n"
                                f"{plan.descripcion}"
                            ),
                            estado='PROGRAMADA',
                            generada_por_sistema=True,
                        )

                        # Actualizar plan
                        plan.ultima_ejecucion = hoy
                        plan.save()

                        # ✅ Notificar al admin y al técnico
                        mensaje = (
                            f"🤖 OT-{orden.id} generada automáticamente: "
                            f"{plan.nombre} en {plan.equipo.codigo_interno}"
                        )
                        usuarios_notif = list(User.objects.filter(
                            rol_principal='ADMIN', is_active=True
                        ))
                        if tecnico:
                            usuarios_notif.append(tecnico)

                        notificar(
                            tipo='OTRA',
                            mensaje=mensaje,
                            equipo=plan.equipo,
                            usuarios=usuarios_notif,
                            evitar_duplicados_minutos=0,
                        )

                        creadas += 1
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ OT-{orden.id} creada para {plan.equipo.codigo_interno} '
                                    f'(Técnico: {tecnico.get_full_name() if tecnico else "Sin asignar"})'
                                )
                            )
                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ Error al crear OT para {plan.nombre}: {str(e)}'
                        )
                    )
            else:
                creadas += 1
                if verbose:
                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f'  🔍 [DRY-RUN] Crearía OT: {plan.nombre} '
                            f'({plan.equipo.codigo_interno}) '
                            f'→ Técnico: {tecnico.get_full_name() if tecnico else "Sin asignar"}'
                        )
                    )

        # =====================================================
        # RESUMEN FINAL
        # =====================================================
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('  RESUMEN'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(f'  📋 Planes procesados: {total_planes}')
        self.stdout.write(
            self.style.SUCCESS(f'  ✅ OTs {"simuladas" if dry_run else "creadas"}: {creadas}')
        )
        if omitidas_por_duplicado > 0:
            self.stdout.write(
                self.style.WARNING(f'  ⏭️  Omitidas (ya tienen OT activa): {omitidas_por_duplicado}')
            )
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'  ❌ Errores: {errores}'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))