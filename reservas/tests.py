from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from reservas.models import Zona, Mesa, Plato, Reserva, ConsumoMesa


class ReservasModelTests(TestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Terraza Principal")
        self.mesa = Mesa.objects.create(
            numero=10,
            capacidad=4,
            zona=self.zona,
            forma="cuadrada",
            posicion_x=120,
            posicion_y=150
        )
        self.usuario = Usuario.objects.create(
            nombre="Juan Perez",
            email="juan.perez@example.com",
            contraseña="pbkdf2_sha256$hashedpassword",
            rol="cliente"
        )
        self.plato = Plato.objects.create(
            nombre="Corte Ribeye",
            descripcion="Carne madurada 350g",
            precio=65000,
            categoria="platos_fuertes",
            stock=15,
            disponible=True
        )

    def test_creacion_mesa(self):
        self.assertEqual(self.mesa.numero, 10)
        self.assertEqual(self.mesa.capacidad, 4)
        self.assertIn("10", str(self.mesa))

    def test_creacion_reserva(self):
        reserva = Reserva.objects.create(
            usuario=self.usuario,
            mesa=self.mesa,
            cantidad_personas=3,
            fecha=date.today() + timedelta(days=1),
            hora=time(19, 30),
            estado="pendiente"
        )
        self.assertEqual(reserva.estado, "pendiente")
        self.assertEqual(reserva.usuario.nombre, "Juan Perez")
        self.assertIn("Juan Perez", str(reserva))

    def test_consumo_mesa_subtotal(self):
        consumo = ConsumoMesa.objects.create(
            mesa=self.mesa,
            plato=self.plato,
            cantidad=2,
            precio_unitario=self.plato.precio,
            pagado=False
        )
        self.assertEqual(consumo.subtotal(), 130000)


class ReservasViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.zona = Zona.objects.create(nombre="Salon Central")
        self.mesa = Mesa.objects.create(
            numero=1,
            capacidad=4,
            zona=self.zona,
            forma="rectangular"
        )
        self.cliente = Usuario.objects.create(
            nombre="Cliente Demo",
            email="demo@reserva.com",
            contraseña="pbkdf2_sha256$hashedpassword",
            rol="cliente"
        )
        self.admin = Usuario.objects.create(
            nombre="Admin General",
            email="admin@reserva.com",
            contraseña="pbkdf2_sha256$hashedpassword",
            rol="admin"
        )

    def test_urls_reverse(self):
        self.assertEqual(reverse('inicio'), '/')
        self.assertEqual(reverse('crear_reserva'), '/reservas/crear_reserva/')
        self.assertEqual(reverse('mis_reservas'), '/reservas/mis_reservas/')
        self.assertEqual(reverse('admin_mapa_mesas'), '/reservas/admin/vender/')
        self.assertEqual(reverse('historial_reservas'), '/reservas/historial_reservas/')
        self.assertEqual(reverse('ver_carta'), '/menu/ver_carta/')

    def test_redireccion_sin_login(self):
        # Un usuario anónimo intentando crear reserva es redirigido a inicio
        response = self.client.get(reverse('crear_reserva'))
        self.assertEqual(response.status_code, 302)

    def test_acceso_cliente_crear_reserva(self):
        session = self.client.session
        session['logueado'] = {
            'id': self.cliente.id,
            'nombre': self.cliente.nombre,
            'rol': self.cliente.rol,
        }
        session.save()

        response = self.client.get(reverse('crear_reserva'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/formulario_reserva.html')

    def test_seguridad_admin_views_bloqueadas_para_cliente(self):
        # Un cliente normal no debe poder entrar a las vistas de admin
        session = self.client.session
        session['logueado'] = {
            'id': self.cliente.id,
            'nombre': self.cliente.nombre,
            'rol': self.cliente.rol,
        }
        session.save()

        response = self.client.get(reverse('historial_reservas'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('admin_mapa_mesas'))
        self.assertEqual(response.status_code, 302)

    def test_acceso_admin_historial_y_mapa(self):
        session = self.client.session
        session['logueado'] = {
            'id': self.admin.id,
            'nombre': self.admin.nombre,
            'rol': self.admin.rol,
        }
        session.save()

        response = self.client.get(reverse('historial_reservas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/historial_reservas.html')

        response = self.client.get(reverse('admin_mapa_mesas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/admin_mapa.html')
