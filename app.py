# Ejemplo para leer las estadísticas en app.py
df_stats = pd.read_excel("data/Analisis_Cartera_Nasdaq_Markowitz.xlsx", sheet_name='03_Estadisticas_Activos', index_col=0)

# El buscador ahora puede mostrar el Sharpe Ratio directamente
st.write("Top activos por Sharpe Ratio:")
st.table(df_stats.head(10))
