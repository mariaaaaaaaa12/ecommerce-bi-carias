import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce — Análisis de Ventas",
    page_icon="🛒",
    layout="wide"
)

# ── Conexión ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="svrmonitoralertas.mysql.database.azure.com",
        user="usr_umg_demo",
        password="Umg.2026",
        database="db_umg_demo",
        ssl_ca=None,
        ssl_disabled=True
    )

@st.cache_data(ttl=300)
def run_query(sql):
    conn = get_connection()
    return pd.read_sql(sql, conn)

TABLE = "db_umg_demo.amazon_ecommerce_1m_CARIAS"

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🛒 Dashboard E-Commerce — Análisis de Ventas")
st.caption("Caso BI · DULCE MARIA CARIAS · UMG 2026")
st.divider()

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.subheader("📊 Resumen General")

kpi_sql = f"""
    SELECT
        COUNT(*)                          AS total_pedidos,
        ROUND(SUM(final_price), 2)        AS ingresos_totales,
        ROUND(AVG(rating), 2)             AS calificacion_promedio,
        ROUND(AVG(is_returned) * 100, 2)  AS tasa_devolucion
    FROM {TABLE}
"""
kpi = run_query(kpi_sql).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pedidos",        f"{int(kpi['total_pedidos']):,}")
c2.metric("Ingresos Totales",     f"${float(kpi['ingresos_totales']):,.0f}")
c3.metric("Calificación Promedio",f"{float(kpi['calificacion_promedio']):.2f} ⭐")
c4.metric("Tasa de Devolución",   f"{float(kpi['tasa_devolucion']):.2f}%")

st.divider()

# ── 1. Ingresos por Categoría ────────────────────────────────────────────────
st.subheader("💰 ¿Qué categorías generan más ingresos?")

cat_sql = f"""
    SELECT category,
           ROUND(SUM(final_price), 2) AS ingresos_totales
    FROM {TABLE}
    GROUP BY category
    ORDER BY ingresos_totales DESC
"""
df_cat = run_query(cat_sql)
fig1 = px.bar(df_cat, x="category", y="ingresos_totales",
              color="category", text_auto=".2s",
              labels={"category": "Categoría", "ingresos_totales": "Ingresos ($)"},
              title="Ingresos Totales por Categoría")
st.plotly_chart(fig1, use_container_width=True)
st.caption("💡 Electronics y Home lideran los ingresos totales.")

st.divider()

# ── 2. Factores de devoluciones ──────────────────────────────────────────────
st.subheader("📦 ¿Qué factores influyen en las devoluciones?")

col1, col2 = st.columns(2)

with col1:
    dev_cat_sql = f"""
        SELECT category,
               ROUND(AVG(is_returned)*100, 2) AS tasa_devolucion
        FROM {TABLE}
        GROUP BY category
        ORDER BY tasa_devolucion DESC
    """
    df_dev = run_query(dev_cat_sql)
    fig2 = px.bar(df_dev, x="tasa_devolucion", y="category",
                  orientation="h", color="tasa_devolucion",
                  color_continuous_scale="Reds",
                  labels={"category": "Categoría", "tasa_devolucion": "Tasa (%)"},
                  title="Tasa de Devolución por Categoría")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    dev_rating_sql = f"""
        SELECT ROUND(rating) AS rating_redondeado,
               ROUND(AVG(is_returned)*100, 2) AS tasa_devolucion
        FROM {TABLE}
        GROUP BY rating_redondeado
        ORDER BY rating_redondeado
    """
    df_dev_r = run_query(dev_rating_sql)
    fig3 = px.line(df_dev_r, x="rating_redondeado", y="tasa_devolucion",
                   markers=True,
                   labels={"rating_redondeado": "Calificación", "tasa_devolucion": "Tasa Devolución (%)"},
                   title="Devoluciones según Calificación del Producto")
    st.plotly_chart(fig3, use_container_width=True)

st.caption("💡 Productos con menor calificación tienen mayor tasa de devolución.")
st.divider()

# ── 3. Impacto de Descuentos ─────────────────────────────────────────────────
st.subheader("🏷️ ¿Los descuentos impactan positivamente las ventas?")

desc_sql = f"""
    SELECT
        CASE
            WHEN discount BETWEEN 1  AND 10 THEN '1%–10%'
            WHEN discount BETWEEN 11 AND 25 THEN '11%–25%'
            WHEN discount BETWEEN 26 AND 50 THEN '26%–50%'
            ELSE 'Más de 50%'
        END AS rango_descuento,
        ROUND(SUM(final_price), 2) AS ingresos_totales,
        COUNT(*)                   AS total_ventas
    FROM {TABLE}
    GROUP BY rango_descuento
    ORDER BY ingresos_totales DESC
"""
df_desc = run_query(desc_sql)
fig4 = px.bar(df_desc, x="ingresos_totales", y="rango_descuento",
              orientation="h", color="rango_descuento", text_auto=".2s",
              labels={"rango_descuento": "Rango de Descuento", "ingresos_totales": "Ingresos ($)"},
              title="Ingresos Totales por Rango de Descuento")
st.plotly_chart(fig4, use_container_width=True)
st.caption("💡 Los descuentos del 11%–25% generan el mayor volumen de ingresos.")
st.divider()

# ── 4. Tiempo de Envío vs Satisfacción ───────────────────────────────────────
st.subheader("🚚 ¿Cómo afecta el tiempo de envío a la satisfacción?")

ship_sql = f"""
    SELECT shipping_time_days,
           ROUND(AVG(rating), 3) AS calificacion_promedio,
           COUNT(*)              AS total_pedidos
    FROM {TABLE}
    GROUP BY shipping_time_days
    ORDER BY shipping_time_days
"""
df_ship = run_query(ship_sql)
fig5 = px.scatter(df_ship, x="shipping_time_days", y="calificacion_promedio",
                  size="total_pedidos", trendline="ols",
                  labels={"shipping_time_days": "Días de Envío",
                          "calificacion_promedio": "Calificación Promedio"},
                  title="Tiempo de Envío vs Satisfacción del Cliente")
st.plotly_chart(fig5, use_container_width=True)
st.caption("💡 A mayor tiempo de envío, la satisfacción tiende a disminuir.")
st.divider()

# ── 5. Desempeño de Vendedores ───────────────────────────────────────────────
st.subheader("🏆 ¿Qué vendedores tienen mejor desempeño?")

top_n = st.slider("Número de vendedores a mostrar", 5, 20, 10)

seller_sql = f"""
    SELECT seller_id,
           ROUND(SUM(final_price), 2)       AS ingresos_generados,
           ROUND(AVG(seller_rating), 2)     AS calificacion_vendedor,
           ROUND(AVG(is_returned)*100, 2)   AS tasa_devolucion,
           COUNT(*)                         AS total_ventas
    FROM {TABLE}
    GROUP BY seller_id
    ORDER BY ingresos_generados DESC
    LIMIT {top_n}
"""
df_sell = run_query(seller_sql)
fig6 = px.bar(df_sell, x="seller_id", y="ingresos_generados",
              color="calificacion_vendedor", text_auto=".2s",
              color_continuous_scale="Blues",
              labels={"seller_id": "Vendedor", "ingresos_generados": "Ingresos ($)",
                      "calificacion_vendedor": "Calificación"},
              title=f"Top {top_n} Vendedores por Ingresos")
st.plotly_chart(fig6, use_container_width=True)

st.dataframe(df_sell.rename(columns={
    "seller_id": "Vendedor",
    "ingresos_generados": "Ingresos ($)",
    "calificacion_vendedor": "Calificación",
    "tasa_devolucion": "Tasa Devolución (%)",
    "total_ventas": "Total Ventas"
}), use_container_width=True)

st.divider()
st.caption("🎓 Caso BI · UMG 2026 · DULCE MARIA CARIAS BRAN")
