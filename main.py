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
# Cálculo de la rentabilidad esperada y el riesgo
# 1. Parámetros para anualizar
trading_days = 252
rf = 0.02 # Tasa libre de riesgo asumida (2%) para el Sharpe individual

# 2. Limpieza de seguridad
# Eliminamos activos que puedan haber quedado con NaN tras el filtrado de GOOG u otros errores
returns_clean = daily_returns.dropna(axis=1, how='all')

# 3. Calcular rendimiento esperado anualizado
# Rendimiento = Media diaria * 252
expected_returns = returns_clean.mean() * trading_days

# 4. Calcular riesgo anualizado (volatilidad)
# Riesgo = Desviación estándar diaria * raíz(252)
risk = returns_clean.std() * np.sqrt(trading_days)

# 5. Crear DataFrame con estadísticas de cada activo
assets_stats = pd.DataFrame({
    "Rendimiento_Anual_Esperado": expected_returns,
    "Riesgo_Anual": risk,
    "Sharpe_Ratio_Individual": (expected_returns - rf) / risk
})

# 6. Ordenar por rendimiento esperado (De mayor a menor)
assets_stats = assets_stats.sort_values(by="Rendimiento_Anual_Esperado", ascending=False)

# 7. Guardar en Excel
output_stats_file = "Estadisticas_Activos_2022_2024.xlsx"
assets_stats.to_excel(output_stats_file, sheet_name="Asset_Stats")

print(f"✅ Estadísticas calculadas para {len(assets_stats)} activos.")
print(f"Archivo guardado: {output_stats_file}")

# 8. Mostrar los 10 mejores activos por Rendimiento
print("\nTop 10 activos por Rendimiento Esperado:")
display(assets_stats.head(10))
# MATRIZ DE COVARIANZA Y CORRELACIONES (Ajustada)

# Usamos 'returns_clean' generado en el bloque estadístico anterior
# 1. Matriz de correlación
# Mide la relación lineal entre activos. Crucial para la diversificación.
correlation_matrix = returns_clean.corr()

print(f"Matriz de correlación para {len(correlation_matrix)} activos (Muestra 10x10):")
display(correlation_matrix.iloc[:10, :10])

# 2. Matriz de covarianza anualizada
# Es el motor del riesgo de la cartera. Se anualiza multiplicando por 252.
trading_days = 252
covariance_matrix = returns_clean.cov() * trading_days

print("\nMatriz de covarianza anualizada (Muestra 10x10):")
display(covariance_matrix.iloc[:10, :10])

# 3. Guardar en Excel
output_matrices_file = "Matrices_Correlacion_Covarianza_2022_2024.xlsx"
with pd.ExcelWriter(output_matrices_file) as writer:
    correlation_matrix.to_excel(writer, sheet_name="Correlacion")
    covariance_matrix.to_excel(writer, sheet_name="Covarianza")

print(f"\n✅ Matrices calculadas y guardadas en: {output_matrices_file}")
import scipy.optimize as sco
import matplotlib.pyplot as plt

# --- 1. FUNCIONES MATEMÁTICAS DE OPTIMIZACIÓN ---
def stats_cartera(pesos):
    pesos = np.array(pesos)
    ret = np.dot(pesos, expected_returns)
    vol = np.sqrt(np.dot(pesos.T, np.dot(covariance_matrix, pesos)))
    return np.array([ret, vol, (ret - rf) / vol])

def min_func_sharpe(pesos):
    return -stats_cartera(pesos)[2]

def min_func_variance(pesos):
    return stats_cartera(pesos)[1]**2

# --- 2. CÁLCULO DE LA CARTERA ÓPTIMA (MAX SHARPE) ---
num_activos = len(expected_returns)
cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
bounds = tuple((0, 1) for x in range(num_activos))
init_guess = num_activos * [1. / num_activos]

opts = sco.minimize(min_func_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
t_ret, t_vol, t_sharpe = stats_cartera(opts['x'])

# --- 3. CÁLCULO DE LOS PUNTOS DE LA FRONTERA EFICIENTE ---
# Generamos 50 niveles de retorno entre el mínimo y el máximo de los activos
target_returns = np.linspace(expected_returns.min(), expected_returns.max(), 50)
efficient_vols = []

for tret in target_returns:
    cons_especifica = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                       {'type': 'eq', 'fun': lambda x: stats_cartera(x)[0] - tret})
    res = sco.minimize(min_func_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons_especifica)
    efficient_vols.append(np.sqrt(res['fun']))

# --- 4. GENERACIÓN DEL GRÁFICO ---
plt.figure(figsize=(12, 8))

# Línea de la Frontera Eficiente
plt.plot(efficient_vols, target_returns, color='royalblue', linestyle='-', linewidth=2, label='Frontera Eficiente')

# Puntos sobre la curva (Carteras óptimas calculadas)
plt.scatter(efficient_vols, target_returns, c=target_returns/efficient_vols, cmap='viridis', s=30, label='Carteras Eficientes')

# Línea de Tangencia (CML)
x_cml = np.linspace(0, max(efficient_vols) * 1.2, 100)
y_cml = rf + t_sharpe * x_cml
plt.plot(x_cml, y_cml, color='forestgreen', linestyle='--', label=f'CML (Tangente rf={rf*100}%)')

# Cartera de Tangencia (Punto Max Sharpe)
plt.scatter(t_vol, t_ret, color='red', marker='*', s=400, label='Máximo Sharpe', zorder=10)

# Activos individuales por separado
plt.scatter(np.sqrt(np.diag(covariance_matrix)), expected_returns, color='gray', s=20, alpha=0.4, label='Activos Individuales')

plt.title('Frontera Eficiente de Markowitz: Optimización Media-Varianza', fontsize=14)
plt.xlabel('Volatilidad Anualizada (Riesgo)', fontsize=12)
plt.ylabel('Retorno Anualizado Esperado', fontsize=12)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.show()
import pandas as pd  # Librería para el manejo de estructuras de datos (tablas/DataFrames)
import numpy as np   # Librería para cálculos numéricos y operaciones matriciales
import scipy.optimize as sco  # Módulo para optimización matemática (usado en Markowitz)
import matplotlib.pyplot as plt  # Librería para la creación de gráficos y visualizaciones
import unicodedata  # Para el manejo de caracteres Unicode (quitar tildes/acentos)
import spacy        # Librería de Procesamiento de Lenguaje Natural (NLP)
import re           # Módulo de expresiones regulares para búsqueda de patrones de texto
import os           # Para interactuar con el sistema operativo (instalar modelos)
import warnings     # Para gestionar los mensajes de advertencia de Python
from datetime import datetime  # Para el manejo de fechas y tiempos
from IPython.display import display # Para mostrar tablas formateadas en entornos tipo Jupyter

class NasdaqConfig:
    def __init__(self):
        """Constructor de la clase de configuración."""
        # Filtra e ignora los mensajes de advertencia para mantener la consola limpia
        warnings.filterwarnings('ignore')
        # Llama al método interno para cargar y asignar el modelo de lenguaje a la instancia
        self.nlp = self._cargar_nlp()

    def _cargar_nlp(self):
        """Intenta cargar el modelo de spaCy. Si no lo encuentra, lo descarga automáticamente."""
        try:
            # Intenta cargar el modelo de tamaño medio en español (incluye vectores de palabras)
            return spacy.load("es_core_news_md")
        except:
            # Si el modelo no está instalado, ejecuta el comando de descarga en la terminal del sistema
            os.system("python -m spacy download es_core_news_md")
            # Una vez descargado, lo carga y lo devuelve
            return spacy.load("es_core_news_md")

    @staticmethod
    def normalizar(texto):
        """Limpia el texto: elimina tildes, caracteres especiales y lo pasa a minúsculas."""
        # Si el texto está vacío o es None, devuelve una cadena vacía para evitar errores
        if not texto: return ""

        # 1. Normaliza el texto separando los caracteres de sus acentos (NFD)
        # 2. Filtra eliminando los caracteres que son marcas de acentuación ('Mn')
        # 3. Vuelve a unir los caracteres en una cadena de texto limpia
        texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

        # Convierte todo a minúsculas y elimina espacios innecesarios al inicio y al final
        return texto.lower().strip()

# --- INICIALIZACIÓN ---

# Crea una instancia global de la configuración (ejecuta el constructor e inicializa NLP)
config = NasdaqConfig()

# Extrae el modelo NLP cargado para que pueda ser usado directamente en el resto del script
nlp = config.nlp
class SemanticBrain:
    def __init__(self):
        """
        Constructor de la clase. Aquí se definen las 'neuronas' o el conocimiento
        base del sistema mediante diccionarios de mapeo.
        """

        # Diccionario que traduce conceptos humanos a sectores oficiales de la industria financiera
        self.sectores = {
            "Technology": ["tecnologia", "tech", "software", "chip", "it", "informatica"],
            "Communication Services": ["comunicacion", "redes", "internet", "com", "telecom"],
            "Consumer Cyclical": ["consumo ciclico", "tienda", "comercio", "automovil", "ropa"],
            "Financial Services": ["financiero", "finanzas", "banco", "bancario", "dinero", "finanza", "bancos"],
            "Consumer Defensive": ["consumo defensivo", "alimentacion", "comida", "supermercado"],
            "Healthcare": ["salud", "sanidad", "medico", "pharma", "farmacia"],
            "Industrials": ["industriales", "fabrica", "logistica", "transporte"],
            "Utilities": ["servicios publicos", "utilities", "electricidad", "luz", "agua"]
        }

        # Mapea términos contables coloquiales a nombres de variables fundamentales
        self.fundamentales = {
            "Net Income": ["beneficio", "ganancia", "utilidad", "neto"],
            "Total Revenue": ["ingresos", "ventas", "revenue", "facturacion"],
            "Total Debt": ["deuda", "debt", "pasivo", "apalancamiento"],
            "EBITDA": ["ebitda", "margen"],
            "Free Cash Flow": ["caja", "flujo", "fcf", "efectivo"]
        }

        # Mapea formas de preguntar por la valoración de una empresa
        self.ratios = {
            "PER": ["per", "p/e", "valoracion", "multiplo"],
            "PriceToSales": ["precio ventas", "p/s", "ps"],
            "PriceToBook": ["valor contable", "p/b", "pb"]
        }

        # Categoría específica para temas relacionados con el reparto de beneficios
        self.dividendos = {"DividendYield": ["dividendo", "yield", "rentabilidad", "pago"]}

        # Listas de "sentimiento de magnitud" para detectar si el usuario busca valores altos o bajos
        self.keys_max = ["maximo", "mejor", "mayor", "top", "alto", "superior", "crecimiento", "maximiza", "max", "altos", "alta", "mucho"]
        self.keys_min = ["minimo", "peor", "menor", "bajo", "inferior", "caida", "bajada", "minimiza", "min", "barato", "poco", "bajos", "baja", "menos"]

    def buscar_por_similitud(self, palabra, diccionario, umbral=0.75):
        """
        Busca la categoría más probable para una palabra dada usando vectores semánticos.

        Parámetros:
        - palabra: El texto que ingresa el usuario (ej: 'guita' o 'bancario').
        - diccionario: El grupo donde buscar (self.sectores, self.fundamentales, etc.).
        - umbral: Nivel de confianza mínimo (0 a 1) para aceptar una coincidencia.
        """

        # Convertimos la palabra del usuario en un 'token' de spaCy (vector de significado)
        token_usuario = nlp(palabra)

        mejor_cat, max_sim = None, 0 # Variables para rastrear la categoría con mayor puntuación

        # Recorremos cada categoría y sus sinónimos definidos en el __init__
        for cat, sinonimos in diccionario.items():
            for s in sinonimos:
                # Comparamos matemáticamente la distancia semántica entre vectores
                # 'nlp(s)' convierte el sinónimo de la lista en vector para la comparación
                sim = token_usuario.similarity(nlp(s))

                # Si encontramos una similitud mayor a la registrada, actualizamos los ganadores
                if sim > max_sim:
                    max_sim, mejor_cat = sim, cat

        # Retornamos la categoría oficial solo si la confianza (max_sim) es mayor al umbral
        # Esto evita que una palabra sin sentido sea asignada a una categoría por error
        return mejor_cat if max_sim > umbral else None

# Instanciamos el objeto para que esté listo para usarse
brain = SemanticBrain()
class QueryEngine:
    def __init__(self, brain):
        """
        Constructor del motor de consultas.
        Recibe una instancia de 'SemanticBrain' y define el archivo para guardar el historial.
        """
        self.brain = brain
        self.log_file = "registro_aprendizaje_nasdaq.csv"

    def registrar_consulta(self, frase, riesgo, sector, ratio, div, fund):
        """
        Guarda la interpretación de la IA en un archivo CSV.
        Sirve para auditar cómo está entendiendo el sistema las peticiones del usuario.
        """
        nuevo_registro = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Frase_Usuario": frase, "Riesgo_Detectado": riesgo,
            "Sector_Detectado": sector, "Ratio_Interpretado": ratio,
            "Dividendo_Interpretado": div, "Fundamental_Interpretado": fund
        }
        df = pd.DataFrame([nuevo_registro])
        # Comprueba si el archivo ya existe para saber si debe escribir el encabezado
        header = not os.path.isfile(self.log_file)
        # 'mode=a' significa 'append' (añadir al final sin borrar lo anterior)
        df.to_csv(self.log_file, mode='a', index=False, header=header, encoding='utf-8-sig')

    def determinar_direccion(self, sinonimos, texto_tokens):
        """
        Analiza el contexto de una palabra para saber si el usuario quiere algo
        'bajo/mínimo' (True) o 'alto/máximo' (False).
        """
        idx = -1
        # Busca en qué posición de la frase está la métrica financiera (ej: 'per')
        for s in sinonimos:
            ns = NasdaqConfig.normalizar(s)
            if ns in texto_tokens:
                idx = texto_tokens.index(ns)
                break

        if idx == -1: return False # Si no encuentra la métrica, asume dirección por defecto

        # Revisa la palabra anterior (idx-1) o la siguiente (idx+1) para ver si hay
        # palabras como 'bajo', 'poco' o 'barato' (keys_min)
        if idx > 0 and any(k in texto_tokens[idx-1] for k in self.brain.keys_min): return True
        if idx < len(texto_tokens)-1 and any(k in texto_tokens[idx+1] for k in self.brain.keys_min): return True

        return False # Por defecto, si no hay palabras de 'mínimo', asume que busca lo 'alto'

    def interpretar(self, frase):
        """
        El método principal: convierte lenguaje natural en variables lógicas.
        """
        # 1. Limpieza inicial con spaCy: sacamos lemas (raíces de palabras), quitamos puntos y conectores
        doc = nlp(frase.lower())
        lemas = [NasdaqConfig.normalizar(t.lemma_) for t in doc if not t.is_stop and not t.is_punct]
        tokens = NasdaqConfig.normalizar(frase).split()

        # 2. Detección de Riesgo: busca palabras clave para clasificar la agresividad de la inversión
        riesgo = next((r for r, k in {"Bajo":["bajo", "seg", "cons"], "Alto":["alt", "arr", "agr"], "Medio":["med", "mod"]}.items() if any(x in lemas for x in k)), "Medio")

        # 3. Detección de Sector: busca coincidencia exacta por lema, si falla, usa similitud semántica
        sector = next((k for k, v in self.brain.sectores.items() if any(NasdaqConfig.normalizar(nlp(s)[0].lemma_) in lemas for s in v)), None)
        if not sector:
            for p in lemas: # Si no hay coincidencia exacta, probamos palabra por palabra vectorialmente
                sector = self.brain.buscar_por_similitud(p, self.brain.sectores)
                if sector: break

        # 4. Análisis de Indicadores (Ratios, Dividendos, Fundamentales)
        # Detecta qué métrica quiere el usuario y su dirección (ascendente/descendente)

        # Ratios (ej: PER)
        r_det = next((k for k, v in self.brain.ratios.items() if any(NasdaqConfig.normalizar(nlp(s)[0].lemma_) in lemas for s in v)), None)
        r_asc = self.determinar_direccion(self.brain.ratios.get(r_det, []), tokens) if r_det else False

        # Dividendos (ej: Yield)
        d_det = next((k for k, v in self.brain.dividendos.items() if any(NasdaqConfig.normalizar(nlp(s)[0].lemma_) in lemas for s in v)), None)
        d_asc = self.determinar_direccion(self.brain.dividendos.get(d_det, []), tokens) if d_det else False

        # Fundamentales (ej: Ingresos)
        f_det = next((k for k, v in self.brain.fundamentales.items() if any(NasdaqConfig.normalizar(nlp(s)[0].lemma_) in lemas for s in v)), None)
        f_asc = self.determinar_direccion(self.brain.fundamentales.get(f_det, []), tokens) if f_det else False

        # 5. Registro y Retorno de resultados
        self.registrar_consulta(frase, riesgo, sector, r_det, d_det, f_det)
        return riesgo, sector, r_det, r_asc, d_det, d_asc, f_det, f_asc

# Inicialización
engine = QueryEngine(brain)
class NasdaqPortfolioOptimizer:
    def __init__(self, data_path):
        """
        Inicializa el optimizador estableciendo la ruta del archivo Excel
        que contiene toda la base de datos financiera del Nasdaq.
        """
        self.data_path = data_path

    def ejecutar(self, params):
        """
        Recibe los parámetros extraídos por el QueryEngine (riesgo, sector, ratios, etc.)
        y realiza todo el flujo de filtrado y optimización matemática.
        """
        # Desempaquetado de los parámetros de búsqueda e interpretación
        riesgo, sector, r_det, r_asc, d_det, d_asc, f_det, f_asc = params

        try:
            # --- FASE 1: CARGA DE DATOS ---
            # Lee la hoja de sectores y capitalización de mercado
            df_val = pd.read_excel(self.data_path, sheet_name='06_Sectores_y_MarketCap', index_col=0)
            # Lee la hoja de rentabilidades históricas diarias para el cálculo de volatilidad
            daily_returns = pd.read_excel(self.data_path, sheet_name='03_Rentabilidad_Diaria', index_col=0)
            # Limpia espacios en blanco en los nombres de las columnas
            df_val.columns = [c.strip() for c in df_val.columns]

            # --- FASE 2: FILTRADO POR SECTOR Y RATIOS ---
            # Si se detectó un sector, filtramos los activos; si no, usamos toda la lista disponible
            activos_base = df_val[df_val['Sector'] == sector].index.tolist() if sector else df_val.index.tolist()

            # Bucle para filtrar por Ratios (PER) y Dividendos (Yield)
            for f, asc, d in [(r_det, r_asc, df_val), (d_det, d_asc, df_val)]:
                if f:
                    # Busca la columna que coincida con el ratio solicitado (ej: "PriceToSales")
                    col = next((c for c in d.columns if f in c or c.lower() == f.lower()), None)
                    if col:
                        # Ordena los activos según el criterio (ascendente/descendente) y se queda con la mejor mitad
                        activos_base = d.loc[activos_base].sort_values(by=col, ascending=asc).head(max(5, len(activos_base)//2)).index.tolist()

            # --- FASE 3: ANÁLISIS FUNDAMENTAL (CRECIMIENTO) ---
            if f_det:
                # Carga datos de balances financieros (Net Income, Revenue, etc.)
                df_fund = pd.read_excel(self.data_path, sheet_name='04_Fundamentales')
                df_fund.columns = [c.strip() for c in df_fund.columns]
                col_t = next((c for c in df_fund.columns if c.lower() == 'ticker'), None)

                # Crea una tabla dinámica para comparar el valor del fundamental entre 2022 y 2024
                df_p = df_fund[df_fund[col_t].isin(activos_base)].pivot(index=col_t, columns='Año', values=f_det).dropna()
                if not df_p.empty:
                    # Calcula la tasa de crecimiento porcentual en el periodo de 2 años
                    tasa = ((df_p[2024] - df_p[2022]) / df_p[2022].abs()) * 100
                    # Filtra los activos con mejor (o peor) crecimiento según solicitó el usuario
                    activos_base = tasa.sort_values(ascending=f_asc).head(max(3, len(tasa)//2)).index.tolist()

            # --- FASE 4: OPTIMIZACIÓN DE MARKOWITZ ---
            # Asegura que los activos filtrados tengan datos de retornos diarios disponibles
            activos = [t for t in activos_base if t in daily_returns.columns]
            if len(activos) < 3: return print("⚠️ Activos insuficientes para optimizar.")

            # Calcula el retorno esperado anualizado y la matriz de covarianza (riesgo)
            returns_c = daily_returns[activos].dropna()
            exp_ret, cov_mat = returns_c.mean() * 252, returns_c.cov() * 252

            puntos = [] # Lista para guardar los puntos de la Frontera Eficiente
            # Genera 100 carteras posibles variando el retorno objetivo
            for tr in np.linspace(exp_ret.min(), exp_ret.max(), 100):
                # Restricciones: suma de pesos = 1, y el retorno debe ser igual al retorno objetivo (tr)
                cons = ({'type': 'eq', 'fun': lambda x: np.sum(x)-1}, {'type': 'eq', 'fun': lambda x: np.dot(x, exp_ret)-tr})
                # Minimiza la volatilidad (riesgo) para cada nivel de retorno
                res = sco.minimize(lambda x: np.sqrt(np.dot(x.T, np.dot(cov_mat, x))), [1./len(activos)]*len(activos),
                                   method='SLSQP', bounds=tuple((0,1) for _ in activos), constraints=cons)
                if res.success:
                    # Calcula el Ratio de Sharpe (Retorno - Tasa Libre de Riesgo 2% / Riesgo)
                    puntos.append({'Ret': tr, 'Vol': res['fun'], 'Sharpe': (tr-0.02)/res['fun'], 'Pesos': res.x})

            # --- FASE 5: SELECCIÓN SEGÚN PERFIL DE RIESGO ---
            df_ef = pd.DataFrame(puntos).sort_values('Vol')
            n = len(df_ef)
            # Divide la frontera eficiente en tres segmentos según el riesgo detectado
            if riesgo == "Bajo":
                df_sel = df_ef.iloc[:int(n*0.33)] # Tercio de menor volatilidad
            elif riesgo == "Alto":
                df_sel = df_ef.iloc[int(n*0.66):] # Tercio de mayor retorno/riesgo
            else:
                df_sel = df_ef.iloc[int(n*0.33):int(n*0.66)] # Segmento intermedio

            # De ese segmento, elige la cartera con el mejor Ratio de Sharpe (la más eficiente)
            cartera_final = df_sel.loc[[df_sel['Sharpe'].idxmax()]]

            # --- FASE 6: VISUALIZACIÓN ---

            plt.figure(figsize=(10, 5))
            plt.scatter(df_ef['Vol'], df_ef['Ret'], c=df_ef['Sharpe'], cmap='viridis', alpha=0.3)
            plt.scatter(cartera_final['Vol'], cartera_final['Ret'], color='red', marker='*', s=250, label='Cartera Óptima')
            plt.title(f"Optimización Nasdaq Multifactorial | Perfil: {riesgo}")
            plt.xlabel("Volatilidad (Riesgo)")
            plt.ylabel("Retorno Esperado")
            plt.show()

            # Muestra la tabla de pesos finales para el usuario
            display(pd.DataFrame({'Activo': activos, 'Peso (%)': np.round(cartera_final['Pesos'].values[0]*100, 2)}).sort_values('Peso (%)', ascending=False).head(10))

        except Exception as e: print(f"❌ Error en el proceso: {e}")

# --- INICIALIZACIÓN ---
optimizer = NasdaqPortfolioOptimizer("Analisis_Cartera_Nasdaq_Markowitz.xlsx")
class NasdaqApp:
    """
    Clase principal que actúa como interfaz de usuario.
    Coordina el flujo desde la entrada de texto hasta el resultado financiero.
    """

    def __init__(self, engine, optimizer):
        self.engine = engine
        self.optimizer = optimizer

    def mostrar_bienvenida(self):
        """Muestra el texto informativo original solicitado."""
        texto = """
================================================================================
            SISTEMA DE ANÁLISIS MULTIFACTORIAL Y OPTIMIZACIÓN NASDAQ
================================================================================
Instrucciones: Describa su estrategia combinando Sector, Riesgo y Métricas.

1. SECTORES DISPONIBLES (Mapeo Automático):
   • Tecnología              • Comunicaciones           • Consumo Cíclico
   • Servicios Financieros   • Consumo Defensivo        • Salud / Sanidad
   • Industriales            • Servicios Públicos (Utilities)

2. RATIOS DE VALORACIÓN (Para identificar empresas infravaloradas):
   • PER (Relación Precio/Beneficio): Veces que el precio contiene al beneficio.
   • Relación Precio/Ventas: Comparación entre el precio y las ventas totales.
   • Relación Precio/Valor Contable: Compara el precio con el patrimonio neto.

3. MÉTRICAS FUNDAMENTALES (Salud financiera):
   • Beneficio Neto: Ganancia real después de todos los gastos e impuestos.
   • Ingresos Totales: Dinero bruto generado por las ventas.
   • EBITDA: Beneficio antes de intereses, impuestos y amortizaciones.
   • Deuda Total: Nivel de endeudamiento total de la empresa.
   • Flujo de Caja Libre: Dinero disponible para reinvertir o pagar dividendos.
   • Activos Totales: Valor de todas las propiedades y derechos de la empresa.

4. RENTABILIDAD POR DIVIDENDO:
   • Rendimiento (Yield %): Porcentaje de beneficio devuelto al accionista.

5. PERFIL DE RIESGO (Segmentación por Tercios de Markowitz):
   • BAJO: Tramo conservador (0% - 33% de la volatilidad en la frontera).
   • MEDIO: Tramo moderado (33% - 66% de la curva).
   • ALTO: Tramo agresivo (66% - 100% de la curva).

EJEMPLO: "Cartera de salud con riesgo bajo, PER menor a 20 y dividendos altos"
================================================================================
        """
        print(texto)

    def ejecutar(self):
        """Inicia el bucle de interacción con el usuario."""
        self.mostrar_bienvenida()

        # --- INPUT DEL USUARIO ---
        consulta_usuario = input("👉 Introduzca su consulta de inversión: ")

        if not consulta_usuario.strip():
            print("⚠️ La consulta no puede estar vacía.")
            return

        print("\n🧠 Procesando lenguaje natural...")

        # 1. Interpretación Semántica (Parte 3)
        parametros = self.engine.interpretar(consulta_usuario)

        # Mostrar tabla de trazabilidad para que el usuario vea qué entendió la IA
        res_riesgo, res_sector, r_det, r_asc, d_det, d_asc, f_det, f_asc = parametros
        mapeo_debug = [
            ["Perfil de Riesgo", res_riesgo],
            ["Sector Identificado", res_sector if res_sector else "Global (Nasdaq 100)"],
            ["Filtro de Ratio", f"{r_det} ({'Minimizar' if r_asc else 'Maximizar'})" if r_det else "Ninguno"],
            ["Filtro Dividendo", f"{d_det} ({'Minimizar' if d_asc else 'Maximizar'})" if d_det else "Ninguno"],
            ["Filtro Fundamental", f"{f_det} ({'Minimizar' if f_asc else 'Maximizar'})" if f_det else "Ninguno"]
        ]
        display(pd.DataFrame(mapeo_debug, columns=["Parámetro", "Interpretación de la IA"]))

        # 2. Optimización Financiera (Parte 4)
        print("\n📈 Ejecutando optimización de Markowitz...")
        self.optimizer.ejecutar(parametros)


# ==============================================================================
# PUNTO DE ENTRADA AL PROGRAMA
# ==============================================================================

# 1. Instanciamos el Optimizador con la ruta del archivo Excel
optimizador_nasdaq = NasdaqPortfolioOptimizer("Analisis_Cartera_Nasdaq_Markowitz.xlsx")

# 2. Creamos la Aplicación principal
app = NasdaqApp(engine, optimizador_nasdaq)

# 3. Lanzamos el sistema
app.ejecutar()
