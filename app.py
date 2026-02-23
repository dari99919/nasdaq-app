import streamlit as st
import pandas as pd
import engine

st.title("🧠 Buscador Financiero Inteligente (Markowitz)")

# Cargamos todas las dimensiones del Excel
@st.cache_data
def cargar_unificado():
    file = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"
    # Unimos sectores, fundamentales y yield en un solo gran DataFrame
    df_sec = pd.read_excel(file, sheet_name='06_Sectores', index_col=0)
    df_yield = pd.read_excel(file, sheet_name='07_Yield', index_col=0)
    df_stats = pd.read_excel(file, sheet_name='03_Stats', index_col=0)
    return pd.concat([df_sec, df_yield, df_stats], axis=1)

try:
    df = cargar_unificado()
    
    # --- INTERFAZ DE FILTRADO ---
    st.sidebar.header("Filtros Avanzados")
    
    # Filtro por Sector
    sectores_libres = ["Todos"] + list(df['Sector'].unique())
    sector_sel = st.sidebar.selectbox("Sector", sectores_libres)
    
    # Filtro por Dividendos
    solo_div = st.sidebar.checkbox("Solo empresas con dividendos")
    
    # Filtros de Ratios (Valoración y Fundamentales)
    per_max = st.sidebar.slider("PER Máximo", 0, 100, 100)
    min_sharpe = st.sidebar.slider("Sharpe Mínimo", 0.0, 3.0, 0.0)

    # --- APLICACIÓN DE LOS FILTROS ---
    mask = (df['PER'] <= per_max) & (df['Sharpe_Ratio'] >= min_sharpe)
    
    if sector_sel != "Todos":
        mask = mask & (df['Sector'] == sector_sel)
    
    if solo_div:
        mask = mask & (df['Yield_2024_%'] > 0)
    
    activos_finales = df[mask].index.tolist()

    # --- EJECUCIÓN DEL MODELO ---
    st.write(f"Empresas que cumplen el criterio: **{len(activos_finales)}**")
    st.dataframe(df[mask][['Sector', 'PER', 'Yield_2024_%', 'Sharpe_Ratio']])

    if len(activos_finales) >= 2:
        if st.button("🚀 Calcular Cartera Óptima con estos filtros"):
            fig, pesos, error = engine.optimizar_max_sharpe(activos_finales)
            if not error:
                st.pyplot(fig)
                st.subheader("Composición Ideal:")
                st.table(pesos[pesos > 0.01].map(lambda x: f"{x:.2%}"))
    else:
        st.warning("Necesitas al menos 2 activos para el modelo de Markowitz.")

except Exception as e:
    st.error("Primero ejecuta el Extractor para generar los datos.")
