from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from usuarios.models import Usuario


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AutenticacionAPITests(APITestCase):
    def setUp(self):
        self.password = "ClaveSegura123"
        self.usuario = Usuario.objects.create(
            nombre="Cliente Api",
            email="cliente.api@example.com",
            contraseña=make_password(self.password),
            rol="cliente",
        )

        # Igual que en producción: el auth.User solo es titular del token y
        # nunca puede iniciar sesión con contraseña propia.
        self.auth_user = User.objects.create_user(
            username=self.usuario.email,
            email=self.usuario.email,
            password=None,
        )
        self.token = Token.objects.create(user=self.auth_user)

    def test_registro_crea_usuario_hasheado_y_token(self):
        payload = {
            "nombre": "  maria lopez  ",
            "email": "  MARIA.LOPEZ@EXAMPLE.COM ",
            "password": "MiClaveSegura99",
            "rol": "admin",
        }
        response = self.client.post(
            reverse("api_auth_register"), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "maria.lopez@example.com")
        self.assertEqual(response.data["user"]["rol"], "cliente")

        creado = Usuario.objects.get(email="maria.lopez@example.com")
        self.assertEqual(creado.nombre, "Maria Lopez")
        self.assertNotEqual(creado.contraseña, "MiClaveSegura99")
        self.assertTrue(check_password("MiClaveSegura99", creado.contraseña))

        auth_user = User.objects.get(username="maria.lopez@example.com")
        self.assertFalse(auth_user.has_usable_password())
        self.assertTrue(Token.objects.filter(user=auth_user).exists())

    def test_registro_duplicado_devuelve_400(self):
        response = self.client.post(
            reverse("api_auth_register"),
            {
                "nombre": "Otro Cliente",
                "email": "CLIENTE.API@EXAMPLE.COM",
                "password": "OtraClave123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registro_contrasena_corta_devuelve_400(self):
        response = self.client.post(
            reverse("api_auth_register"),
            {
                "nombre": "Cliente Corto",
                "email": "corto@example.com",
                "password": "1234567",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registro_acepta_alias_contrasena(self):
        response = self.client.post(
            reverse("api_auth_register"),
            {
                "nombre": "Cliente Alias",
                "email": "alias@example.com",
                "contraseña": "ClaveAlias123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Usuario.objects.filter(email="alias@example.com").exists()
        )

    def test_login_devuelve_token_y_datos(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"email": self.usuario.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], self.token.key)
        self.assertEqual(response.data["user"]["id"], self.usuario.id)
        self.assertNotIn("contraseña", response.data["user"])

    def test_login_credenciales_invalidas(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"email": self.usuario.email, "password": "incorrecta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_sin_datos(self):
        response = self.client.post(reverse("api_auth_login"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_cuenta_deshabilitada(self):
        self.usuario.estado = False
        self.usuario.save(update_fields=["estado"])
        response = self.client.post(
            reverse("api_auth_login"),
            {"email": self.usuario.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_cuenta_suspendida(self):
        self.usuario.nombre = "Cliente Api [SUSPENDIDO]"
        self.usuario.save(update_fields=["nombre"])
        response = self.client.post(
            reverse("api_auth_login"),
            {"email": self.usuario.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_no_reutiliza_auth_user_con_privilegios(self):
        # Un auth.User staff con contraseña utilizable no debe entregar token
        # a una cuenta de cliente aunque el email coincida.
        app_user = Usuario.objects.create(
            nombre="Cliente Staff",
            email="staff.cliente@example.com",
            contraseña=make_password("ClaveStaff123"),
            rol="cliente",
        )
        User.objects.create_user(
            username=app_user.email,
            email=app_user.email,
            password="clave-admin",
            is_staff=True,
        )

        response = self.client.post(
            reverse("api_auth_login"),
            {"email": app_user.email, "password": "ClaveStaff123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_reutiliza_auth_user_legado_sin_contrasena(self):
        # Los auth.User creados por versiones anteriores tienen contraseña
        # vacía; deben seguir funcionando y conservar su token.
        app_user = Usuario.objects.create(
            nombre="Cliente Legado",
            email="legado@example.com",
            contraseña=make_password("ClaveLegado123"),
            rol="cliente",
        )
        auth_user = User.objects.create(
            username=app_user.email, email=app_user.email
        )
        token = Token.objects.create(user=auth_user)

        response = self.client.post(
            reverse("api_auth_login"),
            {"email": app_user.email, "password": "ClaveLegado123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], token.key)

    def test_login_solo_post(self):
        response = self.client.get(reverse("api_auth_login"))
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_me_requiere_token(self):
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_devuelve_usuario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["id"], self.usuario.id)
        self.assertEqual(response.data["user"]["email"], self.usuario.email)

    def test_logout_revoca_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(reverse("api_auth_logout"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
