import streamlit as st
import pandas as pd
import os
from extractor import ejecutar_extraccion # Importamos tu función del extractor

# 1. Configuración de la página
st.set_page_config(page_title="Nasdaq Markowitz Analyzer", page_icon="📈", layout="wide")

# Nombre del archivo que genera tu extractor (en la raíz)
EXCEL_FILE = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"

# 2. Sidebar: Control de Datos
st.sidebar.title("⚙️ Configuración")
if st.sidebar.button("🔄 Actualizar Datos (Yahoo Finance)"):
    with st.spinner("Descargando precios y calculando métricas..."):
        ejecutar_extraccion(EXCEL_FILE)
        st.sidebar.success("¡Datos actualizados!")
        st.cache_data.clear() # Limpia la memoria para leer el nuevo Excel

# 3. Cuerpo principal
st.title("🔍 Buscador de Activos & Métricas")
st.markdown("Busca información fundamental y técnica de las empresas del Nasdaq procesadas.")

# Función para cargar los datos del Excel
@st.cache_data
def load_data(sheet):
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE, sheet_name=sheet, index_col=0)
    return None

# Cargamos las pestañas necesarias
df_stats = load_data('03_Stats')
df_sectores = load_data('06_Sectores')

# 4. Buscador funcional
termino = st.text_input("Introduce el Ticker o Sector:", placeholder="Ej: AAPL, NVDA, Technology...")

if termino:
    if df_stats is not None and df_sectores is not None:
        # Combinamos stats y sectores para la búsqueda
        df_completo = pd.concat([df_sectores, df_stats], axis=1)
        
        # Filtramos por Ticker (índice) o por Sector
        busqueda = termino.upper()
        mask = (df_completo.index.str.contains(busqueda)) | \
               (df_completo['Sector'].str.upper().contains(busqueda))
        
        resultados = df_completo[mask]

        if not resultados.empty:
            st.subheader(f"Resultados para: {termino}")
            
            # Si solo hay un resultado, mostramos "Fichas" de métricas
            if len(resultados) == 1:
                ticker = resultados.index[0]
                row = resultados.iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Retorno Esperado", f"{row['Retorno_Esperado']:.2%}")
                col2.metric("Volatilidad", f"{row['Volatilidad']:.2%}")
                col3.metric("Sharpe Ratio", f"{row['Sharpe_Ratio']:.2f}")
                col4.metric("PER", f"{row['PER']:.2f}")
                
                st.write(f"**Industria:** {row.get('Industria', 'N/A')}")
            
            # Mostramos la tabla general de los encontrados
            st.dataframe(resultados.style.highlight_max(axis=0, subset=['Sharpe_Ratio'], color='#90ee90'))
            st.balloons()
        else:
            st.warning("No se encontraron coincidencias en el Excel local.")
    else:
        st.error("⚠️ El archivo Excel no existe. Pulsa 'Actualizar Datos' en la barra lateral.")

else:
    st.info("Escribe un ticker para ver sus métricas de riesgo y retorno.")
    if df_stats is not None:
        st.write("### Top 5 Activos por Sharpe Ratio (Actual)")
        st.table(df_stats.head(5))
