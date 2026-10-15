import os
import sys
from datetime import date, time, timedelta

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReserVa.settings')
import django
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from usuarios.models import Usuario
from reservas.models import Zona, Mesa, Plato, Reserva, ConsumoMesa
from contabilidad.models import Movimiento, Comentario_caja
from comentarios.models import Resena

def poblar():
    print("🚀 Iniciando carga de datos de prueba para ReserVa...")

    # ==========================================
    # 1. USUARIOS (Admin y Clientes)
    # ==========================================
    print("\n👤 1. Creando usuarios...")
    admin_user, _ = Usuario.objects.get_or_create(
        email='admin@reserva.com',
        defaults={
            'nombre': 'Administrador General',
            'contraseña': make_password('admin1234'),
            'rol': 'admin',
            'estado': True
        }
    )
    # Asegurar que la contraseña esté hasheada y el rol sea admin
    admin_user.contraseña = make_password('admin1234')
    admin_user.rol = 'admin'
    admin_user.save()

    cliente1, _ = Usuario.objects.get_or_create(
        email='carlos.gomez@gmail.com',
        defaults={
            'nombre': 'Carlos Gómez',
            'contraseña': make_password('cliente1234'),
            'rol': 'cliente',
            'estado': True
        }
    )
    cliente1.contraseña = make_password('cliente1234')
    cliente1.save()

    cliente2, _ = Usuario.objects.get_or_create(
        email='laura.restrepo@gmail.com',
        defaults={
            'nombre': 'Laura Restrepo',
            'contraseña': make_password('cliente1234'),
            'rol': 'cliente',
            'estado': True
        }
    )
    cliente2.contraseña = make_password('cliente1234')
    cliente2.save()

    cliente3, _ = Usuario.objects.get_or_create(
        email='miguel.angel@gmail.com',
        defaults={
            'nombre': 'Miguel Ángel',
            'contraseña': make_password('cliente1234'),
            'rol': 'cliente',
            'estado': True
        }
    )
    cliente3.contraseña = make_password('cliente1234')
    cliente3.save()

    # Django Auth User (para superadmin y reseñas)
    super_admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@reserva.com',
            'first_name': 'Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    super_admin.set_password('admin1234')
    super_admin.is_staff = True
    super_admin.is_superuser = True
    super_admin.save()

    user_laura, _ = User.objects.get_or_create(
        username='laura.restrepo@gmail.com',
        defaults={'first_name': 'Laura Restrepo'}
    )

    user_carlos, _ = User.objects.get_or_create(
        username='carlos.gomez@gmail.com',
        defaults={'first_name': 'Carlos Gómez'}
    )

    print("   ✓ Usuarios listos (Admin: admin@reserva.com / admin1234, Cliente: carlos.gomez@gmail.com / cliente1234)")

    # ==========================================
    # 2. ZONAS DEL RESTAURANTE
    # ==========================================
    print("\n🏛️ 2. Creando zonas...")
    zona_principal, _ = Zona.objects.get_or_create(nombre='Salón Principal')
    zona_terraza, _ = Zona.objects.get_or_create(nombre='Terraza Panorámica')
    zona_vip, _ = Zona.objects.get_or_create(nombre='Cava VIP')
    print("   ✓ 3 zonas configuradas.")

    # ==========================================
    # 3. MESAS Y PLANO INTERACTIVO
    # ==========================================
    print("\n🪑 3. Creando mesas con coordenadas para el mapa...")
    mesas_data = [
        # (numero, capacidad, zona, forma, x, y)
        (1, 4, zona_principal, 'cuadrada', 80, 80),
        (2, 2, zona_principal, 'redonda', 240, 80),
        (3, 6, zona_principal, 'rectangular', 400, 80),
        (4, 4, zona_terraza, 'cuadrada', 80, 240),
        (5, 2, zona_terraza, 'redonda', 240, 240),
        (6, 4, zona_terraza, 'cuadrada', 400, 240),
        (7, 8, zona_vip, 'rectangular', 160, 400),
        (8, 6, zona_vip, 'rectangular', 360, 400),
    ]

    mesas_creadas = {}
    for num, cap, zona, forma, x, y in mesas_data:
        m, _ = Mesa.objects.update_or_create(
            numero=num,
            defaults={
                'capacidad': cap,
                'zona': zona,
                'forma': forma,
                'posicion_x': x,
                'posicion_y': y
            }
        )
        mesas_creadas[num] = m
    print(f"   ✓ {len(mesas_creadas)} mesas distribuidas en el plano.")

    # ==========================================
    # 4. CARTA / MENÚ (Platos, Bebidas, Postres)
    # ==========================================
    print("\n🍽️ 4. Creando carta gastronómica...")
    platos_data = [
        # Entradas
        ('Carpaccio de Res Trufado', 'Finas láminas de lomo con parmesano reggiano, rúcula fresca y aceite de trufa blanca.', 34000, 'entradas', True, True, 20),
        ('Ceviche Clásico del Pacífico', 'Corvina fresca marinada en zumo de lima con maíz chulpi, cebolla morada y cilantro.', 29000, 'entradas', True, False, 25),
        ('Bruschettas Mediterráneas', 'Pan rústico a la parrilla con tomates confitados, albahaca genovesa y reducción balsámica.', 22000, 'entradas', True, False, 30),

        # Platos Fuertes
        ('Bife de Chorizo Angus 400g', 'Corte premium a la parrilla con mantequilla de romero y papas rústicas al horno.', 72000, 'platos_fuertes', True, True, 18),
        ('Salmón en Costra de Finas Hierbas', 'Filete de salmón noruego sobre cama de risotto cremoso de espárragos y limón.', 58000, 'platos_fuertes', True, True, 15),
        ('Risotto de Hongos Portobello', 'Arroz arborio con setas silvestres, vino blanco y terminado con mantequilla trufada.', 46000, 'platos_fuertes', True, False, 20),
        ('Pasta Tagliatelle a la Boloñesa', 'Pasta artesanal con ragú de carne cocinado a fuego lento durante 6 horas.', 39000, 'platos_fuertes', True, False, 25),

        # Bebidas
        ('Limonada de Coco Imperial', 'Refrescante mezcla de crema de coco natural y limones frescos con toque de menta.', 14000, 'bebidas', True, True, 50),
        ('Cóctel Mojito Clásico', 'Ron añejo, hierbabuena fresca, zumo de limón verde y soda artesanal.', 26000, 'bebidas', True, True, 40),
        ('Copa de Vino Tinto Malbec', 'Vino reserva argentino con notas a frutos negros y especias.', 28000, 'bebidas', True, False, 35),
        ('Jugo Natural de Frutos Rojos', 'Mora, fresa y arándanos silvestres preparados al instante.', 12000, 'bebidas', True, False, 45),

        # Postres
        ('Tiramisú Tradicional Italiano', 'Capas de bizcochos de soletilla bañados en café espresso y crema mascarpone.', 21000, 'postres', True, True, 20),
        ('Volcán de Chocolate Belga', 'Bizcocho tibio relleno de chocolate fundido acompañado de helado de vainilla.', 24000, 'postres', True, True, 18),
        ('Cheesecake de Frutos del Bosque', 'Cremosa base de queso crema con compota artesanal de arándanos y fresas.', 19000, 'postres', True, False, 22),
    ]

    platos_creados = {}
    for nom, desc, pre, cat, disp, dest, stk in platos_data:
        p, _ = Plato.objects.update_or_create(
            nombre=nom,
            defaults={
                'descripcion': desc,
                'precio': pre,
                'categoria': cat,
                'disponible': disp,
                'destacado': dest,
                'stock': stk
            }
        )
        platos_creados[nom] = p
    print(f"   ✓ {len(platos_creados)} platos, bebidas y postres listos con stock activo.")

    # ==========================================
    # 5. RESERVAS DE DEMOSTRACIÓN
    # ==========================================
    print("\n📅 5. Creando reservas de demostración...")
    hoy = timezone.now().date()
    hora_almuerzo = time(13, 0)
    hora_cena = time(20, 0)

    # Reserva 1: Hoy a mediodía - Asistió / Concluida
    reserva_hoy, _ = Reserva.objects.update_or_create(
        usuario=cliente1,
        fecha=hoy,
        hora=hora_almuerzo,
        defaults={
            'mesa': mesas_creadas[1],
            'cantidad_personas': 4,
            'notas': 'Mesa para celebración de aniversario.',
            'estado': 'asistio'
        }
    )

    # Reserva 2: Hoy en la noche - Confirmada
    reserva_noche, _ = Reserva.objects.update_or_create(
        usuario=cliente2,
        fecha=hoy,
        hora=hora_cena,
        defaults={
            'mesa': mesas_creadas[4],
            'cantidad_personas': 2,
            'notas': 'Preferencia por la vista panorámica.',
            'estado': 'confirmada'
        }
    )

    # Reserva 3: Mañana - Pendiente
    reserva_manana, _ = Reserva.objects.update_or_create(
        usuario=cliente3,
        fecha=hoy + timedelta(days=1),
        hora=hora_cena,
        defaults={
            'mesa': mesas_creadas[7],
            'cantidad_personas': 6,
            'notas': 'Cena de negocios ejecutiva.',
            'estado': 'pendiente'
        }
    )
    print("   ✓ Reservas creadas para hoy y mañana en diferentes estados.")

    # ==========================================
    # 6. COMANDAS / CONSUMOS EN MESA (POS)
    # ==========================================
    print("\n🧾 6. Registrando comandas y consumos de mesa...")
    # Consumos pagados en Mesa 1 (para cuadre de caja de hoy)
    ConsumoMesa.objects.get_or_create(
        mesa=mesas_creadas[1],
        reserva=reserva_hoy,
        plato=platos_creados['Bife de Chorizo Angus 400g'],
        defaults={'cantidad': 2, 'precio_unitario': 72000, 'pagado': True}
    )
    ConsumoMesa.objects.get_or_create(
        mesa=mesas_creadas[1],
        reserva=reserva_hoy,
        plato=platos_creados['Limonada de Coco Imperial'],
        defaults={'cantidad': 2, 'precio_unitario': 14000, 'pagado': True}
    )
    ConsumoMesa.objects.get_or_create(
        mesa=mesas_creadas[1],
        reserva=reserva_hoy,
        plato=platos_creados['Volcán de Chocolate Belga'],
        defaults={'cantidad': 2, 'precio_unitario': 24000, 'pagado': True}
    )

    # Consumos activos (sin pagar) en Mesa 4 (para ver cuenta en el POS)
    ConsumoMesa.objects.get_or_create(
        mesa=mesas_creadas[4],
        reserva=reserva_noche,
        plato=platos_creados['Salmón en Costra de Finas Hierbas'],
        defaults={'cantidad': 2, 'precio_unitario': 58000, 'pagado': False}
    )
    ConsumoMesa.objects.get_or_create(
        mesa=mesas_creadas[4],
        reserva=reserva_noche,
        plato=platos_creados['Copa de Vino Tinto Malbec'],
        defaults={'cantidad': 2, 'precio_unitario': 28000, 'pagado': False}
    )
    print("   ✓ Comandas configuradas (Mesa #1 pagada para cuadre, Mesa #4 activa para probar POS).")

    # ==========================================
    # 7. CONTABILIDAD Y CUADRE DE CAJA
    # ==========================================
    print("\n💰 7. Registrando movimientos de contabilidad...")
    # Ingreso del día
    Movimiento.objects.get_or_create(
        concepto='Cobro Mesa #1 - Almuerzo',
        fecha=hoy,
        defaults={
            'tipo': 'INGRESO',
            'categoria': 'RESERVA',
            'valor': 220000,
            'metodo_pago': 'EFECTIVO'
        }
    )
    Movimiento.objects.get_or_create(
        concepto='Anticipo Evento Corporativo Salón VIP',
        fecha=hoy,
        defaults={
            'tipo': 'INGRESO',
            'categoria': 'RESERVA',
            'valor': 350000,
            'metodo_pago': 'TRANSFERENCIA'
        }
    )
    # Gastos del día
    Movimiento.objects.get_or_create(
        concepto='Compra de carnes premium y cortes finos',
        fecha=hoy,
        defaults={
            'tipo': 'GASTO',
            'categoria': 'INSUMOS',
            'valor': 140000,
            'metodo_pago': 'EFECTIVO'
        }
    )
    Movimiento.objects.get_or_create(
        concepto='Pago servicio de gas natural industrial',
        fecha=hoy,
        defaults={
            'tipo': 'GASTO',
            'categoria': 'SERVICIOS',
            'valor': 85000,
            'metodo_pago': 'TRANSFERENCIA'
        }
    )

    # Observación de caja para hoy
    Comentario_caja.objects.update_or_create(
        fecha=hoy,
        defaults={'comentario': 'Jornada fluida con excelente ocupación en salón principal. Cuadre verificado sin descuadre.'}
    )
    print("   ✓ Ingresos, gastos y observación de caja cargados.")

    # ==========================================
    # 8. RESEÑAS / TESTIMONIOS (Landing Page)
    # ==========================================
    print("\n⭐ 8. Creando reseñas para la landing page...")
    Resena.objects.get_or_create(
        usuario=user_laura,
        comentario='¡Una experiencia culinaria insuperable! El bife de chorizo en su punto y la vista de la terraza es mágica.',
        defaults={
            'calificacion_comida': 5,
            'calificacion_servicio': 5
        }
    )
    Resena.objects.get_or_create(
        usuario=user_carlos,
        comentario='Excelente atención desde que llegamos. La limonada de coco y el tiramisú son un 10 total. Volveremos sin duda.',
        defaults={
            'calificacion_comida': 5,
            'calificacion_servicio': 5
        }
    )
    print("   ✓ Reseñas añadidas al carrusel de la página de inicio.")

    print("\n" + "="*55)
    print("🎉 ¡BASE DE DATOS CARGADA EXITOSAMENTE!")
    print("="*55)
    print("Credenciales para ingresar y mostrar:")
    print(" • Administrador: admin@reserva.com   | Clave: admin1234")
    print(" • Cliente:       carlos.gomez@gmail.com | Clave: cliente1234")
    print(" • Django Admin:  admin                  | Clave: admin1234")
    print("="*55 + "\n")

# Ejecución directa
poblar()
