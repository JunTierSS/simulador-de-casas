# 🏠 Simulador de Precios de Casas — Chile

Dashboard interactivo en Streamlit para simular y comparar escenarios de financiamiento hipotecario en Chile. Pensado tanto para compradores de primera vivienda como para inversionistas inmobiliarios.

> ⚠️ **AVISO IMPORTANTE:** Este simulador es una herramienta educativa e informativa. Los cálculos son estimaciones referenciales y **no constituyen asesoría financiera, legal ni tributaria**. Siempre consulta con un profesional certificado antes de tomar decisiones de inversión o endeudamiento.

---

## Características

- **Comparación de múltiples escenarios** side-by-side
- **11 bancos chilenos** con tasas referenciales de marzo 2026 (Itaú, Falabella, BancoEstado, Coopeuch, Scotiabank, BCI, Consorcio, BICE, Security, Chile, Santander)
- **Sistemas de amortización**: Francés (cuota fija) y Alemán (cuota decreciente)
- **Subsidios**: DS1 (3 tramos), FOGAES, Subsidio al Dividendo 2025–2027
- **Impuestos y gastos**: Impuesto de timbres, IVA en viviendas nuevas, corretaje, gastos de escrituración
- **Beneficios DFL2**: exención de contribuciones, timbres reducidos, arriendo exento de impuesto renta
- **Métricas de inversión**: Cap Rate bruto/neto, Cash on Cash Return, ROI con plusvalía, semáforo de rentabilidad
- **Calculadora inversa**: "¿cuánta casa me alcanza?" dado tu ingreso
- **Valor futuro** con tasa de apreciación configurable
- **Flujo de arriendo neto** con vacancia y reajuste anual
- **Toggle UF / Pesos** en tiempo real
- **Exportación** a PDF y Excel
- **Guardar/cargar simulaciones** en JSON

## Screenshots

> Corriendo en `localhost:8503`

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/JunTierSS/simulador-de-casas.git
cd simulador-de-casas

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

## Dependencias

| Librería | Uso |
|----------|-----|
| streamlit | Framework del dashboard |
| plotly | Gráficos interactivos |
| pandas | Manejo de datos |
| numpy | Cálculos numéricos |
| fpdf2 | Exportación PDF |
| openpyxl | Exportación Excel |
| scipy | Cálculo CAE (brentq) |

## Estructura del Proyecto

```
simulador-de-casas/
├── app.py                  # App principal Streamlit
├── requirements.txt        # Dependencias Python
└── utils/
    ├── calculations.py     # Fórmulas financieras (dividendo, CAE, valor futuro...)
    ├── banks.py            # Datos de bancos, zonas de arriendo, subsidios
    ├── charts.py           # Gráficos Plotly (8 gráficos)
    └── export.py           # Exportación PDF y Excel
```

## Fórmulas Clave

**Dividendo Francés (cuota fija)**
```
M = P × [r(1+r)^n] / [(1+r)^n − 1]
```

**Dividendo Alemán (cuota decreciente)**
```
Amortización = P / n  (constante)
Interés_k = Saldo_k × r
Cuota_k = Amortización + Interés_k
```

**CAE** — resuelto numéricamente igualando el valor presente de los flujos al monto del crédito (scipy.optimize.brentq).

**Cap Rate Neto**
```
Cap Rate Neto = (Arriendo anual − Gastos − Vacancia) / Precio compra × 100
```

**Cash on Cash Return**
```
CoC = Flujo neto anual / Capital invertido (pie + gastos iniciales) × 100
```

## Tasas de Referencia (marzo 2026)

Fuente: [neatpagos.com](https://neatpagos.com)

| Banco | Tasa Fija | Pie Mínimo |
|-------|-----------|-----------|
| Banco Itaú | 3.39% | 20% |
| Banco Falabella | 3.70% | 20% |
| BancoEstado | 4.19% | 10%* |
| Coopeuch | 4.50% | 20% |
| Scotiabank | 5.07% | 20% |
| Banco BCI | 5.41% | 20% |
| Banco Consorcio | 5.40% | 20% |
| BICE Hipotecaria | 5.50% | 20% |
| Security | 5.50% | 20% |
| Banco de Chile | 5.89% | 20% |
| Banco Santander | 5.99% | 20% |

*BancoEstado: 10% pie con FOGAES para viviendas hasta 4.500 UF.

> Las tasas son referenciales y cambian constantemente. Consulta directamente con el banco antes de tomar decisiones.

## Disclaimer

Este proyecto es de uso educativo. Los cálculos presentados son **estimaciones** basadas en fórmulas estándar de amortización hipotecaria y no reemplazan la evaluación crediticia real de ninguna institución financiera. El autor no se hace responsable por decisiones tomadas en base a los resultados de esta herramienta.

**No es asesoría financiera.**

## Licencia

MIT
