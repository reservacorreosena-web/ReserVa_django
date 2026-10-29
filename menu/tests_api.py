from datetime import time, timedelta

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from reservas.models import ConsumoMesa, Mesa, Plato, Reserva, Zona
from usuarios.models import Usuario


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MenuAPITests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Cliente Menu",
            email="menu.cliente@example.com",
            contraseña=make_password("ClaveSegura123"),
            rol="cliente",
        )
        self.auth_user = User.objects.create_user(
            username=self.usuario.email,
            email=self.usuario.email,
            password="otra-clave",
        )
        self.token = Token.objects.create(user=self.auth_user)

        self.admin_app = Usuario.objects.create(
            nombre="Admin Menu",
            email="menu.admin@example.com",
            contraseña=make_password("ClaveSegura123"),
            rol="admin",
        )
        self.admin_user = User.objects.create_user(
            username=self.admin_app.email,
            email=self.admin_app.email,
            password="otra-clave",
            is_staff=True,
        )
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.zona = Zona.objects.create(nombre="Salon")
        self.mesa_reservada = Mesa.objects.create(
            numero=1, capacidad=4, zona=self.zona, posicion_x=100, posicion_y=120
        )
        self.mesa_consumo = Mesa.objects.create(
            numero=2, capacidad=4, zona=self.zona, posicion_x=200, posicion_y=120
        )
        self.mesa_pequena = Mesa.objects.create(
            numero=3, capacidad=2, zona=self.zona, posicion_x=300, posicion_y=120
        )
        self.mesa_libre = Mesa.objects.create(
            numero=4, capacidad=6, zona=self.zona, posicion_x=400, posicion_y=120
        )

        self.plato_stock = Plato.objects.create(
            nombre="Plato con stock",
            descripcion="Disponible",
            precio=25000,
            categoria="entradas",
            disponible=True,
            stock=5,
        )
        self.plato_sin_stock = Plato.objects.create(
            nombre="Plato sin stock",
            descripcion="Sin unidades",
            precio=30000,
            categoria="platos_fuertes",
            disponible=True,
            stock=0,
        )
        self.plato_no_disponible = Plato.objects.create(
            nombre="Plato no disponible",
            descripcion="Deshabilitado",
            precio=35000,
            categoria="postres",
            disponible=False,
            stock=10,
        )

    def _autenticar(self, token=None):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {(token or self.token).key}"
        )

    def test_mesas_requiere_autenticacion(self):
        response = self.client.get("/menu/api/mesas/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mesas_incluye_coordenadas_y_no_calcula_disponibilidad_sin_filtros(self):
        self._autenticar()
        response = self.client.get("/menu/api/mesas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mesa = next(m for m in response.data if m["id"] == self.mesa_libre.id)
        self.assertEqual(mesa["posicion_x"], 400)
        self.assertEqual(mesa["posicion_y"], 120)
        self.assertIsNone(mesa["disponible"])
        self.assertIsNone(mesa["motivo_no_disponible"])

    def test_mesas_calcula_disponibilidad(self):
        fecha = timezone.now().date() + timedelta(days=1)
        hora = time(19, 30)

        Reserva.objects.create(
            usuario=self.usuario,
            mesa=self.mesa_reservada,
            cantidad_personas=2,
            fecha=fecha,
            hora=hora,
            estado="pendiente",
        )
        ConsumoMesa.objects.create(
            mesa=self.mesa_consumo,
            plato=self.plato_stock,
            cantidad=1,
            precio_unitario=self.plato_stock.precio,
            pagado=False,
        )

        self._autenticar()
        response = self.client.get(
            "/menu/api/mesas/",
            {"fecha": fecha.isoformat(), "hora": "19:30", "personas": 4},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        por_id = {mesa["id"]: mesa for mesa in response.data}
        self.assertFalse(por_id[self.mesa_reservada.id]["disponible"])
        self.assertEqual(
            por_id[self.mesa_reservada.id]["motivo_no_disponible"], "reservada"
        )
        self.assertFalse(por_id[self.mesa_consumo.id]["disponible"])
        self.assertEqual(
            por_id[self.mesa_consumo.id]["motivo_no_disponible"], "en_consumo"
        )
        self.assertFalse(por_id[self.mesa_pequena.id]["disponible"])
        self.assertEqual(
            por_id[self.mesa_pequena.id]["motivo_no_disponible"], "capacidad"
        )
        self.assertTrue(por_id[self.mesa_libre.id]["disponible"])
        self.assertIsNone(por_id[self.mesa_libre.id]["motivo_no_disponible"])

    def test_mesas_disponibles_devuelve_solo_libres(self):
        fecha = timezone.now().date() + timedelta(days=1)
        Reserva.objects.create(
            usuario=self.usuario,
            mesa=self.mesa_reservada,
            cantidad_personas=2,
            fecha=fecha,
            hora=time(19, 30),
            estado="confirmada",
        )

        self._autenticar()
        response = self.client.get(
            "/menu/api/mesas/disponibles/",
            {"fecha": fecha.isoformat(), "hora": "19:30", "personas": 4},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [mesa["id"] for mesa in response.data]
        self.assertNotIn(self.mesa_reservada.id, ids)
        self.assertNotIn(self.mesa_pequena.id, ids)
        self.assertIn(self.mesa_libre.id, ids)
        self.assertTrue(all(mesa["disponible"] for mesa in response.data))

    def test_mesas_disponibles_exige_fecha_y_hora(self):
        self._autenticar()
        response = self.client.get("/menu/api/mesas/disponibles/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mesas_rechaza_fecha_invalida(self):
        self._autenticar()
        response = self.client.get(
            "/menu/api/mesas/", {"fecha": "2026-13-40", "hora": "19:30"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mesas_rechaza_fecha_sin_hora(self):
        self._autenticar()
        response = self.client.get(
            "/menu/api/mesas/", {"fecha": timezone.now().date().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mesas_rechaza_zona_no_numerica(self):
        self._autenticar()
        response = self.client.get("/menu/api/mesas/", {"zona": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zonas_requiere_token_y_lista(self):
        response = self.client.get("/menu/api/zonas/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self._autenticar()
        response = self.client.get("/menu/api/zonas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["nombre"], "Salon")

    def test_platos_cliente_solo_disponibles_con_stock(self):
        self._autenticar()
        response = self.client.get("/menu/api/platos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [plato["id"] for plato in response.data]
        self.assertIn(self.plato_stock.id, ids)
        self.assertNotIn(self.plato_sin_stock.id, ids)
        self.assertNotIn(self.plato_no_disponible.id, ids)

    def test_platos_admin_ve_todo_el_catalogo(self):
        self._autenticar(self.admin_token)
        response = self.client.get("/menu/api/platos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [plato["id"] for plato in response.data]
        self.assertIn(self.plato_stock.id, ids)
        self.assertIn(self.plato_sin_stock.id, ids)
        self.assertIn(self.plato_no_disponible.id, ids)

    def test_platos_filtra_categoria_y_busqueda(self):
        self._autenticar()
        response = self.client.get(
            "/menu/api/platos/", {"categoria": "entradas"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.plato_stock.id)

        response = self.client.get(
            "/menu/api/platos/", {"buscar": "sin stock"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
