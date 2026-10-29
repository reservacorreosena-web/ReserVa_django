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
class ReservasAPITests(APITestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Terraza")
        self.mesa = Mesa.objects.create(
            numero=10,
            capacidad=4,
            zona=self.zona,
            posicion_x=150,
            posicion_y=200,
        )
        self.mesa_grande = Mesa.objects.create(
            numero=11,
            capacidad=8,
            zona=self.zona,
            posicion_x=250,
            posicion_y=200,
        )

        self.cliente, self.token = self._crear_usuario(
            "reservas.cliente@example.com", "cliente"
        )
        self.otro, self.otro_token = self._crear_usuario(
            "reservas.otro@example.com", "cliente"
        )
        self.admin, self.admin_token = self._crear_usuario(
            "reservas.admin@example.com", "admin", is_staff=True
        )

        self.fecha = timezone.now().date() + timedelta(days=2)
        self.hora = time(19, 30)

        self.plato = Plato.objects.create(
            nombre="Plato reserva",
            descripcion="Plato de prueba",
            precio=45000,
            categoria="platos_fuertes",
            disponible=True,
            stock=10,
        )

    def _crear_usuario(self, email, rol, is_staff=False):
        app = Usuario.objects.create(
            nombre=f"Usuario {rol}",
            email=email,
            contraseña=make_password("ClaveSegura123"),
            rol=rol,
        )
        auth_user = User.objects.create_user(
            username=email,
            email=email,
            password="otra-clave",
            is_staff=is_staff,
        )
        token = Token.objects.create(user=auth_user)
        return app, token

    def _autenticar(self, token=None):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {(token or self.token).key}"
        )

    def _payload(self, **overrides):
        payload = {
            "mesa": self.mesa.id,
            "cantidad_personas": 2,
            "fecha": self.fecha.isoformat(),
            "hora": "19:30",
            "notas": "Sin cebolla",
        }
        payload.update(overrides)
        return payload

    def test_crear_requiere_autenticacion(self):
        response = self.client.post(
            "/reservas/api/reservas/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crear_fuerza_usuario_del_token_y_estado_pendiente(self):
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/",
            self._payload(
                usuario=self.otro.id,
                estado="asistio",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"], self.cliente.id)
        self.assertEqual(response.data["estado"], "pendiente")
        self.assertEqual(response.data["mesa"], self.mesa.id)

        reserva = Reserva.objects.get(pk=response.data["id"])
        self.assertEqual(reserva.usuario_id, self.cliente.id)
        self.assertEqual(reserva.estado, "pendiente")

    def test_crear_rechaza_fecha_pasada(self):
        self._autenticar()
        ayer = timezone.now().date() - timedelta(days=1)
        response = self.client.post(
            "/reservas/api/reservas/",
            self._payload(fecha=ayer.isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha", response.data)

    def test_crear_rechaza_personas_fuera_de_rango(self):
        self._autenticar()
        for personas in (0, 21):
            response = self.client.post(
                "/reservas/api/reservas/",
                self._payload(cantidad_personas=personas),
                format="json",
            )
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST
            )
            self.assertIn("cantidad_personas", response.data)

    def test_crear_rechaza_capacidad_insuficiente(self):
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/",
            self._payload(mesa=self.mesa.id, cantidad_personas=5),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mesa", response.data)

    def test_crear_rechaza_conflicto_de_mesa(self):
        Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
            estado="confirmada",
        )
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mesa", response.data)

    def test_crear_permite_mesa_con_reserva_cancelada(self):
        Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
            estado="cancelada",
        )
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_rechaza_mesa_con_consumo_activo(self):
        ConsumoMesa.objects.create(
            mesa=self.mesa,
            plato=self.plato,
            cantidad=1,
            precio_unitario=self.plato.precio,
            pagado=False,
        )
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mesa", response.data)

    def test_crear_sin_mesa_es_valido(self):
        self._autenticar()
        response = self.client.post(
            "/reservas/api/reservas/",
            self._payload(mesa=None),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["mesa"])

    def test_lista_solo_reservas_propias(self):
        propia = Reserva.objects.create(
            usuario=self.cliente,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        ajena = Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa_grande,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=time(20, 30),
        )

        self._autenticar()
        response = self.client.get("/reservas/api/reservas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [reserva["id"] for reserva in response.data]
        self.assertIn(propia.id, ids)
        self.assertNotIn(ajena.id, ids)

    def test_admin_lista_todas(self):
        propia = Reserva.objects.create(
            usuario=self.cliente,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        ajena = Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa_grande,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=time(20, 30),
        )

        self._autenticar(self.admin_token)
        response = self.client.get("/reservas/api/reservas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [reserva["id"] for reserva in response.data]
        self.assertIn(propia.id, ids)
        self.assertIn(ajena.id, ids)

    def test_mis_reservas_solo_propias(self):
        propia = Reserva.objects.create(
            usuario=self.cliente,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa_grande,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=time(20, 30),
        )

        self._autenticar()
        response = self.client.get("/reservas/api/reservas/mis-reservas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([reserva["id"] for reserva in response.data], [propia.id])

    def test_no_puede_editar_reserva_ajena(self):
        ajena = Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        self._autenticar()
        response = self.client.patch(
            f"/reservas/api/reservas/{ajena.id}/",
            {"notas": "Intento ajeno"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_no_permite_cambiar_estado(self):
        propia = Reserva.objects.create(
            usuario=self.cliente,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        self._autenticar()
        response = self.client.patch(
            f"/reservas/api/reservas/{propia.id}/",
            {"estado": "asistio", "notas": "Actualizada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "pendiente")
        self.assertEqual(response.data["notas"], "Actualizada")

    def test_cancelar_restaura_stock_y_elimina_consumos(self):
        reserva = Reserva.objects.create(
            usuario=self.cliente,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        self.plato.stock = 9
        self.plato.save(update_fields=["stock"])
        ConsumoMesa.objects.create(
            mesa=self.mesa,
            reserva=reserva,
            plato=self.plato,
            cantidad=1,
            precio_unitario=self.plato.precio,
            pagado=False,
        )

        self._autenticar()
        response = self.client.post(
            f"/reservas/api/reservas/{reserva.id}/cancelar/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "cancelada")
        reserva.refresh_from_db()
        self.plato.refresh_from_db()
        self.assertEqual(reserva.estado, "cancelada")
        self.assertEqual(self.plato.stock, 10)
        self.assertFalse(
            ConsumoMesa.objects.filter(reserva=reserva, pagado=False).exists()
        )

    def test_no_puede_cancelar_reserva_ajena(self):
        ajena = Reserva.objects.create(
            usuario=self.otro,
            mesa=self.mesa,
            cantidad_personas=2,
            fecha=self.fecha,
            hora=self.hora,
        )
        self._autenticar()
        response = self.client.post(
            f"/reservas/api/reservas/{ajena.id}/cancelar/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
