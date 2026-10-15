from django.core.management.base import BaseCommand
import poblar_datos

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos completos de prueba (usuarios, mesas, platos, reservas, caja)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Ejecutando carga de datos...'))
        poblar_datos.poblar()
        self.stdout.write(self.style.SUCCESS('¡Datos cargados con éxito!'))
