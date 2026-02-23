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
    Función que replica tu lógica de extracción y guarda los resultados en la carpeta data/
    """
    # Asegurar que la carpeta 'data' existe para que no de error al guardar
    if not os.path.exists('data'):
        os.makedirs('data')

    # 1. PORTFOLIO Y FILTRADO
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

    all_prices = pd.DataFrame()
    all_dividends = pd.DataFrame()
    fundamentales = {}
    valoracion = {}
    yield_dic_2024 = {}

    # PARTE 1: EXTRACCIÓN (Tu lógica original)
    for ticker in portfolio:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if hist.empty: continue

            all_prices[ticker] = hist['Close']
            divs = stock.dividends
            all_dividends[ticker] = divs[(divs.index >= start_date) & (divs.index <= end_date)]

            # Datos financieros
            fin = stock.financials.T
            bs = stock.balance_sheet.T
            cf = stock.cashflow.T

            if not fin.empty and not bs.empty:
                df_full = pd.concat([fin, bs, cf], axis=1)
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

            info = stock.info
            valoracion[ticker] = {
                'Sector': info.get('sector', 'N/A'),
                'Industria': info.get('industry', 'N/A'),
                'Market Cap': info.get('marketCap', np.nan),
                'PER': info.get('trailingPE'),
                'Price to Sales': info.get('priceToSalesTrailing12Months'),
                'Price to Book': info.get('priceToBook')
            }

            divs_2024 = stock.dividends[stock.dividends.index.year == 2024].sum()
            price_end_2024 = hist['Close'].iloc[-1] if not hist.empty else np.nan
            yield_dic_2024[ticker] = {'Yield 31/12/2024 (%)': (divs_2024 / price_end_2024) * 100 if price_end_2024 > 0 else 0}

        except Exception as e:
            print(f"Error procesando {ticker}: {e}")

    # PARTE 2: ORGANIZACIÓN Y GUARDADO
    all_prices.index = pd.to_datetime(all_prices.index).strftime('%Y-%m-%d')
    all_dividends = all_dividends.reindex(all_prices.index, fill_value=0)
    daily_returns = (all_prices - all_prices.shift(1) + all_dividends) / all_prices.shift(1)
    daily_returns = daily_returns.dropna(how='all')
    daily_returns.index = pd.to_datetime(daily_returns.index).strftime('%Y-%m-%d')

    df_fund_final = pd.Series(fundamentales).unstack().sort_index(axis=1)
    df_val_final = pd.DataFrame.from_dict(valoracion, orient='index')
    df_yield_final = pd.DataFrame.from_dict(yield_dic_2024, orient='index')

    with pd.ExcelWriter(nombre_archivo) as writer:
        all_prices.to_excel(writer, sheet_name='01_Precios_Cierre')
        daily_returns.to_excel(writer, sheet_name='03_Rentabilidad_Diaria')
        df_fund_final.to_excel(writer, sheet_name='04_Fundamentales')
        df_val_final.to_excel(writer, sheet_name='06_Sectores_y_MarketCap')
        df_yield_final.to_excel(writer, sheet_name='07_Yield_2024')

    return nombre_archivo
