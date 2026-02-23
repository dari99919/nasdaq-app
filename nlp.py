import streamlit as st
import pandas as pd
import engine
# Importamos tus clases de lógica (puedes ponerlas en un archivo llamado nlp_logic.py)
from nlp_logic import brain, config, nlp 

def interpretar_consulta(frase):
    """
    Usa el SemanticBrain para desglosar la frase del usuario.
    """
    frase_norm = config.normalizar(frase)
    doc = nlp(frase_norm)
    
    intencion = {
        "sector": None,
        "dividendos": False,
        "magnitud": "max", # Por defecto buscamos lo mejor
        "tickers_especificos": []
    }
    
    # Recorremos cada palabra de la frase
    for token in doc:
        # 1. Detectar Sector
        s = brain.buscar_por_similitud(token.text, brain.sectores)
        if s: intencion["sector"] = s
        
        # 2. Detectar Dividendos
        d = brain.buscar_por_similitud(token.text, brain.dividendos)
        if d: intencion["dividendos"] = True
        
        # 3. Detectar Magnitud (¿Quiere lo más bajo o lo más alto?)
        if token.text in brain.keys_min: intencion["magnitud"] = "min"
        
    return intencion

# --- INTERFAZ STREAMLIT ---
st.title("🤖 Asesor Financiero IA")

consulta = st.text_input("¿Qué cartera deseas hoy?", placeholder="Ej: Quiero tecnología barata con dividendos")

if consulta:
    # La IA interpreta la frase
    plan = interpretar_consulta(consulta)
    
    # Cargamos el Excel
    df = pd.read_excel("Analisis_Cartera_Nasdaq_Markowitz.xlsx", sheet_name='06_Sectores', index_col=0)
    df_yield = pd.read_excel("Analisis_Cartera_Nasdaq_Markowitz.xlsx", sheet_name='07_Yield', index_col=0)
    df_stats = pd.read_excel("Analisis_Cartera_Nasdaq_Markowitz.xlsx", sheet_name='03_Stats', index_col=0)
    df_total = pd.concat([df, df_yield, df_stats], axis=1)

    # APLICAR FILTROS SEGÚN LA IA
    resultado = df_total.copy()
    
    if plan["sector"]:
        resultado = resultado[resultado["Sector"] == plan["sector"]]
        st.write(f"✅ Sector detectado: **{plan['sector']}**")
    
    if plan["dividendos"]:
        resultado = resultado[resultado["Yield_2024_%"] > 0]
        st.write("✅ Filtro aplicado: **Solo con Dividendos**")

    # Si la IA detectó "barato" o "bajo", ordenamos por PER de menor a mayor
    if plan["magnitud"] == "min":
        resultado = resultado.sort_values(by="PER", ascending=True)
    else:
        resultado = resultado.sort_values(by="Sharpe_Ratio", ascending=False)

    # RESULTADO FINAL
    if len(resultado) >= 2:
        tickers = resultado.index.tolist()
        st.success(f"He encontrado {len(tickers)} activos para tu estrategia.")
        
        if st.button("🚀 Optimizar Cartera"):
            fig, pesos, err = engine.optimizar_max_sharpe(tickers)
            st.pyplot(fig)
            st.table(pesos[pesos > 0.01])
    else:
        st.warning("No hay suficientes activos para esta combinación.")
