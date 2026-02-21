#Cargar archivos Excel o CSV, filtrar acciones por sector, agrupar datos y limpiar valores nulos.
import pandas as pd
#Realiza operaciones matemáticas a gran velocidad, se usa para el modelo de markowitz
import numpy as np
#Descargar precios históricos de acciones, dividendos, sectores y datos fundamentales (como el PER o los ingresos) en tiempo real.
import yfinance as yf
#Gestiona los mensajes de alerta de Python
import warnings
#Hace que pueda leer una fecha no como texto, sino como una fecha
from datetime import datetime

# Desactivar advertencias
warnings.filterwarnings('ignore')

# 1. PORTFOLIO Y FILTRADO DE ACTIVOS: excluímos los activos que no tienen datos
excluded_tickers = ["GOOG", "ATVI", "CERN", "WBA", "SGEN", "SPLK", "ANSS", "WLTW"]

portfolio_raw = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRO",
    "AVGO", "COST", "PEP", "ADBE", "CSCO", "CMCSA", "NFLX", "TMO", "AMD",
    "QCOM", "INTC", "AMAT", "SBUX", "GILD", "INTU", "MDLZ", "ISRG", "ADI",
    "PYPL", "VRTX", "BKNG", "FISV", "REGN", "LRCX", "CHTR", "MU",
    "MNST", "KHC", "WDAY", "MAR", "MRNA", "ASML", "CSX", "KDP", "MCHP",
    "AEP", "SNPS", "XEL", "IDXX", "CTAS", "KLAC", "FAST", "EA",
    "ADSK", "BIDU", "CDNS", "ALGN", "DLTR", "SWKS", "BIIB",
    "SIRI", "NTES", "ILMN", "PCAR", "DXCM", "PAYX", "INCY", "MCO",
    "JD", "ROST", "EXC", "PINS", "ODFL", "CTSH", "HBAN", "VRSK",
    "FOX", "CBOE", "TTWO", "EBAY", "ZM", "FTNT", "MTCH", "OKTA",
    "CPRT", "MRVL", "PTON", "DDOG", "DOCU", "CZR", "ABNB", "ZBRA"
]
#Crea una nueva lista llamada portfolio, recorre cada elemento (t) de la lista original (portfolio_raw),
#pero solo agrégalo a la nueva lista si ese elemento no está en mi lista de excluidos (excluded_tickers).
portfolio = [t for t in portfolio_raw if t not in excluded_tickers]

start_date = '2022-01-01'
end_date = '2025-01-01'
TARGET_YEARS = [2022, 2023, 2024]

# Creamos dataframes y diccionarios para guardar los datos
#Precios de cierre diarios
all_prices = pd.DataFrame()
#Dividendos para calcular la rentbailidad total
all_dividends = pd.DataFrame()
#Valores fundamentales, como beneficios o ingresos
fundamentales = {}
#Sectores y PER
valoracion = {}
#Dividend yield
yield_dic_2024 = {}

print(f"Iniciando proceso para {len(portfolio)} activos...")

# PARTE 1: EXTRACCIÓN Y CÁLCULOS DE DATOS
for ticker in portfolio:
    try:
#Crea un objeto que es como una "llave" para entrar a toda la información de una empresa
        stock = yf.Ticker(ticker)
#Descarga los precios históricos. Si no hay datos (hist.empty), el código usa continue para saltar a la siguiente empresa y no dar error.
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            continue
#Aquí llenas las tablas que creamos antes. Metes el precio de cierre en all_prices y los dividendos en all_dividends, filtrando para que las fechas coincidan con tu rango de estudio.
        all_prices[ticker] = hist['Close']
        divs = stock.dividends
        all_dividends[ticker] = divs[(divs.index >= start_date) & (divs.index <= end_date)]

        # --- Datos financieros ---
  #Originalmente, Yahoo Finance da las tablas con las fechas en las columnas y los conceptos (Net Income, etc.) en las filas. Al usar .T (Transponer),
  #les das la vuelta: las fechas pasan a ser las filas. Esto permite que el programa las recorra mucho más fácil.
        fin = stock.financials.T
        bs = stock.balance_sheet.T
        cf = stock.cashflow.T

        if not fin.empty and not bs.empty:
  #Unes la cuenta de resultados, el balance de situación y el flujo de caja en una sola gran tabla horizontal. Ahora, para una fecha determinada, tienes acceso a todos los datos contables de la empresa en una sola fila.
            df_full = pd.concat([fin, bs, cf], axis=1)
  #Esta línea limpia la tabla y se queda solo con los años que definiste al principio.
            if hasattr(df_full.index, 'year'):
                df_hist = df_full[df_full.index.year.isin(TARGET_YEARS)]
                for date, row in df_hist.iterrows():
                    year = date.year
                    fundamentales[(ticker, f"Net Income {year}")] = row.get('Net Income Common Stockholders', np.nan)
                    fundamentales[(ticker, f"Total Revenue {year}")] = row.get('Total Revenue', np.nan)
                    fundamentales[(ticker, f"EBITDA {year}")] = row.get('EBITDA', np.nan)
                    fundamentales[(ticker, f"Free Cash Flow {year}")] = row.get('Free Cash Flow', np.nan)
                    fundamentales[(ticker, f"Total Debt {year}")] = row.get('Total Debt', np.nan)
                    fundamentales[(ticker, f"Total Assets {year}")] = row.get('Total Assets', np.nan)

        # --- EXTRACCIÓN DE SECTOR, MARKET CAP Y VALORACIÓN ---
        info = stock.info

        valoracion[ticker] = {
            'Sector': info.get('sector', 'N/A'),
            'Industria': info.get('industry', 'N/A'),
            'Market Cap': info.get('marketCap', np.nan),
            'PER': info.get('trailingPE'),
            'Price to Sales': info.get('priceToSalesTrailing12Months'),
            'Price to Book': info.get('priceToBook')
        }

        # Dividendos 2024
        divs_2024 = stock.dividends[stock.dividends.index.year == 2024].sum()
        price_end_2024 = hist['Close'].iloc[-1] if not hist.empty else np.nan
        yield_dic_2024[ticker] = {'Yield 31/12/2024 (%)': (divs_2024 / price_end_2024) * 100 if price_end_2024 > 0 else 0}

        print(f"✅ {ticker} extraído con éxito.")

    except Exception as e:
        print(f"Error procesando {ticker}: {e}")

# PARTE 2: ORGANIZACIÓN DE TABLAS Y EXCEL
all_prices.index = pd.to_datetime(all_prices.index).strftime('%Y-%m-%d')
all_dividends = all_dividends.reindex(all_prices.index, fill_value=0)
daily_returns = (all_prices - all_prices.shift(1) + all_dividends) / all_prices.shift(1)
daily_returns = daily_returns.dropna(how='all')
daily_returns.index = pd.to_datetime(daily_returns.index).strftime('%Y-%m-%d')

df_fund_final = pd.Series(fundamentales).unstack().sort_index(axis=1)
df_val_final = pd.DataFrame.from_dict(valoracion, orient='index')
df_yield_final = pd.DataFrame.from_dict(yield_dic_2024, orient='index')

# GUARDADO EN EXCEL
nombre_archivo = "Analisis_Cartera_Nasdaq_Markowitz.xlsx"
with pd.ExcelWriter(nombre_archivo) as writer:
    all_prices.to_excel(writer, sheet_name='01_Precios_Cierre')
    daily_returns.to_excel(writer, sheet_name='03_Rentabilidad_Diaria')
    df_fund_final.to_excel(writer, sheet_name='04_Fundamentales')
    df_val_final.to_excel(writer, sheet_name='06_Sectores_y_MarketCap')
    df_yield_final.to_excel(writer, sheet_name='07_Yield_2024')

print(f"\n✅ Proceso finalizado. Archivo generado: {nombre_archivo}")