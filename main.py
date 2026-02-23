import streamlit as st

# Esto SÍ se ve en la web
st.title("¡Mi primera web!")
st.write("Hola mundo, esta es mi página oficial.")

# Esto NO se ve en la web (solo lo verías tú en los logs de Streamlit)
print("Esto se queda en la consola")
