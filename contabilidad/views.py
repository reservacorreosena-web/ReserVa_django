from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from usuarios.decorador import verificar
from .models import Movimiento

from contabilidad.serializador import MovimientoSerializer

from .serializador import *
from rest_framework import viewsets

# Esta es la parte principal, acá mostraremos todos los gastos, ganancias ETC
@verificar
def inicio(request):
    gastos = Movimiento.objects.all()

    gasto_total = 0
    gasto_efectivo = 0
    gasto_banco = 0

    for g in gastos:
        gasto_total += g.valor

        metodo = g.metodo_pago.strip().lower() if g.metodo_pago else ""

        if metodo == "efectivo":
            gasto_efectivo += g.valor
        elif any(x in metodo for x in ["tarjeta", "transferencia", "débito", "debito", "crédito", "credito"]):
            gasto_banco += g.valor

    q = {
        'gastos': gastos,
        'gasto_total': gasto_total,
        'gasto_efectivo': gasto_efectivo,
        'gasto_banco': gasto_banco
    }

    return render(request, "contabilidad/prueba.html", q)


@verificar
def control_gastos(request):
    return render(request, "contabilidad/control_gastos.html")


@verificar
def guardar_gasto(request):
    if request.method == "POST":
        concepto = request.POST.get("concepto", "").strip().title()
        categoria = request.POST.get("categoria", "").strip().title()
        valor_raw = request.POST.get("valor", 0)
        metodo_pago = request.POST.get("metodo_pago", "").strip()

        if not concepto or not valor_raw:
            messages.error(request, "Por favor llena los campos obligatorios.")
            return redirect('control_gastos')

        try:
            valor = float(valor_raw)
        except ValueError:
            messages.error(request, "El valor ingresado debe ser un número válido.")
            return redirect('control_gastos')

        Movimiento.objects.create(
            concepto=concepto,
            categoria=categoria,
            valor=valor,
            metodo_pago=metodo_pago
        )
        messages.success(request, "¡Gasto Registrado con Éxito!")
        return redirect('inicio_contabilidad')

    return redirect('inicio_contabilidad')


@verificar
def eliminar_gasto(request, id):
    g = get_object_or_404(Movimiento, pk=id)
    g.delete()
    messages.success(request, "Gasto eliminado correctamente.")
    return redirect('inicio_contabilidad')


@verificar
def editar_gasto(request, id):
    g = get_object_or_404(Movimiento, pk=id)
    
    if request.method == "POST":
        g.concepto = request.POST.get('concepto', '').strip().title()
        g.categoria = request.POST.get('categoria', '').strip().title()
        g.valor = request.POST.get('valor', 0)
        g.metodo_pago = request.POST.get('metodo_pago', '').strip()
        
        if request.POST.get('fecha'):
            g.fecha = request.POST.get('fecha')

        g.save()  # <--- Persistir cambios en BD
        messages.success(request, "Gasto actualizado con éxito.")
        return redirect('inicio_contabilidad')

    contexto = {
        "gasto": g
    }
    return render(request, "contabilidad/editar_gasto.html", contexto)

class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer