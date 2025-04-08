import os
import json
import gradio as gr
import folium
from dotenv import load_dotenv
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

# Modèle de prompt avec contexte RAG
template = """
You are a friendly and knowledgeable travel assistant chatbot named Téranga Tour.
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
    llm = HuggingFaceEndpoint(huggingfacehub_api_token=api_token, repo_id=repo_id, task=task)
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "chat_history": chat_history,
        "user_question": user_query,
        "context": retrieved_info
    })
    return response.strip()

# Dictionnaire de lieux touristiques
lieux_touristiques = {
    "Île de Gorée": (14.6684, -17.3984),
    "Lac Rose": (14.8486, -17.2348),
    "Monument de la Renaissance Africaine": (14.7225, -17.4945),
    "Parc National du Djoudj": (16.5593, -16.2632),
    "Désert de Lompoul": (15.5455, -16.5269)
}

# Fonction pour générer une carte interactive
def generate_map(location_name):
    if location_name in lieux_touristiques:
        latitude, longitude = lieux_touristiques[location_name]
        m = folium.Map(location=[latitude, longitude], zoom_start=14)
        folium.Marker([latitude, longitude], popup=location_name).add_to(m)
        return m._repr_html_()
    return "No location found."

# Interface Gradio
def chatbot_interface(user_query, chat_history=[]):
    response = get_response(user_query, chat_history)
    chat_history.append((user_query, response))
    
    # Vérifier si l'utilisateur demande un lieu
    best_match, score = process.extractOne(user_query, list(lieux_touristiques.keys()))
    if score > 70:
        map_html = generate_map(best_match)
        return chat_history, map_html
    
    return chat_history, None

with gr.Blocks(theme="soft") as demo:
    gr.Markdown("""
    # 🌍 **Téranga Tour Chatbot** ✈️
    ## Votre assistant de voyage intelligent
    """)
    
    chatbot = gr.Chatbot(label="Chat avec Téranga Tour")
    user_input = gr.Textbox(placeholder="Posez votre question ici...")
    map_output = gr.HTML(label="Carte du lieu")
    submit_btn = gr.Button("Envoyer")
    
    submit_btn.click(fn=chatbot_interface, inputs=[user_input, chatbot], outputs=[chatbot, map_output])
    user_input.submit(fn=chatbot_interface, inputs=[user_input, chatbot], outputs=[chatbot, map_output])

demo.launch()