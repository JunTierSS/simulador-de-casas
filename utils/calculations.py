"""
Calculos financieros para creditos hipotecarios.
Incluye: dividendo frances/aleman, amortizacion, CAE, valor futuro, flujo arriendo.
"""

import numpy as np
import pandas as pd
from scipy.optimize import brentq


def calcular_monto_credito(precio_uf, pie_porcentaje, bono_uf=0, subsidio_dividendo_activo=False):
    """Calcula el monto a financiar descontando pie y bonos."""
    pie = precio_uf * (pie_porcentaje / 100)
    monto = precio_uf - pie - bono_uf
    return max(monto, 0), pie


def dividendo_frances(monto, tasa_anual, plazo_anos):
    """Calcula cuota fija mensual (sistema frances)."""
    if monto <= 0 or plazo_anos <= 0:
        return 0
    r = tasa_anual / 100 / 12
    n = plazo_anos * 12
    if r == 0:
        return monto / n
    cuota = monto * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return cuota


def dividendo_aleman(monto, tasa_anual, plazo_anos, mes=1):
    """Calcula cuota del mes indicado (sistema aleman - cuota decreciente)."""
    if monto <= 0 or plazo_anos <= 0:
        return 0
    r = tasa_anual / 100 / 12
    n = plazo_anos * 12
    amortizacion = monto / n
    saldo = monto - amortizacion * (mes - 1)
    interes = saldo * r
    return amortizacion + interes


def generar_tabla_amortizacion(monto, tasa_anual, plazo_anos, sistema="frances",
                                seguro_desgravamen_pct=0, seguro_incendio_uf=0):
    """
    Genera tabla de amortizacion completa.
    Retorna DataFrame con columnas: mes, cuota, interes, capital, saldo,
    seg_desgravamen, seg_incendio, cuota_total
    """
    if monto <= 0 or plazo_anos <= 0:
        return pd.DataFrame()

    r = tasa_anual / 100 / 12
    n = plazo_anos * 12
    saldo = monto
    filas = []

    if sistema == "frances":
        cuota_base = dividendo_frances(monto, tasa_anual, plazo_anos)

    for mes in range(1, n + 1):
        interes = saldo * r

        if sistema == "frances":
            capital = cuota_base - interes
            cuota = cuota_base
        else:  # aleman
            capital = monto / n
            cuota = capital + interes

        seg_desgravamen = saldo * (seguro_desgravamen_pct / 100 / 12)
        seg_incendio = seguro_incendio_uf
        cuota_total = cuota + seg_desgravamen + seg_incendio

        saldo_nuevo = saldo - capital

        filas.append({
            "mes": mes,
            "ano": (mes - 1) // 12 + 1,
            "cuota_base": round(cuota, 4),
            "interes": round(interes, 4),
            "capital": round(capital, 4),
            "saldo": round(max(saldo_nuevo, 0), 4),
            "seg_desgravamen": round(seg_desgravamen, 4),
            "seg_incendio": round(seg_incendio, 4),
            "cuota_total": round(cuota_total, 4),
        })

        saldo = max(saldo_nuevo, 0)

    return pd.DataFrame(filas)


def calcular_cae(monto, cuotas_totales, gastos_iniciales=0):
    """
    Calcula la Carga Anual Equivalente (CAE).
    cuotas_totales: lista/array de cuotas mensuales totales (incluyendo seguros).
    gastos_iniciales: gastos de escrituracion + operacionales.
    """
    if monto <= 0 or len(cuotas_totales) == 0:
        return 0

    monto_neto = monto - gastos_iniciales

    def ecuacion_cae(cae_mensual):
        vp = sum(c / (1 + cae_mensual) ** k for k, c in enumerate(cuotas_totales, 1))
        return vp - monto_neto

    try:
        cae_mensual = brentq(ecuacion_cae, -0.01, 0.05, maxiter=1000)
        cae_anual = (1 + cae_mensual) ** 12 - 1
        return round(cae_anual * 100, 2)
    except (ValueError, RuntimeError):
        return 0


def calcular_valor_futuro(precio_actual_uf, tasa_apreciacion_anual, anos):
    """Calcula valor futuro de la propiedad con apreciacion compuesta."""
    valores = []
    for ano in range(anos + 1):
        vf = precio_actual_uf * (1 + tasa_apreciacion_anual / 100) ** ano
        valores.append({"ano": ano, "valor_futuro_uf": round(vf, 2)})
    return valores


def calcular_flujo_arriendo(arriendo_mensual_uf, tabla_amortizacion,
                             gastos_comunes_uf=0, contribuciones_trim_uf=0,
                             tasa_incremento_arriendo=3.0):
    """
    Calcula flujo de caja neto mensual: arriendo - dividendo - gastos.
    Incluye incremento anual del arriendo.
    """
    if tabla_amortizacion.empty:
        return pd.DataFrame()

    contribucion_mensual = contribuciones_trim_uf / 3
    flujos = []
    arriendo_actual = arriendo_mensual_uf

    for _, fila in tabla_amortizacion.iterrows():
        mes = fila["mes"]
        ano = fila["ano"]

        # Incrementar arriendo cada 12 meses
        if mes > 1 and (mes - 1) % 12 == 0:
            arriendo_actual *= (1 + tasa_incremento_arriendo / 100)

        flujo_neto = arriendo_actual - fila["cuota_total"] - gastos_comunes_uf - contribucion_mensual

        flujos.append({
            "mes": mes,
            "ano": ano,
            "arriendo": round(arriendo_actual, 4),
            "dividendo": round(fila["cuota_total"], 4),
            "gastos_comunes": gastos_comunes_uf,
            "contribuciones": round(contribucion_mensual, 4),
            "flujo_neto": round(flujo_neto, 4),
        })

    return pd.DataFrame(flujos)


def calcular_gastos_iniciales(gastos_dict):
    """Suma todos los gastos de escrituracion."""
    return sum(gastos_dict.values())


def calcular_impuesto_timbres(monto_credito, es_dfl2=False):
    """Impuesto de timbres y estampillas: 0.8% del prestamo (0.2% si DFL2)."""
    tasa = 0.002 if es_dfl2 else 0.008
    return round(monto_credito * tasa, 2)


def calcular_comision_corretaje(precio_uf, es_usada=False):
    """Comision de corretaje: 2% + IVA solo para propiedades usadas."""
    if not es_usada:
        return 0
    return round(precio_uf * 0.02 * 1.19, 2)


def calcular_iva_propiedad(precio_uf, es_nueva=True, iva_exento=False):
    """IVA en propiedades nuevas (19%). Puede estar exento temporalmente."""
    if not es_nueva or iva_exento:
        return 0
    return round(precio_uf * 0.19, 2)


def calcular_renta_minima(dividendo_mensual_uf, valor_uf_clp, porcentaje_renta=25):
    """Calcula la renta liquida minima requerida (regla del 25%)."""
    dividendo_clp = dividendo_mensual_uf * valor_uf_clp
    renta_min = dividendo_clp / (porcentaje_renta / 100)
    return round(renta_min, 0)


def calcular_capacidad_compra(renta_liquida_clp, tasa_anual, plazo_anos, pie_pct,
                               valor_uf_clp, porcentaje_renta=25):
    """Calculadora inversa: cuanta casa puedo comprar con mi renta."""
    max_dividendo_clp = renta_liquida_clp * (porcentaje_renta / 100)
    max_dividendo_uf = max_dividendo_clp / valor_uf_clp

    r = tasa_anual / 100 / 12
    n = plazo_anos * 12
    if r == 0:
        monto_max = max_dividendo_uf * n
    else:
        monto_max = max_dividendo_uf * ((1 + r) ** n - 1) / (r * (1 + r) ** n)

    # monto_max = precio * (1 - pie/100) => precio = monto_max / (1 - pie/100)
    if pie_pct >= 100:
        return 0
    precio_max = monto_max / (1 - pie_pct / 100)
    return round(precio_max, 2)


def calcular_cap_rate(arriendo_anual_uf, precio_uf):
    """Cap Rate bruto = arriendo anual / precio compra * 100."""
    if precio_uf <= 0:
        return 0
    return round((arriendo_anual_uf / precio_uf) * 100, 2)


def calcular_cap_rate_neto(arriendo_anual_uf, gastos_anuales_uf, precio_uf):
    """Cap Rate neto = (arriendo - gastos) anual / precio * 100."""
    if precio_uf <= 0:
        return 0
    noi = arriendo_anual_uf - gastos_anuales_uf
    return round((noi / precio_uf) * 100, 2)


def calcular_roi(ganancia_neta_anual_uf, inversion_total_uf):
    """ROI = ganancia neta / inversion total * 100."""
    if inversion_total_uf <= 0:
        return 0
    return round((ganancia_neta_anual_uf / inversion_total_uf) * 100, 2)


def calcular_cash_on_cash(flujo_neto_anual_uf, capital_invertido_uf):
    """Cash on Cash Return = flujo neto anual / capital propio invertido (pie + gastos)."""
    if capital_invertido_uf <= 0:
        return 0
    return round((flujo_neto_anual_uf / capital_invertido_uf) * 100, 2)


def calcular_beneficios_dfl2(precio_uf, contribuciones_trim_uf, metros_cuadrados,
                              arriendo_anual_uf, num_propiedades_dfl2=0):
    """
    Calcula beneficios DFL2 (viviendas hasta 140m2).
    - Exencion contribuciones: 50% por 20 anos (<=70m2), 50% por 15 anos (71-100m2), 50% por 10 anos (101-140m2)
    - Arriendo exento impuesto renta (max 2 propiedades DFL2)
    - Impuesto timbres reducido (0.2% vs 0.8%)
    """
    aplica = metros_cuadrados <= 140
    if not aplica:
        return {"aplica_dfl2": False, "ahorro_contribuciones_anual": 0,
                "arriendo_exento": False, "timbres_reducido": False,
                "anos_exencion_contrib": 0}

    if metros_cuadrados <= 70:
        anos_exencion = 20
    elif metros_cuadrados <= 100:
        anos_exencion = 15
    else:
        anos_exencion = 10

    ahorro_contrib_anual = contribuciones_trim_uf * 4 * 0.5  # 50% de las contribuciones anuales
    arriendo_exento = num_propiedades_dfl2 < 2

    return {
        "aplica_dfl2": True,
        "ahorro_contribuciones_anual": round(ahorro_contrib_anual, 2),
        "arriendo_exento": arriendo_exento,
        "timbres_reducido": True,
        "anos_exencion_contrib": anos_exencion,
    }


def evaluar_semaforo(cap_rate_neto, cash_on_cash, flujo_neto_promedio):
    """
    Indicador semaforo para la inversion.
    Verde: buena inversion, Amarillo: aceptable, Rojo: mala inversion.
    """
    puntaje = 0

    # Cap Rate neto
    if cap_rate_neto >= 5.5:
        puntaje += 3
    elif cap_rate_neto >= 4.0:
        puntaje += 2
    elif cap_rate_neto >= 3.0:
        puntaje += 1

    # Cash on Cash
    if cash_on_cash >= 10:
        puntaje += 3
    elif cash_on_cash >= 5:
        puntaje += 2
    elif cash_on_cash >= 2:
        puntaje += 1

    # Flujo neto
    if flujo_neto_promedio > 0:
        puntaje += 2
    elif flujo_neto_promedio > -2:
        puntaje += 1

    if puntaje >= 6:
        return "verde", "Buena inversion"
    elif puntaje >= 3:
        return "amarillo", "Inversion aceptable"
    else:
        return "rojo", "Inversion riesgosa"


def calcular_resumen_escenario(precio_uf, pie_pct, bono_uf, tasa_anual, plazo_anos,
                                 sistema, seguro_desgravamen_pct, seguro_incendio_uf,
                                 gastos_escrituracion, arriendo_uf, gastos_comunes_uf,
                                 contribuciones_trim_uf, tasa_apreciacion, valor_uf_clp,
                                 subsidio_dividendo=False, fogaes=False, ds1_tramo=None,
                                 metros_cuadrados=60, es_nueva=True, iva_exento=False,
                                 vacancia_meses=1, num_propiedades_dfl2=0,
                                 porcentaje_renta=25):
    """Calcula resumen completo de un escenario."""

    # Ajustar tasa si tiene subsidio al dividendo
    tasa_efectiva = tasa_anual
    if subsidio_dividendo and precio_uf <= 4000:
        tasa_efectiva = max(tasa_anual - 0.88, 0)  # rebaja promedio 0.88%

    # Calcular monto credito
    monto_credito, pie_monto = calcular_monto_credito(precio_uf, pie_pct, bono_uf)

    # DFL2
    dfl2 = calcular_beneficios_dfl2(precio_uf, contribuciones_trim_uf, metros_cuadrados,
                                     arriendo_uf * 12, num_propiedades_dfl2)

    # Impuesto timbres
    imp_timbres = calcular_impuesto_timbres(monto_credito, es_dfl2=dfl2["aplica_dfl2"])

    # Corretaje (solo usadas)
    corretaje = calcular_comision_corretaje(precio_uf, es_usada=not es_nueva)

    # IVA propiedad nueva
    iva = calcular_iva_propiedad(precio_uf, es_nueva=es_nueva, iva_exento=iva_exento)

    # Generar tabla amortizacion
    tabla = generar_tabla_amortizacion(
        monto_credito, tasa_efectiva, plazo_anos, sistema,
        seguro_desgravamen_pct, seguro_incendio_uf
    )

    if tabla.empty:
        return None

    # Metricas principales
    dividendo_mes1 = tabla.iloc[0]["cuota_total"] if not tabla.empty else 0
    dividendo_base_mes1 = tabla.iloc[0]["cuota_base"] if not tabla.empty else 0
    total_pagado = tabla["cuota_total"].sum()
    total_intereses = tabla["interes"].sum()
    total_capital = tabla["capital"].sum()
    total_seguros = tabla["seg_desgravamen"].sum() + tabla["seg_incendio"].sum()

    # Gastos iniciales (escrituracion + timbres + corretaje)
    gastos_ini = calcular_gastos_iniciales(gastos_escrituracion) + imp_timbres + corretaje

    # CAE
    cae = calcular_cae(monto_credito, tabla["cuota_total"].tolist(), gastos_ini)

    # Renta minima requerida
    renta_minima = calcular_renta_minima(dividendo_mes1, valor_uf_clp, porcentaje_renta)

    # Valor futuro
    valor_futuro = calcular_valor_futuro(precio_uf, tasa_apreciacion, plazo_anos)

    # Flujo arriendo (considerando vacancia)
    arriendo_con_vacancia = arriendo_uf * (12 - vacancia_meses) / 12
    flujo_arriendo = calcular_flujo_arriendo(
        arriendo_con_vacancia, tabla, gastos_comunes_uf, contribuciones_trim_uf
    )

    # Costo total real
    costo_total = total_pagado + pie_monto + gastos_ini

    # Ganancia neta si vende al final del plazo
    vf_final = valor_futuro[-1]["valor_futuro_uf"] if valor_futuro else precio_uf
    ganancia_neta = vf_final - costo_total

    # Flujo neto promedio mensual
    flujo_neto_promedio = flujo_arriendo["flujo_neto"].mean() if not flujo_arriendo.empty else 0

    # --- Metricas de inversion ---
    arriendo_anual = arriendo_uf * 12
    arriendo_anual_con_vacancia = arriendo_uf * (12 - vacancia_meses)
    gastos_anuales = (gastos_comunes_uf * 12) + (contribuciones_trim_uf * 4)
    if dfl2["aplica_dfl2"]:
        gastos_anuales -= dfl2["ahorro_contribuciones_anual"]

    cap_rate_bruto = calcular_cap_rate(arriendo_anual, precio_uf)
    cap_rate_neto = calcular_cap_rate_neto(arriendo_anual_con_vacancia, gastos_anuales, precio_uf)

    # Capital propio invertido = pie + gastos iniciales
    capital_invertido = pie_monto + gastos_ini
    flujo_neto_anual = flujo_neto_promedio * 12
    cash_on_cash = calcular_cash_on_cash(flujo_neto_anual, capital_invertido)

    # ROI total (incluye plusvalia prorrateada)
    plusvalia_anual = (vf_final - precio_uf) / plazo_anos if plazo_anos > 0 else 0
    roi = calcular_roi(flujo_neto_anual + plusvalia_anual, capital_invertido)

    # Semaforo
    semaforo_color, semaforo_texto = evaluar_semaforo(cap_rate_neto, cash_on_cash, flujo_neto_promedio)

    return {
        "precio_uf": precio_uf,
        "pie_pct": pie_pct,
        "pie_monto_uf": round(pie_monto, 2),
        "bono_uf": bono_uf,
        "monto_credito_uf": round(monto_credito, 2),
        "tasa_original": tasa_anual,
        "tasa_efectiva": round(tasa_efectiva, 2),
        "plazo_anos": plazo_anos,
        "sistema": sistema,
        "dividendo_mes1_uf": round(dividendo_mes1, 4),
        "dividendo_mes1_clp": round(dividendo_mes1 * valor_uf_clp, 0),
        "dividendo_base_mes1_uf": round(dividendo_base_mes1, 4),
        "total_pagado_uf": round(total_pagado, 2),
        "total_intereses_uf": round(total_intereses, 2),
        "total_capital_uf": round(total_capital, 2),
        "total_seguros_uf": round(total_seguros, 2),
        "gastos_iniciales_uf": round(gastos_ini, 2),
        "imp_timbres_uf": imp_timbres,
        "corretaje_uf": corretaje,
        "iva_uf": iva,
        "costo_total_uf": round(costo_total, 2),
        "costo_total_clp": round(costo_total * valor_uf_clp, 0),
        "cae": cae,
        "renta_minima_clp": renta_minima,
        "valor_futuro_final_uf": round(vf_final, 2),
        "ganancia_neta_uf": round(ganancia_neta, 2),
        "arriendo_mensual_uf": arriendo_uf,
        "flujo_neto_promedio_uf": round(flujo_neto_promedio, 4),
        "tabla_amortizacion": tabla,
        "valor_futuro_serie": valor_futuro,
        "flujo_arriendo": flujo_arriendo,
        # Metricas de inversion
        "cap_rate_bruto": cap_rate_bruto,
        "cap_rate_neto": cap_rate_neto,
        "cash_on_cash": cash_on_cash,
        "roi": roi,
        "capital_invertido_uf": round(capital_invertido, 2),
        "dfl2": dfl2,
        "vacancia_meses": vacancia_meses,
        "semaforo_color": semaforo_color,
        "semaforo_texto": semaforo_texto,
    }
