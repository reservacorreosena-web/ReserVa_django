from decimal import Decimal

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.http import require_POST
from reservas.models import ConsumoMesa
from usuarios.models import Usuario

from usuarios.decorador import verificar, solo_admin
from .models import Movimiento, Comentario_caja, SesionCaja

from .serializador import MovimientoSerializer, ComentarioCajaSerializer
from rest_framework import viewsets
from datetime import datetime

# Esta es la parte principal, acá mostraremos todos los movimientos
@solo_admin
def inicio(request):
    movimientos = Movimiento.objects.all().order_by('-fecha', '-id')

    gasto_total = 0
    ingreso_total = 0
    gasto_efectivo = 0
    gasto_banco = 0
    ingreso_efectivo = 0
    ingreso_banco = 0

    for g in movimientos:
        metodo = g.metodo_pago.strip().lower() if g.metodo_pago else ""
        valor = g.valor or 0
        tipo = (g.tipo or '').strip().upper()

        if tipo == 'GASTO':
            gasto_total += valor
            if metodo == "efectivo":
                gasto_efectivo += valor
            elif any(x in metodo for x in ["tarjeta", "transferencia", "débito", "debito", "crédito", "credito", "nequi", "daviplata"]):
                gasto_banco += valor
        elif tipo == 'INGRESO':
            ingreso_total += valor
            if metodo == "efectivo":
                ingreso_efectivo += valor
            elif any(x in metodo for x in ["tarjeta", "transferencia", "débito", "debito", "crédito", "credito", "nequi", "daviplata"]):
                ingreso_banco += valor

    saldo_neto = ingreso_total - gasto_total

    q = {
        'movimientos': movimientos,
        'gastos': movimientos,
        'gasto_total': gasto_total,
        'ingreso_total': ingreso_total,
        'saldo_neto': saldo_neto,
        'gasto_efectivo': gasto_efectivo,
        'gasto_banco': gasto_banco,
        'ingreso_efectivo': ingreso_efectivo,
        'ingreso_banco': ingreso_banco,
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
@require_POST
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


@solo_admin
def cierre_caja(request):
    fecha_seleccionada = request.GET.get('fecha', timezone.now().date().strftime('%Y-%m-%d'))
    caja_abierta = SesionCaja.objects.filter(estado='ABIERTA').first()
    
    consumos_pagados = ConsumoMesa.objects.filter(
        pagado=True,
        fecha_hora__date=fecha_seleccionada
    ).select_related('mesa', 'plato', 'reserva__usuario')
    
    total_recaudado = sum(c.subtotal() for c in consumos_pagados)
    total_platos_vendidos = sum(c.cantidad for c in consumos_pagados)
    
    mesas_procesadas = set(c.mesa.id for c in consumos_pagados)
    total_mesas_cobradas = len(mesas_procesadas)

    contexto = {
        'consumos': consumos_pagados,
        'total_recaudado': total_recaudado,
        'total_mesas_cobradas': total_mesas_cobradas,
        'total_platos_vendidos': total_platos_vendidos,
        'fecha_actual': fecha_seleccionada,
        'caja_abierta': caja_abierta,
        'observacion_actual': Comentario_caja.objects.filter(fecha=fecha_seleccionada).values_list('comentario', flat=True).first() or "",
    }
    
    return render(request, "contabilidad/inicio_cierre_caja.html", contexto)


@solo_admin
def comentario_caja(request):
    if request.method == "POST":
        texto = request.POST.get("observacion")
        fecha_form = request.POST.get("fecha")
  
        Comentario_caja.objects.update_or_create(
            fecha=fecha_form,
            defaults={'comentario': texto}
        )
        
        messages.success(request, "¡Creado Con Éxito!")

    return redirect('inicio_cierre_caja')


@solo_admin
def abrir_caja(request):
    caja_abierta = SesionCaja.objects.filter(estado='ABIERTA').first()

    if request.method == 'POST':
        if caja_abierta:
            messages.error(request, "Ya existe una caja abierta. Debes cerrarla antes de abrir una nueva.")
            return redirect('abrir_caja')

        saldo_inicial_raw = request.POST.get('saldo_inicial', '0').strip()

        try:
            saldo_inicial = Decimal(saldo_inicial_raw)
            if saldo_inicial < 0:
                messages.error(request, "El saldo inicial no puede ser negativo.")
                return redirect('abrir_caja')
        except Exception:
            messages.error(request, "Ingresa un valor numérico válido para el saldo inicial.")
            return redirect('abrir_caja')

        sesion_data = request.session.get('logueado', {})
        usuario = None
        if sesion_data and sesion_data.get('id'):
            usuario = Usuario.objects.filter(id=sesion_data['id']).first()

        SesionCaja.objects.create(
            saldo_inicial=saldo_inicial,
            usuario_apertura=usuario,
        )
        messages.success(request, f"¡Caja abierta con éxito! Base inicial: ${saldo_inicial:,.0f}")
        return redirect('inicio_cierre_caja')

    fecha_seleccionada = timezone.now().date()

    contexto = {
        'caja_abierta': caja_abierta,
        'observacion_actual': Comentario_caja.objects.filter(fecha=fecha_seleccionada).values_list('comentario', flat=True).first() or "",
    }
    return render(request, 'contabilidad/abrir_caja.html', contexto)


@solo_admin
def cerrar_caja_proceso(request):
    caja_abierta = SesionCaja.objects.filter(estado='ABIERTA').first()

    if not caja_abierta:
        messages.error(request, "No hay ninguna caja abierta para cerrar.")
        return redirect('inicio_cierre_caja')

    fecha_seleccionada = timezone.now().date()

    fecha_apertura = caja_abierta.fecha_apertura.date()

    # Ventas: Movimientos de tipo INGRESO registrados desde la apertura de caja
    ingresos_qs = Movimiento.objects.filter(
        tipo='INGRESO',
        fecha__gte=fecha_apertura,
    )
    total_ventas = ingresos_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0')
    try:
        total_ventas = Decimal(str(total_ventas))
    except Exception:
        total_ventas = Decimal('0')

    # Gastos: Movimientos de tipo GASTO registrados desde la apertura de caja
    gastos_qs = Movimiento.objects.filter(
        tipo='GASTO',
        fecha__gte=fecha_apertura,
    )
    total_gastos = gastos_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0')
    try:
        total_gastos = Decimal(str(total_gastos))
    except Exception:
        total_gastos = Decimal('0')

    balance_esperado = caja_abierta.saldo_inicial + total_ventas - total_gastos

    # También mostrar mesas cerradas/cobradas el día para mayor claridad
    try:
        from reservas.models import ConsumoMesa
        consumos_pagados_hoy = ConsumoMesa.objects.filter(
            pagado=True,
            fecha_hora__date__gte=fecha_apertura
        ).select_related('mesa', 'plato', 'reserva__usuario')
        total_recaudado_mesas = sum((c.subtotal() for c in consumos_pagados_hoy), Decimal('0'))
        mesas_cerradas = len(set(c.mesa_id for c in consumos_pagados_hoy))
    except Exception:
        consumos_pagados_hoy = []
        total_recaudado_mesas = Decimal('0')
        mesas_cerradas = 0

    if request.method == 'POST':
        dinero_real_raw = request.POST.get('dinero_real', '0').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        try:
            dinero_real = Decimal(dinero_real_raw)
            if dinero_real < 0:
                messages.error(request, "El dinero real no puede ser negativo.")
                return redirect('cerrar_caja')
        except Exception:
            messages.error(request, "Ingresa un valor numérico válido para el dinero en caja.")
            return redirect('cerrar_caja')

        diferencia = dinero_real - balance_esperado

        sesion_data = request.session.get('logueado', {})
        usuario = None
        if sesion_data and sesion_data.get('id'):
            try:
                usuario = Usuario.objects.filter(id=sesion_data['id']).first()
            except Exception:
                usuario = None

        caja_abierta.total_ventas = total_ventas
        caja_abierta.total_gastos = total_gastos
        caja_abierta.balance_esperado = balance_esperado
        caja_abierta.dinero_real = dinero_real
        caja_abierta.diferencia = diferencia
        caja_abierta.observaciones = observaciones
        caja_abierta.usuario_cierre = usuario
        caja_abierta.fecha_cierre = timezone.now()
        caja_abierta.estado = 'CERRADA'
        caja_abierta.save()

        messages.success(request, "¡Caja cerrada con éxito! El cierre ha sido registrado.")
        return redirect('inicio_cierre_caja')

    fecha_seleccionada = timezone.now().date()

    contexto = {
        'caja': caja_abierta,
        'total_ventas': total_ventas,
        'total_gastos': total_gastos,
        'balance_esperado': balance_esperado,
        'ingresos': ingresos_qs,
        'gastos_lista': gastos_qs,
        'consumos_pagados_hoy': consumos_pagados_hoy,
        'total_recaudado_mesas': total_recaudado_mesas,
        'mesas_cerradas': mesas_cerradas,
    }
    return render(request, 'contabilidad/cerrar_caja.html', contexto)


@solo_admin
def historial_cierres(request):
    cierres = SesionCaja.objects.filter(estado='CERRADA').order_by('-fecha_cierre')
    contexto = {
        'cierres': cierres,
    }
    return render(request, 'contabilidad/historial_cierres.html', contexto)


# ==========================================
# VIEWSETS PARA LA API REST
# ==========================================
from usuarios.permissions import IsUsuarioAdmin


class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all().order_by('-id')
    serializer_class = MovimientoSerializer
    permission_classes = [IsUsuarioAdmin]


class ComentarioCajaViewSet(viewsets.ModelViewSet):
    queryset = Comentario_caja.objects.all().order_by('-id')
    serializer_class = ComentarioCajaSerializer
    permission_classes = [IsUsuarioAdmin]