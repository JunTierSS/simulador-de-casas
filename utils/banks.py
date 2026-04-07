"""
Datos de bancos chilenos y estimaciones de arriendo por zona.
Tasas actualizadas a marzo 2026 (fuente: neatpagos.com).
"""

BANCOS = {
    "Banco Itau": {
        "tasa_fija": 3.39,
        "tasa_mixta": 4.70,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "Mejor tasa del mercado",
    },
    "Banco Falabella": {
        "tasa_fija": 3.70,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "Tasa preferencial para clientes",
    },
    "BancoEstado": {
        "tasa_fija": 4.19,
        "tasa_mixta": None,
        "pie_minimo": 10,
        "plazo_max": 30,
        "financiamiento_max": 90,
        "notas": "10% pie con FOGAES (viviendas hasta 4.500 UF)",
    },
    "Coopeuch": {
        "tasa_fija": 4.50,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "",
    },
    "Scotiabank": {
        "tasa_fija": 5.07,
        "tasa_mixta": 4.84,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "Tasas con subsidio disponibles",
    },
    "Banco Consorcio": {
        "tasa_fija": 5.40,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "",
    },
    "Banco BCI": {
        "tasa_fija": 5.41,
        "tasa_mixta": 5.51,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "",
    },
    "BICE Hipotecaria": {
        "tasa_fija": 5.50,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "Flexibilidad en plazos",
    },
    "Security": {
        "tasa_fija": 5.50,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 40,
        "financiamiento_max": 80,
        "notas": "Plazo extendido hasta 40 anos",
    },
    "Banco de Chile": {
        "tasa_fija": 5.89,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "",
    },
    "Banco Santander": {
        "tasa_fija": 5.99,
        "tasa_mixta": None,
        "pie_minimo": 20,
        "plazo_max": 30,
        "financiamiento_max": 80,
        "notas": "",
    },
}

# Subsidio al Dividendo (2025-2027): rebaja tasa entre 0.61% y 1.16%
SUBSIDIO_DIVIDENDO = {
    "rebaja_tasa_min": 0.61,
    "rebaja_tasa_max": 1.16,
    "rebaja_tasa_promedio": 0.88,
    "tope_vivienda_uf": 4000,
    "solo_vivienda_nueva": True,
    "pie_reducido": 10,
    "vigencia_hasta": "27/05/2027",
}

# FOGAES Vivienda
FOGAES = {
    "cobertura_pie": 10,  # cubre hasta 10% del pie
    "tope_vivienda_uf": 4500,
    "solo_primera_vivienda": True,
}

# DS1 - Bono Primera Vivienda
DS1_TRAMOS = {
    "Tramo 1": {
        "subsidio_max_uf": 600,
        "tope_vivienda_uf": 1100,
        "ahorro_min_uf": 30,
    },
    "Tramo 2": {
        "subsidio_max_uf": 450,
        "tope_vivienda_uf": 1600,
        "ahorro_min_uf": 40,
    },
    "Tramo 3": {
        "subsidio_max_uf": 400,  # promedio 250-550
        "tope_vivienda_uf": 2200,
        "ahorro_min_uf": 80,
    },
}

# Estimacion arriendo por zona de Santiago (UF/m2/mes)
ZONAS_ARRIENDO = {
    "Zona Alta (Las Condes, Vitacura, Lo Barnechea)": {
        "uf_m2_min": 0.22,
        "uf_m2_max": 0.30,
        "uf_m2_promedio": 0.26,
    },
    "Zona Media Alta (Providencia, Nunoa, La Reina)": {
        "uf_m2_min": 0.16,
        "uf_m2_max": 0.22,
        "uf_m2_promedio": 0.19,
    },
    "Zona Centro (Santiago Centro, Independencia)": {
        "uf_m2_min": 0.12,
        "uf_m2_max": 0.18,
        "uf_m2_promedio": 0.15,
    },
    "Zona Baja (Maipu, Puente Alto, La Florida)": {
        "uf_m2_min": 0.08,
        "uf_m2_max": 0.13,
        "uf_m2_promedio": 0.105,
    },
}

# Gastos de escrituracion tipicos (en UF)
GASTOS_ESCRITURACION_DEFAULT = {
    "estudio_titulos": 6.0,
    "tasacion": 4.0,
    "notaria": 8.0,
    "inscripcion_cbr": 3.0,
    "gastos_operacionales": 5.0,
}


def obtener_nombres_bancos():
    """Retorna lista de nombres de bancos disponibles."""
    return list(BANCOS.keys()) + ["Banco Custom"]


def obtener_datos_banco(nombre):
    """Retorna datos de un banco por nombre."""
    if nombre == "Banco Custom":
        return {
            "tasa_fija": 5.0,
            "tasa_mixta": None,
            "pie_minimo": 20,
            "plazo_max": 30,
            "financiamiento_max": 80,
            "notas": "Banco personalizado",
        }
    return BANCOS.get(nombre, None)


def estimar_arriendo(zona, metros_cuadrados):
    """Estima arriendo mensual en UF basado en zona y m2."""
    datos_zona = ZONAS_ARRIENDO.get(zona)
    if not datos_zona:
        return 0, 0, 0
    arriendo_min = datos_zona["uf_m2_min"] * metros_cuadrados
    arriendo_max = datos_zona["uf_m2_max"] * metros_cuadrados
    arriendo_promedio = datos_zona["uf_m2_promedio"] * metros_cuadrados
    return round(arriendo_min, 2), round(arriendo_promedio, 2), round(arriendo_max, 2)


def obtener_nombres_zonas():
    """Retorna lista de zonas disponibles."""
    return list(ZONAS_ARRIENDO.keys())


def obtener_tramos_ds1():
    """Retorna lista de tramos DS1 disponibles."""
    return ["Sin subsidio DS1"] + list(DS1_TRAMOS.keys())
