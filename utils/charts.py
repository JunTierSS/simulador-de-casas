"""
Graficos Plotly para el simulador de casas.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Paleta de colores para escenarios
COLORES = px.colors.qualitative.Set2


def _color(idx):
    return COLORES[idx % len(COLORES)]


def grafico_dividendo_comparado(resumenes, nombres):
    """Barras agrupadas: dividendo mes 1 por escenario (UF y CLP)."""
    fig = go.Figure()
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        fig.add_trace(go.Bar(
            name=nombre,
            x=[nombre],
            y=[r["dividendo_mes1_uf"]],
            marker_color=_color(i),
            text=[f'{r["dividendo_mes1_uf"]:.2f} UF'],
            textposition="auto",
        ))
    fig.update_layout(
        title="Dividendo Mensual (Mes 1)",
        yaxis_title="UF/mes",
        showlegend=True,
        barmode="group",
    )
    return fig


def grafico_evolucion_saldo(resumenes, nombres):
    """Lineas: evolucion del saldo de deuda por escenario."""
    fig = go.Figure()
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        tabla = r["tabla_amortizacion"]
        if tabla.empty:
            continue
        fig.add_trace(go.Scatter(
            x=tabla["mes"],
            y=tabla["saldo"],
            mode="lines",
            name=nombre,
            line=dict(color=_color(i), width=2),
        ))
    fig.update_layout(
        title="Evolucion del Saldo de Deuda",
        xaxis_title="Mes",
        yaxis_title="Saldo (UF)",
    )
    return fig


def grafico_interes_vs_capital(resumenes, nombres):
    """Area apilada: desglose interes vs capital acumulado por escenario."""
    fig = go.Figure()
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        tabla = r["tabla_amortizacion"]
        if tabla.empty:
            continue
        # Agrupar por ano
        anual = tabla.groupby("ano").agg({"interes": "sum", "capital": "sum"}).reset_index()
        fig.add_trace(go.Bar(
            name=f"{nombre} - Interes",
            x=anual["ano"],
            y=anual["interes"],
            marker_color=_color(i),
            opacity=0.6,
        ))
        fig.add_trace(go.Bar(
            name=f"{nombre} - Capital",
            x=anual["ano"],
            y=anual["capital"],
            marker_color=_color(i),
            opacity=1.0,
        ))
    fig.update_layout(
        title="Desglose Anual: Interes vs Capital",
        xaxis_title="Ano",
        yaxis_title="UF",
        barmode="stack",
    )
    return fig


def grafico_costo_total(resumenes, nombres):
    """Barras apiladas: desglose del costo total por escenario."""
    fig = go.Figure()

    pies = [r["pie_monto_uf"] for r in resumenes]
    intereses = [r["total_intereses_uf"] for r in resumenes]
    seguros = [r["total_seguros_uf"] for r in resumenes]
    gastos = [r["gastos_iniciales_uf"] for r in resumenes]

    fig.add_trace(go.Bar(name="Pie", x=nombres, y=pies, marker_color="#2196F3"))
    fig.add_trace(go.Bar(name="Intereses", x=nombres, y=intereses, marker_color="#FF5722"))
    fig.add_trace(go.Bar(name="Seguros", x=nombres, y=seguros, marker_color="#FFC107"))
    fig.add_trace(go.Bar(name="Gastos Iniciales", x=nombres, y=gastos, marker_color="#9C27B0"))

    fig.update_layout(
        title="Desglose del Costo Total del Credito",
        yaxis_title="UF",
        barmode="stack",
    )
    return fig


def grafico_flujo_caja_neto(resumenes, nombres):
    """Lineas: flujo de caja neto (arriendo - dividendo - gastos) mensual."""
    fig = go.Figure()

    # Linea de referencia en 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        flujo = r["flujo_arriendo"]
        if flujo.empty:
            continue
        # Agrupar por ano para suavizar
        anual = flujo.groupby("ano").agg({"flujo_neto": "mean"}).reset_index()
        fig.add_trace(go.Scatter(
            x=anual["ano"],
            y=anual["flujo_neto"],
            mode="lines+markers",
            name=nombre,
            line=dict(color=_color(i), width=2),
        ))

    fig.update_layout(
        title="Flujo de Caja Neto (Arriendo - Dividendo - Gastos)",
        xaxis_title="Ano",
        yaxis_title="UF/mes (promedio anual)",
    )
    return fig


def grafico_valor_futuro(resumenes, nombres):
    """Lineas: proyeccion valor futuro de la propiedad."""
    fig = go.Figure()
    for i, (r, nombre) in enumerate(zip(resumenes, nombres)):
        vf = r["valor_futuro_serie"]
        if not vf:
            continue
        df_vf = pd.DataFrame(vf)
        fig.add_trace(go.Scatter(
            x=df_vf["ano"],
            y=df_vf["valor_futuro_uf"],
            mode="lines+markers",
            name=nombre,
            line=dict(color=_color(i), width=2),
        ))
    fig.update_layout(
        title="Valor Futuro de la Propiedad",
        xaxis_title="Ano",
        yaxis_title="Valor (UF)",
    )
    return fig


def grafico_ganancia_neta(resumenes, nombres):
    """Barras: ganancia neta si vende al final del plazo."""
    fig = go.Figure()
    ganancias = [r["ganancia_neta_uf"] for r in resumenes]
    colores = ["#4CAF50" if g >= 0 else "#F44336" for g in ganancias]

    fig.add_trace(go.Bar(
        x=nombres,
        y=ganancias,
        marker_color=colores,
        text=[f'{g:,.0f} UF' for g in ganancias],
        textposition="auto",
    ))
    fig.update_layout(
        title="Ganancia Neta al Vender (Valor Futuro - Costo Total)",
        yaxis_title="UF",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig


def grafico_dividendo_vs_arriendo(resumenes, nombres):
    """Barras agrupadas: dividendo mensual vs arriendo estimado."""
    fig = go.Figure()

    dividendos = [r["dividendo_mes1_uf"] for r in resumenes]
    arriendos = [r["arriendo_mensual_uf"] for r in resumenes]

    fig.add_trace(go.Bar(
        name="Dividendo",
        x=nombres,
        y=dividendos,
        marker_color="#2196F3",
    ))
    fig.add_trace(go.Bar(
        name="Arriendo Estimado",
        x=nombres,
        y=arriendos,
        marker_color="#4CAF50",
    ))

    fig.update_layout(
        title="Dividendo vs Arriendo Estimado",
        yaxis_title="UF/mes",
        barmode="group",
    )
    return fig
