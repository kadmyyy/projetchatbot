import streamlit as st
import subprocess

st.set_page_config(page_title="Téranga Tour", page_icon="🌍", layout="wide")

# CSS + HTML stylisé
st.markdown("""
    <style>
        .hero {
            background-image: url('https://www.cherifaistesvalises.com/wp-content/uploads/2022/07/shutterstock_1916503415-1200x675.jpg');
            background-size: cover;
            background-position: center;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            color: white;
            position: relative;
        }

        .hero::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(0, 0, 0, 0.5); /* assombrit l’image */
            z-index: 0;
        }

        .hero-content {
            position: relative;
            z-index: 1;
            max-width: 800px;
        }

        .hero h1 {
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 0.5em;
        }

        .hero h2 {
            font-size: 1.7em;
            font-weight: 400;
            margin-bottom: 1.5em;
            font-style: italic;
        }

        .btn {
            display: inline-block;
            margin: 10px;
            padding: 12px 30px;
            font-size: 16px;
            border: 2px solid white;
            color: white;
            background-color: transparent;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
        }

        .btn:hover {
            background-color: white;
            color: black;
        }

    </style>
""", unsafe_allow_html=True)

# Section principale
st.markdown("""
    <div class="hero">
        <div class="hero-content">
            <h1>Téranga Chatbot Sénégal 🌍</h1>
            <h2>Découvrez le Sénégal autrement avec notre assistant de voyage intelligent.</h2>
            <a class="btn" href="#">À propos</a>
            <a class="btn" href="#">Réserver un Tour</a>
        </div>
    </div>
""", unsafe_allow_html=True)

# (Optionnel) Démarrage chatbot
if st.button("🗣️ Démarrer le Chatbot"):
    st.success("Le chatbot se lance...")
    subprocess.Popen(["chainlit", "run", "app.py", "--port", "8503"])
    st.markdown("➡️ Accédez au chatbot [ici](http://localhost:8503).")
