import streamlit as st

# 1. Configuración de la pestaña del navegador
st.set_page_config(page_title="Mi Buscador Inteligente", page_icon="🔍")

# 2. Título y diseño visual
st.title("🔍 Buscador de Proyectos")
st.markdown("---") # Una línea divisoria para que se vea limpio

# 3. El Buscador (Input)
# Guardamos lo que el usuario escribe en la variable 'termino'
termino = st.text_input("¿Qué estás buscando?", placeholder="Ej: Datos de CaixaBank...")

# 4. Botón de acción
if st.button("Ejecutar Búsqueda"):
    if termino:
        # Aquí es donde el código da una respuesta basada en lo que el usuario puso
        st.subheader(f"Resultados para: {termino}")
        
        # Simulamos una lógica de respuesta
        if "caixabank" in termino.lower():
            st.info("ℹ️ Información detectada: El Consejero Coordinador de CaixaBank no es ejecutivo.")
            st.write("Datos de la tabla procesada:")
            st.table({"Categoría": ["Dietas", "Comisiones"], "Total": [454, 861]})
        else:
            st.success(f"He encontrado información relevante sobre '{termino}' en la red.")
            st.write(f"Has buscado el término: **{termino}**. Pulsa el botón de abajo para ver más.")
            
            # Generamos un link externo dinámico
            url = f"https://www.google.com/search?q={termino}"
            st.markdown(f"[🔗 Haz clic aquí para ver resultados completos]({url})")
            
        st.balloons() # ¡Efecto de globos para celebrar la búsqueda!
    else:
        st.warning("⚠️ Por favor, escribe algo antes de buscar.")

# 5. Pie de página o Sidebar
st.sidebar.title("Sobre esta App")
st.sidebar.write("Esta aplicación está alojada en Streamlit Cloud y conectada a GitHub.")
