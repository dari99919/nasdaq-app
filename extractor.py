import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import os

# Desactivar advertencias
warnings.filterwarnings('ignore')

# Cambiamos la ruta por defecto a la raíz (sin data/)
def ejecutar_extraccion(nombre_archivo="Analisis_Cartera_Nasdaq_Markowitz.xlsx"):
    """
    Extrae datos financieros, fundamentales y calcula métricas de riesgo/retorno.
    """
    # --- 1. CONFIGURACIÓN ---
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
    portfolio = [t for t in portfolio_raw if t not in excluded_tickers]
    
    start_date = '2022-01-01'
    end_date = '2025-01-01'
    trading_days = 252
    rf = 0.02

    all_prices = pd.DataFrame()
    all_dividends = pd.DataFrame()
    valoracion = {}
    yield_dic_2024 = {}
    fundamentales_data = [] # Para guardar datos contables

    # --- 2. PROCESO DE EXTRACCIÓN ---
    print(f"Extrayendo {len(portfolio)} activos...")
    for ticker in portfolio:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty: continue

            # Precios y Dividendos
            all_prices[ticker] = hist['Close']
            divs = stock.dividends
            all_dividends[ticker] = divs[(divs.index >= start_date) & (divs.index <= end_date)]

            # Datos de Valoración (Info)
            info = stock.info
            valoracion[ticker] = {
                'Sector': info.get('sector', 'N/A'),
                'Industria': info.get('industry', 'N/A'),
                'Market Cap': info.get('marketCap', np.nan),
                'PER': info.get('trailingPE'),
                'Price_to_Sales': info.get('priceToSalesTrailing12Months')
            }
            
            # Yield 2024
            divs_2024 = stock.dividends[stock.dividends.index.year == 2024].sum()
            price_last = hist['Close'].iloc[-1]
            yield_dic_2024[ticker] = {'Yield_2024_%': (divs_2024 / price_last) * 100 if price_last > 0 else 0}

        except Exception as e:
            print(f"Error en {ticker}: {e}")

    # --- 3. CÁLCULOS MATEMÁTICOS ---
    all_prices.index = pd.to_datetime(all_prices.index).strftime('%Y-%m-%d')
    all_dividends = all_dividends.reindex(all_prices.index, fill_value=0)
    
    # Rentabilidades (incluyendo dividendos)
    daily_returns = (all_prices - all_prices.shift(1) + all_dividends) / all_prices.shift(1)
    returns_clean = daily_returns.dropna(how='all').dropna(axis=1, how='all')

    # Estadísticas Anualizadas
    expected_returns = returns_clean.mean() * trading_days
    volatility = returns_clean.std() * np.sqrt(trading_days)
    
    assets_stats = pd.DataFrame({
        "Retorno_Esperado": expected_returns,
        "Volatilidad": volatility,
        "Sharpe_Ratio": (expected_returns - rf) / volatility
    }).sort_values(by="Sharpe_Ratio", ascending=False)

    # Matrices para Markowitz
    corr_matrix = returns_clean.corr()
    cov_matrix = returns_clean.cov() * trading_days

    # --- 4. GUARDADO EN RAÍZ ---
    with pd.ExcelWriter(nombre_archivo) as writer:
        all_prices.to_excel(writer, sheet_name='01_Precios')
        returns_clean.to_excel(writer, sheet_name='02_Rentabilidades')
        assets_stats.to_excel(writer, sheet_name='03_Stats')
        corr_matrix.to_excel(writer, sheet_name='04_Correlacion')
        cov_matrix.to_excel(writer, sheet_name='05_Covarianza')
        pd.DataFrame.from_dict(valoracion, orient='index').to_excel(writer, sheet_name='06_Sectores')
        pd.DataFrame.from_dict(yield_dic_2024, orient='index').to_excel(writer, sheet_name='07_Yield')

    print(f"✅ Archivo generado: {nombre_archivo}")
    return nombre_archivo
