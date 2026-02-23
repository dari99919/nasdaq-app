import streamlit as st
import pandas as pd
import engine
import os
from nlp_logic import brain, config, nlp  # Importamos tu Cerebro Semántico

st.title("🤖 Asesor Financiero Inteligente")

# 1. Carga de datos unificada
@st.cache_data
def cargar_unificado():
    file = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"
    if not os.path.exists(file):
        return None
    df_sec = pd.read_excel(file, sheet_name='06_Sectores', index_col=0)
    df_yield = pd.read_excel(file, sheet_name='07_Yield', index_col=0)
    df_stats = pd.read_excel(file, sheet_name='03_Stats', index_col=0)
    return pd.concat([df_sec, df_yield, df_stats], axis=1)

df = cargar_unificado()

if df is not None:
    # --- BLOQUE DE IA (Buscador Natural) ---
    st.markdown("### 💬 ¿Qué cartera tienes en mente?")
    consulta = st.text_input("Ejemplo: 'Quiero tecnología barata con dividendos'", key="nlp_search")
    
    # Variables de control para la IA
    sector_ia = None
    solo_div_ia = False
    orden_ia = "Sharpe_Ratio" # Por defecto ordenamos por eficiencia

    if consulta:
        doc = nlp(config.normalizar(consulta))
        for token in doc:
            # Detectar Sector por similitud semántica
            s = brain.buscar_por_similitud(token.text, brain.sectores)
            if s: sector_ia = s
            # Detectar Dividendos
            if brain.buscar_por_similitud(token.text, brain.dividendos): solo_div_ia = True
            # Detectar si quiere "Barato" (PER bajo)
            if token.text in brain.keys_min: orden_ia = "PER"

    # --- BLOQUE DE FILTROS (Barra Lateral) ---
    st.sidebar.header("🎯 Ajuste Manual")
    sectores_libres = ["Cualquiera"] + list(df['Sector'].unique())
    
    # El sector se selecciona automáticamente si la IA lo detecta
    index_sector = sectores_libres.index(sector_ia) if sector_ia in sectores_libres else 0
    sector_sel = st.sidebar.selectbox("Sector", sectores_libres, index=index_sector)
    
    # Los dividendos se marcan si la IA lo detecta
    solo_div = st.sidebar.checkbox("Solo con dividendos", value=solo_div_ia)
    
    per_max = st.sidebar.slider("PER Máximo", 0, 100, 100)
    min_sharpe = st.sidebar.slider("Sharpe Mínimo", 0.0, 3.0, 0.0)

    # --- APLICACIÓN DE FILTROS COMBINADOS ---
    mask = (df['PER'] <= per_max) & (df['Sharpe_Ratio'] >= min_sharpe)
    
    if sector_sel != "Cualquiera":
        mask = mask & (df['Sector'] == sector_sel)
    if solo_div:
        mask = mask & (df['Yield_2024_%'] > 0)
    
    df_filtrado = df[mask].sort_values(by=orden_ia, ascending=(orden_ia == "PER"))
    activos_finales = df_filtrado.index.tolist()

    # --- RESULTADOS Y MODELO ---
    st.write(f"✅ **{len(activos_finales)}** activos cumplen tus criterios.")
    st.dataframe(df_filtrado[['Sector', 'PER', 'Yield_2024_%', 'Sharpe_Ratio']].head(15))

    if len(activos_finales) >= 2:
        if st.button("🚀 Calcular Cartera Óptima de Markowitz"):
            with st.spinner("Ejecutando optimización matemática..."):
                fig, pesos, error = engine.optimizar_max_sharpe(activos_finales)
                if not error:
                    st.pyplot(fig)
                    st.subheader("📊 Composición Sugerida:")
                    st.table(pesos[pesos > 0.01].map(lambda x: f"{x:.2%}"))
    else:
        st.warning("Selecciona al menos 2 activos para activar el modelo.")

else:
    st.error("⚠️ No se han encontrado datos. Por favor, ejecuta el Extractor primero.")
