import streamlit as st
import subprocess

st.set_page_config(page_title="Téranga Tour", page_icon="🌍")

st.title("Bienvenue sur Téranga Tour 🌍")
st.write("Découvrez les merveilles du Sénégal avec notre assistant intelligent.")

if st.button("🗣️ Démarrer le Chatbot"):
    st.success("Le chatbot démarre... Veuillez patienter.")
    subprocess.Popen(["chainlit", "run", "app.py", "--port", "8503"])
    st.markdown("👉 Le chatbot est disponible [ici](http://localhost:8503) dans un nouvel onglet.")
