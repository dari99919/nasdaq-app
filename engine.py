import numpy as np
import pandas as pd
import scipy.optimize as sco
import matplotlib.pyplot as plt

def optimizar_max_sharpe(tickers, excel_path="Analisis_Cartera_Nasdaq_Markowitz.xlsx"):
    try:
        # Carga de datos estadísticos y covarianza
        returns = pd.read_excel(excel_path, sheet_name='03_Stats', index_col=0).loc[tickers, 'Retorno_Esperado']
        cov = pd.read_excel(excel_path, sheet_name='05_Covarianza', index_col=0).loc[tickers, tickers]
        rf = 0.02
    except Exception as e:
        return None, None, f"Error al leer datos: {e}"

    num_assets = len(tickers)
    
    # Función para calcular Retorno, Volatilidad y Sharpe
    def stats(weights):
        weights = np.array(weights)
        ret = np.dot(weights, returns)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        return np.array([ret, vol, (ret - rf) / vol])

    # Función objetivo: Maximizar Sharpe (Minimizar el Sharpe negativo)
    def min_sharpe(weights):
        return -stats(weights)[2]

    # Restricciones: la suma de pesos debe ser 1 (100%)
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # Límites: cada peso entre 0 y 1 (no cortos)
    bounds = tuple((0, 1) for x in range(num_assets))
    # Punto de partida: distribución equitativa
    init_guess = num_assets * [1. / num_assets]

    # Ejecución de la optimización
    opts = sco.minimize(min_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
    
    # Generar gráfico de resultados
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(np.sqrt(np.diag(cov)), returns, c=(returns-rf)/np.sqrt(np.diag(cov)), marker='o', label='Activos seleccionados')
    
    # Punto de la cartera óptima
    res_stats = stats(opts['x'])
    ax.scatter(res_stats[1], res_stats[0], marker='*', color='red', s=200, label='Cartera Óptima (Max Sharpe)')
    
    ax.set_title(f'Optimización de Cartera: {len(tickers)} activos')
    ax.set_xlabel('Riesgo (Volatilidad)')
    ax.set_ylabel('Retorno Esperado')
    ax.legend()
    ax.grid(True, alpha=0.3)

    pesos_finales = pd.Series(opts['x'], index=tickers)
    return fig, pesos_finales, None
