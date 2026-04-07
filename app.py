"""
Simulador de Precios de Casas - Dashboard Interactivo
Compara escenarios de financiamiento hipotecario en Chile.
"""

import streamlit as st
import json
import pandas as pd

from utils.banks import (
    obtener_nombres_bancos, obtener_datos_banco, estimar_arriendo,
    obtener_nombres_zonas, obtener_tramos_ds1, DS1_TRAMOS,
    GASTOS_ESCRITURACION_DEFAULT, SUBSIDIO_DIVIDENDO,
)
from utils.calculations import calcular_resumen_escenario, calcular_capacidad_compra
from utils.charts import (
    grafico_dividendo_comparado, grafico_evolucion_saldo,
    grafico_interes_vs_capital, grafico_costo_total,
    grafico_flujo_caja_neto, grafico_valor_futuro,
    grafico_ganancia_neta, grafico_dividendo_vs_arriendo,
)
from utils.export import exportar_pdf, exportar_excel

# =====================================================================
# Configuracion de pagina
# =====================================================================
st.set_page_config(
    page_title="Simulador de Casas Chile",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# Estado inicial
# =====================================================================
if "escenarios" not in st.session_state:
    st.session_state.escenarios = [1, 2]  # IDs de escenarios
if "next_id" not in st.session_state:
    st.session_state.next_id = 3
if "bancos_custom" not in st.session_state:
    st.session_state.bancos_custom = {}

# =====================================================================
# CSS personalizado
# =====================================================================
st.markdown("""
<style>
    .stMetric > div { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 10px; border-radius: 10px; color: white; }
    .stMetric label { color: white !important; }
    .stMetric [data-testid="stMetricValue"] { color: white !important; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# Sidebar - Configuracion Global
# =====================================================================
with st.sidebar:
    st.title("Configuracion Global")

    valor_uf = st.number_input(
        "Valor UF (CLP)", value=38500, min_value=10000, max_value=80000,
        step=100, help="Ingrese el valor actual de la UF en pesos chilenos"
    )

    mostrar_pesos = st.toggle("Mostrar en pesos ($)", value=False,
                               help="Cambia todos los montos entre UF y pesos chilenos")

    perfil = st.radio("Perfil", ["Primera Vivienda", "Inversionista"],
                       horizontal=True, help="Cambia las metricas que se muestran")

    porcentaje_renta = st.slider(
        "Dividendo max / renta (%)", min_value=15, max_value=40, value=25, step=1,
        help="Porcentaje maximo del ingreso neto que puede destinarse al dividendo. Bancos conservadores usan 25%, algunos llegan hasta 30-35%."
    )

    st.divider()

    # Calculadora inversa
    with st.expander("Cuanta casa me alcanza?"):
        renta_input = st.number_input("Tu renta liquida mensual ($)", value=1500000,
                                       min_value=0, step=50000, key="renta_inversa")
        tasa_inv = st.number_input("Tasa estimada (%)", value=4.5, min_value=0.0,
                                    max_value=20.0, step=0.1, key="tasa_inversa")
        plazo_inv = st.slider("Plazo (anos)", 5, 40, 25, key="plazo_inverso")
        pie_inv = st.slider("Pie (%)", 0, 50, 20, key="pie_inverso")

        precio_max = calcular_capacidad_compra(renta_input, tasa_inv, plazo_inv,
                                                pie_inv, valor_uf, porcentaje_renta)
        precio_max_clp = precio_max * valor_uf

        st.metric("Precio maximo de casa", f"{precio_max:,.0f} UF")
        st.caption(f"${precio_max_clp:,.0f} CLP")
        st.caption(f"Dividendo max: ${renta_input * (porcentaje_renta / 100):,.0f}/mes ({porcentaje_renta}% de tu renta)")

    st.divider()

    # Gestionar escenarios
    st.subheader("Escenarios")
    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button("+ Agregar", use_container_width=True):
            st.session_state.escenarios.append(st.session_state.next_id)
            st.session_state.next_id += 1
            st.rerun()
    with col_remove:
        if len(st.session_state.escenarios) > 1:
            if st.button("- Quitar ultimo", use_container_width=True):
                st.session_state.escenarios.pop()
                st.rerun()

    st.caption(f"Escenarios activos: {len(st.session_state.escenarios)}")

    st.divider()

    # Crear banco custom
    st.subheader("Crear Banco Custom")
    with st.expander("Agregar nuevo banco"):
        nuevo_nombre = st.text_input("Nombre del banco", key="nuevo_banco_nombre")
        nueva_tasa = st.number_input("Tasa fija (%)", value=5.0, min_value=0.0, max_value=20.0,
                                      step=0.01, key="nuevo_banco_tasa")
        nuevo_pie = st.number_input("Pie minimo (%)", value=20, min_value=0, max_value=100,
                                     key="nuevo_banco_pie")
        nuevo_plazo = st.number_input("Plazo max (anos)", value=30, min_value=1, max_value=40,
                                       key="nuevo_banco_plazo")
        if st.button("Guardar banco"):
            if nuevo_nombre:
                st.session_state.bancos_custom[nuevo_nombre] = {
                    "tasa_fija": nueva_tasa,
                    "tasa_mixta": None,
                    "pie_minimo": nuevo_pie,
                    "plazo_max": nuevo_plazo,
                    "financiamiento_max": 100 - nuevo_pie,
                    "notas": "Banco personalizado",
                }
                st.success(f"Banco '{nuevo_nombre}' creado")
                st.rerun()

    if st.session_state.bancos_custom:
        st.caption("Bancos custom: " + ", ".join(st.session_state.bancos_custom.keys()))

    st.divider()

    # Guardar / Cargar simulacion
    st.subheader("Guardar / Cargar")

    # Guardar: se descarga como JSON
    if st.button("Descargar simulacion (JSON)", use_container_width=True):
        save_data = {
            "valor_uf": valor_uf,
            "bancos_custom": st.session_state.bancos_custom,
            "num_escenarios": len(st.session_state.escenarios),
        }
        st.download_button(
            "Descargar", data=json.dumps(save_data, indent=2, default=str),
            file_name="simulacion_casas.json", mime="application/json",
        )

    # Cargar
    archivo = st.file_uploader("Cargar simulacion", type=["json"])
    if archivo:
        data = json.loads(archivo.read())
        st.session_state.bancos_custom = data.get("bancos_custom", {})
        st.info("Simulacion cargada. Los bancos custom fueron restaurados.")


# =====================================================================
# Helper: lista de bancos disponibles
# =====================================================================
def get_bancos_disponibles():
    bancos = obtener_nombres_bancos()
    for nombre in st.session_state.bancos_custom:
        if nombre not in bancos:
            bancos.insert(-1, nombre)  # antes de "Banco Custom"
    return bancos


def get_datos_banco_ext(nombre):
    if nombre in st.session_state.bancos_custom:
        return st.session_state.bancos_custom[nombre]
    return obtener_datos_banco(nombre)


# =====================================================================
# Titulo principal
# =====================================================================
st.title("Simulador de Precios de Casas")
st.caption("Compara escenarios de financiamiento hipotecario en Chile | Tasas marzo 2026")

st.warning(
    "**Aviso:** Este simulador es una herramienta educativa. Los cálculos son estimaciones referenciales "
    "y **no constituyen asesoría financiera, legal ni tributaria**. "
    "Siempre consulta con un profesional certificado antes de tomar decisiones de inversión o endeudamiento.",
    icon="⚠️",
)

# =====================================================================
# Panel de Escenarios
# =====================================================================
st.header("Escenarios de Financiamiento")

num_escenarios = len(st.session_state.escenarios)
cols = st.columns(min(num_escenarios, 3))

inputs_escenarios = []

for idx, esc_id in enumerate(st.session_state.escenarios):
    col = cols[idx % min(num_escenarios, 3)]
    prefix = f"esc_{esc_id}"

    with col:
        nombre = st.text_input("Nombre", value=f"Escenario {idx + 1}", key=f"{prefix}_nombre")

        # --- Propiedad ---
        with st.expander(f"Propiedad - {nombre}", expanded=True):
            precio_uf = st.number_input("Precio (UF)", value=3000.0, min_value=0.0,
                                         max_value=100000.0, step=50.0, key=f"{prefix}_precio")
            metros = st.number_input("Metros cuadrados", value=60.0, min_value=1.0,
                                      max_value=1000.0, step=5.0, key=f"{prefix}_m2")
            zona = st.selectbox("Zona Santiago", obtener_nombres_zonas(), key=f"{prefix}_zona")
            contribuciones = st.number_input("Contribuciones trimestrales (UF)", value=3.0,
                                              min_value=0.0, step=0.5, key=f"{prefix}_contrib")
            gastos_comunes = st.number_input("Gastos comunes mensuales (UF)", value=2.0,
                                              min_value=0.0, step=0.5, key=f"{prefix}_gc")

        # --- Credito ---
        with st.expander(f"Credito - {nombre}", expanded=True):
            bancos_disp = get_bancos_disponibles()
            banco = st.selectbox("Banco", bancos_disp, key=f"{prefix}_banco")
            datos_banco = get_datos_banco_ext(banco)

            tasa_default = datos_banco["tasa_fija"] if datos_banco else 5.0
            tasa = st.number_input("Tasa interes anual (%)", value=tasa_default,
                                    min_value=0.0, max_value=20.0, step=0.01,
                                    key=f"{prefix}_tasa")

            if datos_banco and datos_banco.get("notas"):
                st.caption(f"Nota: {datos_banco['notas']}")

            plazo_max = datos_banco["plazo_max"] if datos_banco else 30
            plazo = st.slider("Plazo (anos)", min_value=1, max_value=40,
                               value=min(25, plazo_max), key=f"{prefix}_plazo")

            pie_min = datos_banco["pie_minimo"] if datos_banco else 20
            pie = st.slider(f"Pie (%)", min_value=0, max_value=100,
                             value=pie_min, key=f"{prefix}_pie",
                             help=f"Pie minimo sugerido: {pie_min}%")

            sistema = st.selectbox("Sistema amortizacion",
                                    ["frances", "aleman"],
                                    format_func=lambda x: "Frances (cuota fija)" if x == "frances" else "Aleman (cuota decreciente)",
                                    key=f"{prefix}_sistema")

        # --- Subsidios ---
        with st.expander(f"Subsidios - {nombre}"):
            sub_dividendo = st.checkbox(
                "Subsidio al Dividendo (rebaja ~0.88% tasa)",
                key=f"{prefix}_sub_div",
                help=f"Viviendas nuevas hasta {SUBSIDIO_DIVIDENDO['tope_vivienda_uf']:,} UF. Vigente hasta {SUBSIDIO_DIVIDENDO['vigencia_hasta']}",
            )

            tramo_ds1 = st.selectbox("DS1 - Bono Primera Vivienda",
                                      obtener_tramos_ds1(), key=f"{prefix}_ds1")
            bono_uf = 0.0
            if tramo_ds1 != "Sin subsidio DS1":
                datos_tramo = DS1_TRAMOS[tramo_ds1]
                bono_uf = st.number_input(
                    f"Monto bono (max {datos_tramo['subsidio_max_uf']} UF)",
                    value=float(datos_tramo["subsidio_max_uf"]),
                    min_value=0.0,
                    max_value=float(datos_tramo["subsidio_max_uf"]),
                    key=f"{prefix}_bono",
                )
                if precio_uf > datos_tramo["tope_vivienda_uf"]:
                    st.warning(f"Precio excede tope de {datos_tramo['tope_vivienda_uf']} UF para {tramo_ds1}")

        # --- Seguros ---
        with st.expander(f"Seguros (opcional) - {nombre}"):
            seg_desgravamen = st.number_input("Seguro desgravamen (% anual sobre saldo)",
                                               value=0.0, min_value=0.0, max_value=5.0,
                                               step=0.01, key=f"{prefix}_seg_des")
            seg_incendio = st.number_input("Seguro incendio (UF/mes)",
                                            value=0.0, min_value=0.0, max_value=5.0,
                                            step=0.01, key=f"{prefix}_seg_inc")

        # --- Gastos escrituracion ---
        with st.expander(f"Gastos escrituracion - {nombre}"):
            gastos = {}
            for gasto, default in GASTOS_ESCRITURACION_DEFAULT.items():
                label = gasto.replace("_", " ").capitalize()
                gastos[gasto] = st.number_input(
                    f"{label} (UF)", value=default, min_value=0.0,
                    step=0.5, key=f"{prefix}_{gasto}"
                )

        # --- Tipo propiedad e impuestos ---
        with st.expander(f"Tipo propiedad e impuestos - {nombre}"):
            es_nueva = st.checkbox("Vivienda nueva", value=True, key=f"{prefix}_nueva")
            iva_exento = False
            if es_nueva:
                iva_exento = st.checkbox("IVA exento (medida temporal 2026)",
                                          value=False, key=f"{prefix}_iva_exento",
                                          help="Eliminacion temporal del IVA en viviendas nuevas")
            vacancia = st.slider("Vacancia (meses/ano sin arriendo)", 0, 6, 1,
                                  key=f"{prefix}_vacancia",
                                  help="Meses al ano que la propiedad estaria sin arrendatario")
            num_dfl2 = st.number_input("Propiedades DFL2 que ya tienes", value=0,
                                        min_value=0, max_value=10, key=f"{prefix}_num_dfl2",
                                        help="Beneficios DFL2 aplican solo a las 2 mas antiguas")

        # --- Arriendo ---
        with st.expander(f"Arriendo estimado - {nombre}"):
            arr_min, arr_prom, arr_max = estimar_arriendo(zona, metros)
            st.caption(f"Estimacion zona: {arr_min:.1f} - {arr_prom:.1f} - {arr_max:.1f} UF/mes")

            if st.button("Usar promedio zona", key=f"{prefix}_btn_arr"):
                st.session_state[f"{prefix}_arriendo"] = arr_prom

            arriendo = st.number_input("Arriendo mensual (UF)", value=arr_prom,
                                        min_value=0.0, max_value=500.0, step=0.5,
                                        key=f"{prefix}_arriendo")

        # --- Valor futuro ---
        with st.expander(f"Valor futuro - {nombre}"):
            tasa_aprec = st.number_input("Tasa apreciacion anual (%)", value=3.0,
                                          min_value=-10.0, max_value=30.0, step=0.5,
                                          key=f"{prefix}_aprec")

        inputs_escenarios.append({
            "nombre": nombre,
            "precio_uf": precio_uf,
            "metros": metros,
            "zona": zona,
            "contribuciones": contribuciones,
            "gastos_comunes": gastos_comunes,
            "banco": banco,
            "tasa": tasa,
            "plazo": plazo,
            "pie": pie,
            "sistema": sistema,
            "sub_dividendo": sub_dividendo,
            "bono_uf": bono_uf,
            "seg_desgravamen": seg_desgravamen,
            "seg_incendio": seg_incendio,
            "gastos": gastos,
            "arriendo": arriendo,
            "tasa_aprec": tasa_aprec,
            "es_nueva": es_nueva,
            "iva_exento": iva_exento,
            "vacancia": vacancia,
            "num_dfl2": num_dfl2,
        })

# =====================================================================
# Calculos
# =====================================================================
st.divider()

resumenes = []
nombres = []

for inp in inputs_escenarios:
    r = calcular_resumen_escenario(
        precio_uf=inp["precio_uf"],
        pie_pct=inp["pie"],
        bono_uf=inp["bono_uf"],
        tasa_anual=inp["tasa"],
        plazo_anos=inp["plazo"],
        sistema=inp["sistema"],
        seguro_desgravamen_pct=inp["seg_desgravamen"],
        seguro_incendio_uf=inp["seg_incendio"],
        gastos_escrituracion=inp["gastos"],
        arriendo_uf=inp["arriendo"],
        gastos_comunes_uf=inp["gastos_comunes"],
        contribuciones_trim_uf=inp["contribuciones"],
        tasa_apreciacion=inp["tasa_aprec"],
        valor_uf_clp=valor_uf,
        subsidio_dividendo=inp["sub_dividendo"],
        metros_cuadrados=inp["metros"],
        es_nueva=inp["es_nueva"],
        iva_exento=inp["iva_exento"],
        vacancia_meses=inp["vacancia"],
        num_propiedades_dfl2=inp["num_dfl2"],
        porcentaje_renta=porcentaje_renta,
    )
    if r:
        resumenes.append(r)
        nombres.append(inp["nombre"])

# =====================================================================
# Helpers de formato
# =====================================================================
def fmt(valor_uf_monto, decimales=0):
    """Formatea un monto en UF o pesos segun el toggle."""
    if mostrar_pesos:
        pesos = valor_uf_monto * valor_uf
        if abs(pesos) >= 1_000_000:
            return f"${pesos / 1_000_000:,.1f}M"
        return f"${pesos:,.0f}"
    if decimales == 0:
        return f"{valor_uf_monto:,.0f} UF"
    return f"{valor_uf_monto:,.{decimales}f} UF"


def fmt_full(valor_uf_monto):
    """Formato completo sin abreviar."""
    if mostrar_pesos:
        return f"${valor_uf_monto * valor_uf:,.0f}"
    return f"{valor_uf_monto:,.2f} UF"


def moneda():
    return "$" if mostrar_pesos else "UF"


def to_display(valor_uf_monto):
    """Convierte a valor numerico segun moneda seleccionada."""
    if mostrar_pesos:
        return valor_uf_monto * valor_uf
    return valor_uf_monto


# =====================================================================
# Resumen Comparativo
# =====================================================================
if resumenes:

    # =================================================================
    # RESUMEN SIMPLE - Lo que realmente importa
    # =================================================================
    st.header("Resumen Simple")
    st.caption("Lo esencial de cada escenario de un vistazo")

    simple_cols = st.columns(len(resumenes))
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        with simple_cols[i]:
            st.subheader(nombre)

            # Precio de la casa
            st.markdown(f"**Precio de la casa:** {fmt(r['precio_uf'])}")

            # Cuanto pedi prestado
            st.markdown(f"**Pedi prestado:** {fmt(r['monto_credito_uf'])}")

            # Dividendo mensual
            st.markdown(f"**Pago mensual (dividendo):** {fmt(r['dividendo_mes1_uf'], 2)}")

            st.divider()

            # Cuanto pague en total (pie + credito + gastos)
            st.markdown(f"### Total que pague: {fmt(r['costo_total_uf'])}")

            # Cuanto era la casa vs cuanto pague = cuanto pague de mas
            extra = r["costo_total_uf"] - r["precio_uf"]
            pct_extra = (extra / r["precio_uf"]) * 100 if r["precio_uf"] > 0 else 0
            st.markdown(f"**Pague de mas (intereses + gastos):** {fmt(extra)}"
                        f" ({pct_extra:.0f}% extra)")

            st.divider()

            # Cuanto vale la casa al final
            st.markdown(f"### La casa valdra: {fmt(r['valor_futuro_final_uf'])}")

            # Ganancia o perdida neta
            ganancia = r["ganancia_neta_uf"]
            if ganancia >= 0:
                st.success(f"Ganancia si vendo: {fmt(ganancia)}")
            else:
                st.error(f"Perdida si vendo: {fmt(ganancia)}")

            st.divider()

            # Renta minima
            st.markdown(f"**Renta minima requerida ({porcentaje_renta}%):** ${r['renta_minima_clp']:,.0f}/mes")

            # Arriendo vs dividendo
            diff_arr = r["arriendo_mensual_uf"] - r["dividendo_mes1_uf"]
            st.markdown(f"**Arriendo estimado:** {fmt(r['arriendo_mensual_uf'], 2)}/mes")
            if diff_arr >= 0:
                st.success(f"Arriendo cubre dividendo + {fmt(diff_arr, 2)}/mes")
            else:
                st.warning(f"Falta {fmt(abs(diff_arr), 2)}/mes para cubrir dividendo")

            # Gastos extra (timbres, corretaje, IVA)
            extras_list = []
            if r["imp_timbres_uf"] > 0:
                extras_list.append(f"Imp. timbres: {fmt(r['imp_timbres_uf'], 2)}")
            if r["corretaje_uf"] > 0:
                extras_list.append(f"Corretaje: {fmt(r['corretaje_uf'], 2)}")
            if r["iva_uf"] > 0:
                extras_list.append(f"IVA (19%): {fmt(r['iva_uf'])}")
            if extras_list:
                st.caption("Gastos adicionales: " + " | ".join(extras_list))

            # DFL2
            dfl2 = r["dfl2"]
            if dfl2["aplica_dfl2"]:
                st.info(f"DFL2: ahorro contrib. {fmt(dfl2['ahorro_contribuciones_anual'], 2)}/ano"
                        f" por {dfl2['anos_exencion_contrib']} anos"
                        f" | Timbres reducidos (0.2%)"
                        f" | Arriendo {'exento' if dfl2['arriendo_exento'] else 'NO exento'} de impuesto")

    # =================================================================
    # METRICAS DE INVERSION
    # =================================================================
    if perfil == "Inversionista":
        st.divider()
        st.header("Analisis de Inversion")
        st.caption(
            "⚠️ Las métricas de inversión (Cap Rate, ROI, Cash on Cash) son proyecciones basadas en supuestos configurables. "
            "Los resultados reales dependen del mercado, la vacancia real, los gastos imprevistos y la situación tributaria individual. "
            "No constituyen recomendación de inversión."
        )

        inv_cols = st.columns(len(resumenes))
        for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
            with inv_cols[i]:
                st.subheader(nombre)

                # Semaforo
                color = r["semaforo_color"]
                texto = r["semaforo_texto"]
                if color == "verde":
                    st.success(f"SEMAFORO: {texto}")
                elif color == "amarillo":
                    st.warning(f"SEMAFORO: {texto}")
                else:
                    st.error(f"SEMAFORO: {texto}")

                st.metric("Cap Rate Bruto", f"{r['cap_rate_bruto']}%",
                           help="Arriendo anual / Precio compra")
                st.metric("Cap Rate Neto", f"{r['cap_rate_neto']}%",
                           help="(Arriendo - gastos - vacancia) / Precio")
                st.metric("Cash on Cash", f"{r['cash_on_cash']}%",
                           help="Flujo neto anual / Capital invertido (pie + gastos)")
                st.metric("ROI (con plusvalia)", f"{r['roi']}%",
                           help="(Flujo neto + plusvalia anual) / Capital invertido")
                st.metric("Capital invertido", fmt(r['capital_invertido_uf']),
                           help="Pie + gastos iniciales")

                # Referencia
                st.caption("Referencia Cap Rate Chile: <4% bajo | 4-5.5% normal | >5.5% bueno")

    st.divider()

    # =================================================================
    # RESUMEN DETALLADO
    # =================================================================
    st.header("Resumen Detallado")

    met_cols = st.columns(len(resumenes))
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        with met_cols[i]:
            st.subheader(nombre)
            st.metric("Dividendo Mes 1", fmt(r['dividendo_mes1_uf'], 2))
            st.metric("Tasa Efectiva", f"{r['tasa_efectiva']}%")
            st.metric("CAE", f"{r['cae']}%")
            st.metric("Costo Total", fmt(r['costo_total_uf']))
            st.metric("Valor Futuro", fmt(r['valor_futuro_final_uf']))

            flujo_color = "normal" if r["flujo_neto_promedio_uf"] >= 0 else "inverse"
            st.metric("Flujo Neto Prom.", fmt(r['flujo_neto_promedio_uf'], 2) + "/mes",
                       delta=f"{'Positivo' if r['flujo_neto_promedio_uf'] >= 0 else 'Negativo'}",
                       delta_color=flujo_color)

    # Tabla resumen
    st.subheader("Tabla Comparativa Detallada")
    tabla_resumen = pd.DataFrame([
        {
            "Escenario": n,
            "Precio": fmt(r['precio_uf']),
            "Pie": f"{r['pie_pct']}% ({fmt(r['pie_monto_uf'])})",
            "Monto Credito": fmt(r['monto_credito_uf']),
            "Tasa Efectiva": f"{r['tasa_efectiva']}%",
            "Plazo": f"{r['plazo_anos']} anos",
            "Sistema": r['sistema'].capitalize(),
            "Dividendo Mes 1": fmt(r['dividendo_mes1_uf'], 2),
            "CAE": f"{r['cae']}%",
            "Total Intereses": fmt(r['total_intereses_uf']),
            "Costo Total": fmt(r['costo_total_uf']),
            "Pague de Mas": fmt(r['costo_total_uf'] - r['precio_uf']),
            "Valor Futuro": fmt(r['valor_futuro_final_uf']),
            "Ganancia Neta": fmt(r['ganancia_neta_uf']),
            "Arriendo/mes": fmt(r['arriendo_mensual_uf'], 2),
        }
        for r, n in zip(resumenes, nombres)
    ])
    st.dataframe(tabla_resumen, use_container_width=True, hide_index=True)

    # =====================================================================
    # Graficos
    # =====================================================================
    st.header("Graficos Comparativos")

    # Fila 1: Dividendo + Dividendo vs Arriendo
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_dividendo_comparado(resumenes, nombres), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_dividendo_vs_arriendo(resumenes, nombres), use_container_width=True)

    # Fila 2: Evolucion Saldo + Interes vs Capital
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(grafico_evolucion_saldo(resumenes, nombres), use_container_width=True)
    with col4:
        st.plotly_chart(grafico_interes_vs_capital(resumenes, nombres), use_container_width=True)

    # Fila 3: Costo Total + Flujo Caja Neto
    col5, col6 = st.columns(2)
    with col5:
        st.plotly_chart(grafico_costo_total(resumenes, nombres), use_container_width=True)
    with col6:
        st.plotly_chart(grafico_flujo_caja_neto(resumenes, nombres), use_container_width=True)

    # Fila 4: Valor Futuro + Ganancia Neta
    col7, col8 = st.columns(2)
    with col7:
        st.plotly_chart(grafico_valor_futuro(resumenes, nombres), use_container_width=True)
    with col8:
        st.plotly_chart(grafico_ganancia_neta(resumenes, nombres), use_container_width=True)

    # =====================================================================
    # Tablas de Amortizacion
    # =====================================================================
    st.header("Tablas de Amortizacion")

    for r, nombre in zip(resumenes, nombres):
        with st.expander(f"Tabla de Amortizacion - {nombre}"):
            tabla = r["tabla_amortizacion"]
            if tabla.empty:
                st.warning("No hay datos")
                continue

            # Vista resumen anual
            st.subheader("Resumen Anual")
            anual = tabla.groupby("ano").agg({
                "cuota_base": "sum",
                "interes": "sum",
                "capital": "sum",
                "seg_desgravamen": "sum",
                "seg_incendio": "sum",
                "cuota_total": "sum",
            }).reset_index()
            anual["saldo_final"] = tabla.groupby("ano")["saldo"].last().values
            anual.columns = ["Ano", "Cuota Total", "Interes", "Capital",
                            "Seg. Desgravamen", "Seg. Incendio", "Pago Total", "Saldo Final"]

            st.dataframe(
                anual.style.format({
                    "Cuota Total": "{:,.2f}",
                    "Interes": "{:,.2f}",
                    "Capital": "{:,.2f}",
                    "Seg. Desgravamen": "{:,.4f}",
                    "Seg. Incendio": "{:,.2f}",
                    "Pago Total": "{:,.2f}",
                    "Saldo Final": "{:,.2f}",
                }),
                use_container_width=True, hide_index=True,
            )

            # Vista detallada mensual
            with st.expander("Ver detalle mensual"):
                display_tabla = tabla.copy()
                display_tabla.columns = ["Mes", "Ano", "Cuota Base", "Interes", "Capital",
                                          "Saldo", "Seg. Desgravamen", "Seg. Incendio", "Cuota Total"]
                st.dataframe(
                    display_tabla.style.format({
                        "Cuota Base": "{:,.4f}",
                        "Interes": "{:,.4f}",
                        "Capital": "{:,.4f}",
                        "Saldo": "{:,.4f}",
                        "Seg. Desgravamen": "{:,.4f}",
                        "Seg. Incendio": "{:,.4f}",
                        "Cuota Total": "{:,.4f}",
                    }),
                    use_container_width=True, hide_index=True, height=400,
                )

    # =====================================================================
    # Exportacion
    # =====================================================================
    st.header("Exportar Resultados")
    col_pdf, col_excel = st.columns(2)

    with col_pdf:
        pdf_buffer = exportar_pdf(resumenes, nombres, valor_uf)
        st.download_button(
            "Descargar PDF",
            data=pdf_buffer,
            file_name="simulacion_casas.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col_excel:
        excel_buffer = exportar_excel(resumenes, nombres, valor_uf)
        st.download_button(
            "Descargar Excel",
            data=excel_buffer,
            file_name="simulacion_casas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

else:
    st.warning("No se pudieron calcular los escenarios. Verifique los datos ingresados.")

# =====================================================================
# Footer
# =====================================================================
st.divider()
st.caption(
    "⚠️ Los cálculos son estimaciones referenciales y no constituyen asesoría financiera, legal ni tributaria. "
    "Tasas referenciales marzo 2026 (fuente: neatpagos.com). "
    "Consulta siempre con un profesional certificado antes de tomar decisiones financieras."
)
