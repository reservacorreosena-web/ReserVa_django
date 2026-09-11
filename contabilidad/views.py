from multiprocessing.managers import convert_to_error

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from reservas.models import ConsumoMesa

from usuarios.decorador import verificar
from .models import Movimiento
from usuarios.decorador import solo_admin


from contabilidad.serializador import MovimientoSerializer

from .serializador import *
from rest_framework import viewsets

# Esta es la parte principal, acá mostraremos todos los gastos, ganancias ETC
@solo_admin
def inicio(request):
    #Creamos una variable que tiene todos los movimientos registrados
    gastos = Movimiento.objects.all()

    gasto_total = 0
    gasto_efectivo = 0
    gasto_banco = 0

    for g in gastos:
        gasto_total += g.valor
                                                #Con esto verificamos que el gasto no venga vacio para evitar un none
        metodo = g.metodo_pago.strip().lower() if g.metodo_pago else ""

        if metodo == "efectivo":
            gasto_efectivo += g.valor
            #Any es para comprobar si al menos una condicion se cumple y poder sumarle a gasto_banco
        elif any(x in metodo for x in ["tarjeta", "transferencia", "débito", "debito", "crédito", "credito"]):
            gasto_banco += g.valor
    #Esto es un query para pasarle los datos a el HTML y poder pintarlos mas adelante
    q = {
        'gastos': gastos,
        'gasto_total': gasto_total,
        'gasto_efectivo': gasto_efectivo,
        'gasto_banco': gasto_banco
    }

    return render(request, "contabilidad/prueba.html", q)


@solo_admin
def control_gastos(request):
    return render(request, "contabilidad/control_gastos.html")


@solo_admin
def guardar_gasto(request):
    if request.method == "POST":
        concepto = request.POST.get("concepto", "").strip().title()
        categoria = request.POST.get("categoria", "").strip().title()
        valor = request.POST.get("valor", 0)
        metodo_pago = request.POST.get("metodo_pago", "").strip()

        datos_contabilidad = {
            "concepto" : concepto,
            "categoria" : categoria,
            "valor" : valor,
        }

        contexto = {
            "datos_contabilidad" : datos_contabilidad
        }

        if not concepto or not valor or not categoria or not metodo_pago:
            messages.error(request, "Por favor llena los campos obligatorios.")
            return render(request, 'contabilidad/control_gastos.html',  contexto)

        if len(concepto)<5:
            messages.warning(request,"El concepto debe tener al menos 5 caracteres")
            return render(request, 'contabilidad/control_gastos.html',  contexto)

        try:
            valor = float(valor)
            if valor <=0:
                messages.error(request,"Ingrese un valor valido")
                return render(request, 'contabilidad/control_gastos.html',  contexto)
        except ValueError:
            messages.error(request, "El valor ingresado debe ser un número válido.")
            return render(request, 'contabilidad/control_gastos.html', contexto)

        Movimiento.objects.create(
            concepto=concepto,
            categoria=categoria,
            valor=valor,
            metodo_pago=metodo_pago
        )
        messages.success(request, "¡Gasto Registrado con Éxito!")
        return redirect('inicio_contabilidad')

    return redirect('inicio_contabilidad')


@solo_admin
def eliminar_gasto(request, id):
    g = get_object_or_404(Movimiento, id=id)
    g.delete()
    messages.success(request, "Gasto eliminado correctamente.")
    return redirect('inicio_contabilidad')


@solo_admin
def editar_gasto(request, id):
    g = get_object_or_404(Movimiento, id=id)

    if request.method == "POST":
        concepto = request.POST.get('concepto', '').strip().title()
        categoria = request.POST.get('categoria', '').strip().title()
        valor_raw = request.POST.get('valor', 0)
        metodo_pago = request.POST.get('metodo_pago', '').strip()

       
        if not concepto or not categoria or not valor_raw or not metodo_pago:
            messages.error(request, 'Los campos no pueden estar vacíos.')
            return redirect('editar_gasto', id=id)

       
        if len(concepto) < 5:
            messages.warning(request, 'El concepto tiene que tener al menos 5 caracteres.')
            return redirect('editar_gasto', id=id)

        try:
            valor = float(valor_raw)
            if valor <=0:
                messages.error(request,"El valor ingresado tiene que ser un numero valido")
                return redirect('editar_gasto',id=id)
        except ValueError:
            messages.error(request,"El valor ingresado debe ser un numero.")
            return redirect('editar_gasto', id=id)
        


            

        g.concepto = concepto
        g.categoria = categoria
        g.valor = valor
        g.metodo_pago = metodo_pago
        g.save()
        messages.success(request, "Gasto actualizado con éxito.")
        return redirect('inicio_contabilidad')

    contexto = {
        "gasto": g
    }
    return render(request, "contabilidad/editar_gasto.html", contexto)

class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer

@solo_admin
def cierre_caja(request):
    total_recaudado = 0
    total_mesas_cobradas = 0
    mesas_procesadas = []
    total_platos_vendidos = 0
    
    fecha_seleccionada = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    
    # Filtramos por el campo fecha_hora del consumo, que es el momento real en que se paga/registra
    consumos_pagados = ConsumoMesa.objects.filter(
        pagado=True,
        fecha_hora__date=fecha_seleccionada
    )
    
    for c in consumos_pagados:
        total_recaudado += c.subtotal()
        total_platos_vendidos += c.cantidad
        
        # Conteo de mesas únicas evitando duplicados
        if c.mesa.id not in mesas_procesadas:
            mesas_procesadas.append(c.mesa.id)
            total_mesas_cobradas += 1

    contexto = {
        'consumos': consumos_pagados,
        'total_recaudado': total_recaudado,
        'total_mesas_cobradas': total_mesas_cobradas,
        'total_platos_vendidos': total_platos_vendidos,
        'fecha_actual': fecha_seleccionada,
    }
    
    return render(request, "contabilidad/inicio_cierre_caja.html", contexto)

@solo_admin
def historia_cierres(request):
    pass