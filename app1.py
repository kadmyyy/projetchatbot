#importations
import os
import json
import streamlit as st
import folium
from dotenv import load_dotenv
from streamlit_folium import folium_static
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from fuzzywuzzy import process

# Chargement des variables d'environnement
load_dotenv()
api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Modèle Hugging Face
repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
task = "text-generation"

# Chargement de la base de connaissances
with open("datasetchatbot.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

# Configurer l'application Streamlit
st.set_page_config(page_title="Téranga Tour", page_icon="🌍")

# Charger le CSS
def load_css():
    with open("styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# En-tête de l'application
st.title("Téranga Tour ✈️")

# Modèle de prompt avec contexte RAG
template = """
You are a friendly and knowledgeable travel assistant chatbot named Téranga Tour 
Use the following retrieved knowledge to enhance your answers, while keeping the conversation natural and engaging.

Retrieved knowledge:
{context}

Chat history:
{chat_history}

User question:
{user_question}

Provide a well-structured and informative response, making it sound natural and conversational.
"""
prompt = ChatPromptTemplate.from_template(template)

# Fonction pour récupérer les informations pertinentes
def retrieve_info(user_query):
    instructions = [entry["instruction"] for entry in knowledge_base]
    best_match, score = process.extractOne(user_query, instructions)
    
    if score > 70:
        for entry in knowledge_base:
            if entry["instruction"] == best_match:
                return entry["output"]
    
    return "I couldn't find relevant information in my database, but I can still try to help!"

# Fonction pour interagir avec le modèle LLM
def get_response(user_query, chat_history):
    retrieved_info = retrieve_info(user_query)

    llm = HuggingFaceEndpoint(
        huggingfacehub_api_token=api_token,
        repo_id=repo_id,
        task=task
    )

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "chat_history": chat_history,
        "user_question": user_query,
        "context": retrieved_info
    })

    # Nettoyage de la réponse
    response = response.replace(" response:", "").strip()
    response = response.replace("Assistant:", "").strip()
    
    return response.strip()

# Fonction pour afficher une carte uniquement si l'utilisateur demande un lieu
def afficher_carte(latitude, longitude, nom_lieu):
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        carte = folium.Map(location=[latitude, longitude], zoom_start=15)
        folium.Marker(
            location=[latitude, longitude],
            popup=nom_lieu,
            tooltip="Cliquez pour voir"
        ).add_to(carte)
        folium_static(carte)
        st.markdown('</div>', unsafe_allow_html=True)

# Liste des lieux touristiques
lieux_touristiques = {
    "Île de Gorée": (14.6684, -17.3984),
    "Lac Rose": (14.8486, -17.2348),
    "Monument de la Renaissance Africaine": (14.7225, -17.4945),
    "Parc National du Djoudj": (16.5593, -16.2632),
    "Désert de Lompoul": (15.5455, -16.5269)
}

# Liste de mots-clés pour détecter une demande de carte
keywords_localisation = ["localisation", "où se trouve", "adresse", "situer", "position", "emplacement", "carte", "map"]

# Initialiser l'historique du chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm Téranga Tour. How can I assist you with your travel plans today?")
    ]

# Affichage des messages du chat
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        st.markdown(f'<div class="bot-msg">{message.content}</div>', unsafe_allow_html=True)
    elif isinstance(message, HumanMessage):
        st.markdown(f'<div class="user-msg">{message.content}</div>', unsafe_allow_html=True)

# Zone de saisie utilisateur
user_query = st.chat_input("Type your message here...")
if user_query:
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    st.markdown(f'<div class="user-msg">{user_query}</div>', unsafe_allow_html=True)

    response = get_response(user_query, st.session_state.chat_history)

    st.markdown(f'<div class="bot-msg">{response}</div>', unsafe_allow_html=True)

    st.session_state.chat_history.append(AIMessage(content=response))

    # Vérifier si une localisation est demandée avant d'afficher la carte
    if any(keyword in user_query.lower() for keyword in keywords_localisation):
        best_match, score = process.extractOne(user_query, lieux_touristiques.keys())
        if score > 70:
            latitude, longitude = lieux_touristiques[best_match]
            afficher_carte(latitude, longitude, best_match)
