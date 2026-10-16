from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import (
    User, Repuesto, Proveedor, Equipo, CategoriaEquipo,
    OrdenTrabajo, OrdenRepuesto, PedidoProveedor, MovimientoRepuesto, Alerta
)


class SistemaRolesYAlmacenTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Usuarios con cada rol
        self.admin = User.objects.create_user(
            username='admin_user', password='password123', rol_principal='ADMIN'
        )
        self.owner = User.objects.create_user(
            username='owner_user', password='password123', rol_principal='OWNER'
        )
        self.almacen = User.objects.create_user(
            username='almacen_user', password='password123', rol_principal='ALMACEN'
        )
        self.tecnico = User.objects.create_user(
            username='tecnico_user', password='password123', rol_principal='TECNICO'
        )
        self.operario = User.objects.create_user(
            username='operario_user', password='password123', rol_principal='OPERARIO'
        )

        # Categoría y Equipo
        self.cat = CategoriaEquipo.objects.create(nombre='Maquinaria Pesada')
        self.equipo = Equipo.objects.create(
            codigo_interno='EQ-001',
            nombre='Torno CNC',
            categoria=self.cat,
            intervalo_mantenimiento=30,
            tipo_intervalo='DIAS',
            estado_operativo='ACTIVO'
        )

        # Proveedor y Repuesto
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Industrial S.A.',
            telefono='0414-1234567',
            email='ventas@industrial.com',
            direccion='Zona Industrial'
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de Aceite HF-6510',
            codigo_sku='REP-FLT-001',
            cantidad_actual=10,
            stock_minimo=2,
            precio_unitario=25.00,
            proveedor=self.proveedor
        )

        # Orden de Trabajo
        self.orden = OrdenTrabajo.objects.create(
            equipo=self.equipo,
            tecnico=self.tecnico,
            tipo='PREVENTIVO',
            prioridad='MEDIA',
            fecha_programada=timezone.now(),
            descripcion_trabajo='Mantenimiento preventivo general',
            estado='PROGRAMADA'
        )

    def test_redirecciones_por_rol(self):
        """Verifica que cada rol sea redirigido a su respectivo dashboard tras login."""
        roles_y_destinos = [
            (self.admin, reverse('mantenimiento:dashboard_admin')),
            (self.owner, reverse('mantenimiento:dashboard_owner')),
            (self.almacen, reverse('mantenimiento:dashboard_almacen')),
            (self.tecnico, reverse('mantenimiento:dashboard_tecnico')),
            (self.operario, reverse('mantenimiento:dashboard_operario')),
        ]

        for user, url_esperada in roles_y_destinos:
            self.client.force_login(user)
            response = self.client.get(reverse('mantenimiento:redirigir_por_rol'))
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, url_esperada)

    def test_tecnico_no_puede_retirar_repuesto_libremente(self):
        """El técnico no debe tener acceso libre a retirar repuestos de forma directa."""
        self.client.force_login(self.tecnico)
        response = self.client.get(reverse('mantenimiento:retirar_repuesto', args=[self.repuesto.id]))
        # Debe redirigir con mensaje de error bloqueando el acceso libre
        self.assertRedirects(response, reverse('mantenimiento:lista_repuestos'))

    def test_solicitud_repuesto_queda_pendiente(self):
        """Al enlazar un repuesto a la OT, queda en estado PENDIENTE sin descontar stock."""
        stock_inicial = self.repuesto.cantidad_actual

        solicitud = OrdenRepuesto.objects.create(
            orden=self.orden,
            repuesto=self.repuesto,
            cantidad_utilizada=3,
            estado='PENDIENTE',
            solicitado_por=self.tecnico
        )

        self.repuesto.refresh_from_db()
        # El stock no debe descontarse al crear la solicitud
        self.assertEqual(self.repuesto.cantidad_actual, stock_inicial)
        self.assertEqual(solicitud.estado, 'PENDIENTE')

    def test_administrador_almacen_da_salida_y_descuenta_stock(self):
        """El Administrador de Almacén autoriza la salida física descontando stock."""
        solicitud = OrdenRepuesto.objects.create(
            orden=self.orden,
            repuesto=self.repuesto,
            cantidad_utilizada=4,
            estado='PENDIENTE',
            solicitado_por=self.tecnico
        )

        self.client.force_login(self.almacen)
        response = self.client.post(reverse('mantenimiento:dar_salida_repuesto', args=[solicitud.id]))
        self.assertEqual(response.status_code, 302)

        solicitud.refresh_from_db()
        self.repuesto.refresh_from_db()

        self.assertEqual(solicitud.estado, 'DESPACHADO')
        self.assertEqual(solicitud.despachado_por, self.almacen)
        self.assertEqual(self.repuesto.cantidad_actual, 6)  # 10 - 4 = 6

        # Se debe registrar movimiento de salida
        mov = MovimientoRepuesto.objects.filter(repuesto=self.repuesto, tipo='SALIDA').first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.cantidad, 4)
        self.assertEqual(mov.usuario, self.almacen)

    def test_administrador_almacen_rechaza_solicitud(self):
        """El Administrador de Almacén puede rechazar la solicitud con un motivo."""
        solicitud = OrdenRepuesto.objects.create(
            orden=self.orden,
            repuesto=self.repuesto,
            cantidad_utilizada=2,
            estado='PENDIENTE',
            solicitado_por=self.tecnico
        )

        self.client.force_login(self.almacen)
        response = self.client.post(
            reverse('mantenimiento:rechazar_repuesto', args=[solicitud.id]),
            {'motivo_rechazo': 'Pieza reservada para línea de producción'}
        )
        self.assertEqual(response.status_code, 302)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'RECHAZADO')
        self.assertEqual(solicitud.motivo_rechazo, 'Pieza reservada para línea de producción')
        # Stock intacto
        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.cantidad_actual, 10)

    def test_ingreso_de_stock_por_almacen(self):
        """El Administrador de Almacén puede registrar entradas de stock directo."""
        self.client.force_login(self.almacen)
        response = self.client.post(
            reverse('mantenimiento:ingreso_repuesto', args=[self.repuesto.id]),
            {'cantidad': 5, 'motivo': 'Compra de reposición'}
        )
        self.assertEqual(response.status_code, 302)

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.cantidad_actual, 15)  # 10 + 5 = 15

    def test_owner_gestion_pedidos_proveedores(self):
        """El Dueño (Owner) puede crear pedidos y recibirlos sumando stock en almacén."""
        self.client.force_login(self.owner)

        # Crear pedido
        response = self.client.post(
            reverse('mantenimiento:crear_pedido_proveedor'),
            {
                'proveedor': self.proveedor.id,
                'repuesto': self.repuesto.id,
                'descripcion_item': 'Lote de filtros de repuesto',
                'cantidad': 12,
                'precio_unitario_estimado': '20.00',
                'observaciones': 'Pago a 30 días'
            }
        )
        self.assertEqual(response.status_code, 302)

        pedido = PedidoProveedor.objects.filter(proveedor=self.proveedor).first()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.cantidad, 12)
        self.assertEqual(pedido.costo_total, 240.00)
        self.assertEqual(pedido.estado, 'PENDIENTE')

        # Cambiar a ENVIADO
        self.client.get(reverse('mantenimiento:cambiar_estado_pedido_proveedor', args=[pedido.id, 'ENVIADO']))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'ENVIADO')

        # Cambiar a RECIBIDO (debe ingresar el stock automáticamente al almacén)
        stock_antes = self.repuesto.cantidad_actual
        self.client.get(reverse('mantenimiento:cambiar_estado_pedido_proveedor', args=[pedido.id, 'RECIBIDO']))
        pedido.refresh_from_db()
        self.repuesto.refresh_from_db()

        self.assertEqual(pedido.estado, 'RECIBIDO')
        self.assertEqual(self.repuesto.cantidad_actual, stock_antes + 12)
