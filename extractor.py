import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import os
from datetime import datetime

# Desactivar advertencias
warnings.filterwarnings('ignore')

def ejecutar_extraccion(nombre_archivo="data/Analisis_Cartera_Nasdaq_Markowitz.xlsx"):
    """
    Extrae datos, calcula rentabilidades, riesgos, correlaciones y 
    guarda todo en un único archivo Excel con varias pestañas.
    """
    if not os.path.exists('data'):
        os.makedirs('data')

    # --- 1. CONFIGURACIÓN Y PORTFOLIO ---
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
    TARGET_YEARS = [2022, 2023, 2024]
    trading_days = 252
    rf = 0.02

    all_prices = pd.DataFrame()
    all_dividends = pd.DataFrame()
    fundamentales = {}
    valoracion = {}
    yield_dic_2024 = {}

    # --- 2. EXTRACCIÓN DE DATOS ---
    print(f"Iniciando extracción para {len(portfolio)} activos...")
    for ticker in portfolio:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty: continue

            all_prices[ticker] = hist['Close']
            divs = stock.dividends
            all_dividends[ticker] = divs[(divs.index >= start_date) & (divs.index <= end_date)]

            # Fundamentales (simplificado para el ejemplo)
            info = stock.info
            valoracion[ticker] = {
                'Sector': info.get('sector', 'N/A'),
                'Market Cap': info.get('marketCap', np.nan),
                'PER': info.get('trailingPE')
            }
            
            # Yield 2024
            divs_2024 = stock.dividends[stock.dividends.index.year == 2024].sum()
            price_end_2024 = hist['Close'].iloc[-1] if not hist.empty else np.nan
            yield_dic_2024[ticker] = {'Yield_2024_%': (divs_2024 / price_end_2024) * 100 if price_end_2024 > 0 else 0}

        except Exception as e:
            print(f"Error en {ticker}: {e}")

    # --- 3. CÁLCULO DE RENTABILIDADES Y MATRICES ---
    # Limpieza y Rentabilidad Diaria
    all_prices.index = pd.to_datetime(all_prices.index).strftime('%Y-%m-%d')
    all_dividends = all_dividends.reindex(all_prices.index, fill_value=0)
    
    # daily_returns = (Precio_hoy - Precio_ayer + Divs) / Precio_ayer
    daily_returns = (all_prices - all_prices.shift(1) + all_dividends) / all_prices.shift(1)
    returns_clean = daily_returns.dropna(how='all').dropna(axis=1, how='all')

    # Estadísticas Anualizadas
    expected_returns = returns_clean.mean() * trading_days
    risk = returns_clean.std() * np.sqrt(trading_days)
    
    assets_stats = pd.DataFrame({
        "Rendimiento_Anual": expected_returns,
        "Riesgo_Anual": risk,
        "Sharpe_Ratio": (expected_returns - rf) / risk
    }).sort_values(by="Rendimiento_Anual", ascending=False)

    # Matrices
    correlation_matrix = returns_clean.corr()
    covariance_matrix = returns_clean.cov() * trading_days

    # --- 4. GUARDADO MAESTRO EN UN SOLO EXCEL ---
    with pd.ExcelWriter(nombre_archivo) as writer:
        all_prices.to_excel(writer, sheet_name='01_Precios')
        returns_clean.to_excel(writer, sheet_name='02_Rentabilidades_Limpias')
        assets_stats.to_excel(writer, sheet_name='03_Estadisticas_Activos')
        correlation_matrix.to_excel(writer, sheet_name='04_Correlacion')
        covariance_matrix.to_excel(writer, sheet_name='05_Covarianza')
        pd.DataFrame.from_dict(valoracion, orient='index').to_excel(writer, sheet_name='06_Sectores')
        pd.DataFrame.from_dict(yield_dic_2024, orient='index').to_excel(writer, sheet_name='07_Yield')

    print(f"✅ Extracción y cálculos finalizados: {nombre_archivo}")
    return nombre_archivo
