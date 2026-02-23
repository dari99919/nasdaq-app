import streamlit as st
import pandas as pd
import os
import engine

st.set_page_config(page_title="Asesor Markowitz", layout="wide")
st.title("📈 Optimizador de Cartera por Preferencias")

EXCEL_FILE = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"

# Buscador intuitivo
consulta = st.text_input("¿Qué tipo de cartera buscas?", placeholder="Ej: Tecnología con dividendos")

if consulta:
    if not os.path.exists(EXCEL_FILE):
        st.error("El archivo de datos no existe. Debes ejecutar el extractor primero.")
    else:
        # Cargar metadatos para filtrar
        df_sectores = pd.read_excel(EXCEL_FILE, sheet_name='06_Sectores', index_col=0)
        df_yield = pd.read_excel(EXCEL_FILE, sheet_name='07_Yield', index_col=0)
        
        candidatos = df_sectores.index.tolist()

        # 1. Filtro por Sector
        if any(palabra in consulta.lower() for palabra in ["tech", "tecnología", "tecnológico"]):
            candidatos = df_sectores[df_sectores['Sector'] == 'Technology'].index.tolist()
        
        # 2. Filtro por Dividendos
        if "dividendo" in consulta.lower():
            # Quedarse solo con los que tienen Yield > 0
            candidatos = [t for t in candidatos if df_yield.loc[t, 'Yield_2024_%'] > 0]

        if len(candidatos) > 1:
            st.success(f"Analizando la combinación óptima de {len(candidatos)} activos encontrados.")
            
            if st.button("🚀 Calcular Cartera Óptima"):
                with st.spinner("Buscando el máximo Ratio de Sharpe..."):
                    fig, pesos, error = engine.optimizar_max_sharpe(candidatos)
                    
                    if error:
                        st.error(error)
                    else:
                        st.pyplot(fig)
                        st.subheader("Distribución de Capital Recomendada:")
                        # Mostrar solo los que tengan más de un 1% de peso
                        recomendados = pesos[pesos > 0.01].sort_values(ascending=False)
                        st.table(recomendados.apply(lambda x: "{:.2%}".format(x)))
        else:
            st.warning("No hay suficientes activos (mínimo 2) para optimizar con esos filtros.")
