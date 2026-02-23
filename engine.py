import numpy as np
import pandas as pd
import scipy.optimize as sco
import matplotlib.pyplot as plt

def optimizar_cartera(excel_path="Analisis_Cartera_Nasdaq_Markowitz.xlsx"):
    # 1. Cargar datos del Excel que generó el extractor
    try:
        expected_returns = pd.read_excel(excel_path, sheet_name='03_Stats', index_col=0)['Retorno_Esperado']
        covariance_matrix = pd.read_excel(excel_path, sheet_name='05_Covarianza', index_col=0)
        rf = 0.02
    except Exception as e:
        return None, f"Error al cargar Excel: {e}"

    num_activos = len(expected_returns)

    # --- FUNCIONES INTERNAS ---
    def stats_cartera(pesos):
        pesos = np.array(pesos)
        ret = np.dot(pesos, expected_returns)
        vol = np.sqrt(np.dot(pesos.T, np.dot(covariance_matrix, pesos)))
        return np.array([ret, vol, (ret - rf) / vol])

    def min_func_sharpe(pesos):
        return -stats_cartera(pesos)[2]

    def min_func_variance(pesos):
        return stats_cartera(pesos)[1]**2

    # --- OPTIMIZACIÓN ---
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for x in range(num_activos))
    init_guess = num_activos * [1. / num_activos]

    opts = sco.minimize(min_func_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
    t_ret, t_vol, t_sharpe = stats_cartera(opts['x'])

    # --- FRONTERA EFICIENTE ---
    target_returns = np.linspace(expected_returns.min(), expected_returns.max(), 50)
    efficient_vols = []
    for tret in target_returns:
        cons_especifica = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                           {'type': 'eq', 'fun': lambda x: stats_cartera(x)[0] - tret})
        res = sco.minimize(min_func_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons_especifica)
        efficient_vols.append(np.sqrt(res['fun']))

    # --- GENERAR FIGURA (Sin plt.show) ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(efficient_vols, target_returns, color='royalblue', label='Frontera Eficiente')
    ax.scatter(t_vol, t_ret, color='red', marker='*', s=200, label='Max Sharpe')
    
    # CML
    x_cml = np.linspace(0, max(efficient_vols) * 1.2, 100)
    y_cml = rf + t_sharpe * x_cml
    ax.plot(x_cml, y_cml, color='green', linestyle='--', label='CML')
    
    ax.set_title('Optimización de Cartera Markowitz')
    ax.set_xlabel('Riesgo (Volatilidad)')
    ax.set_ylabel('Retorno Esperado')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Devolvemos la figura y los pesos óptimos
    pesos_finales = pd.Series(opts['x'], index=expected_returns.index)
    return fig, pesos_finales
