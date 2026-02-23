import streamlit as st
import pandas as pd
import engine
import os
from nlp_logic import brain, config, nlp
from extractor import ejecutar_extraccion  # Importamos tu script extractor

# --- CONFIGURACIÓN INICIAL ---
EXCEL_FILE = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"

st.set_page_config(page_title="Asesor Markowitz IA", layout="wide")
st.title("🤖 Asesor Financiero Inteligente")

# --- LÓGICA DE EXTRACCIÓN ÚNICA ---
# Si el archivo no existe, lo extraemos una sola vez al arrancar la app
if not os.path.exists(EXCEL_FILE):
    with st.status("🚀 Configurando base de datos por primera vez...", expanded=True) as status:
        st.write("Descargando datos del Nasdaq desde Yahoo Finance...")
        ejecutar_extraccion(EXCEL_FILE)
        st.write("Calculando matrices de covarianza y métricas...")
        status.update(label="✅ Base de datos lista para usar", state="complete", expanded=False)

# --- CARGA DE DATOS CON CACHÉ ---
@st.cache_data
def cargar_unificado():
    if not os.path.exists(EXCEL_FILE):
        return None
    # Cargamos las pestañas clave del Excel
    df_sec = pd.read_excel(EXCEL_FILE, sheet_name='06_Sectores', index_col=0)
    df_yield = pd.read_excel(EXCEL_FILE, sheet_name='07_Yield', index_col=0)
    df_stats = pd.read_excel(EXCEL_FILE, sheet_name='03_Stats', index_col=0)
    return pd.concat([df_sec, df_yield, df_stats], axis=1)

df = cargar_unificado()

if df is not None:
    # --- BLOQUE DE IA (Buscador Natural) ---
    st.markdown("### 💬 ¿Qué cartera tienes en mente?")
    consulta = st.text_input("Ejemplo: 'Tecnología barata con dividendos'", key="nlp_search")
    
    sector_ia = None
    solo_div_ia = False
    orden_ia = "Sharpe_Ratio"

    if consulta:
        doc = nlp(config.normalizar(consulta))
        for token in doc:
            # IA detecta sector
            s = brain.buscar_por_similitud(token.text, brain.sectores)
            if s: sector_ia = s
            # IA detecta dividendos
            if brain.buscar_por_similitud(token.text, brain.dividendos): solo_div_ia = True
            # IA detecta si quieres PER bajo
            if token.text in brain.keys_min: orden_ia = "PER"

    # --- BLOQUE DE FILTROS (Barra Lateral) ---
    st.sidebar.header("🎯 Ajuste Manual")
    
    # Sincronizamos la IA con la barra lateral
    sectores_libres = ["Cualquiera"] + list(df['Sector'].unique())
    index_sector = sectores_libres.index(sector_ia) if sector_ia in sectores_libres else 0
    sector_sel = st.sidebar.selectbox("Sector", sectores_libres, index=index_sector)
    
    solo_div = st.sidebar.checkbox("Solo con dividendos", value=solo_div_ia)
    per_max = st.sidebar.slider("PER Máximo", 0, 100, 100)
    min_sharpe = st.sidebar.slider("Sharpe Mínimo", 0.0, 3.0, 0.0)

    # Botón para forzar actualización si el usuario lo desea
    if st.sidebar.button("🔄 Forzar actualización de datos"):
        if os.path.exists(EXCEL_FILE):
            os.remove(EXCEL_FILE)
        st.cache_data.clear()
        st.rerun()

    # --- FILTRADO Y MODELO ---
    mask = (df['PER'] <= per_max) & (df['Sharpe_Ratio'] >= min_sharpe)
    if sector_sel != "Cualquiera":
        mask = mask & (df['Sector'] == sector_sel)
    if solo_div:
        mask = mask & (df['Yield_2024_%'] > 0)
    
    df_filtrado = df[mask].sort_values(by=orden_ia, ascending=(orden_ia == "PER"))
    activos_finales = df_filtrado.index.tolist()

    st.write(f"✅ **{len(activos_finales)}** activos seleccionados.")
    st.dataframe(df_filtrado[['Sector', 'PER', 'Yield_2024_%', 'Sharpe_Ratio']].head(10))

    if len(activos_finales) >= 2:
        if st.button("🚀 Calcular Cartera Óptima (Markowitz)"):
            with st.spinner("Optimizando pesos..."):
                fig, pesos, error = engine.optimizar_max_sharpe(activos_finales)
                if not error:
                    st.pyplot(fig)
                    st.subheader("📊 Distribución recomendada:")
                    st.table(pesos[pesos > 0.01].map(lambda x: f"{x:.2%}"))
    else:
        st.warning("Selecciona al menos 2 activos para el modelo.")
else:
    st.error("Error crítico: No se ha podido generar ni cargar la base de datos.")
