from fastapi import FastAPI

# Esto crea el servidor
app = FastAPI()

# Esto es lo que Render busca para saber que la web funciona
@app.get("/")
def home():
    return {"mensaje": "Hola Mundo desde la API"}

# Esta es la ruta que usará tu buscador de Lovable más tarde
@app.get("/buscar")
def buscar(query: str = ""):
    return {"resultado": f"Has buscado: {query}"}