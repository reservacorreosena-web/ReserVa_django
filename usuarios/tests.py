from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password
from usuarios.models import Usuario


class UsuarioAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password_plana = "Segura12345"
        self.usuario = Usuario.objects.create(
            nombre="Carlos Gomez",
            email="carlos@example.com",
            contraseña=make_password(self.password_plana),
            rol="cliente"
        )

    def test_contrasena_hasheada(self):
        self.assertNotEqual(self.usuario.contraseña, self.password_plana)
        self.assertTrue(check_password(self.password_plana, self.usuario.contraseña))

    def test_login_exitoso(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'carlos@example.com',
            'contraseña': self.password_plana
        })
        self.assertEqual(response.status_code, 302)
        # Verifica que la sesión se haya establecido
        self.assertEqual(self.client.session.get('logueado')['id'], self.usuario.id)

    def test_login_credenciales_invalidas(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'carlos@example.com',
            'contraseña': 'contrasenaincorrecta'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get('logueado'))

    def test_registro_usuario_nuevo(self):
        response = self.client.post(reverse('crear_usuario'), {
            'nombre': 'Maria Lopez',
            'email': 'maria@example.com',
            'contraseña': 'MiClaveSecreta99'
        })
        self.assertEqual(response.status_code, 302)
        nuevo = Usuario.objects.filter(email='maria@example.com').first()
        self.assertIsNotNone(nuevo)
        self.assertEqual(nuevo.nombre, 'Maria Lopez')
        self.assertTrue(check_password('MiClaveSecreta99', nuevo.contraseña))

    def test_logout(self):
        session = self.client.session
        session['logueado'] = {'id': self.usuario.id, 'nombre': self.usuario.nombre, 'rol': self.usuario.rol}
        session.save()

        response = self.client.get(reverse('cerrar_sesion'))
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get('logueado'))
