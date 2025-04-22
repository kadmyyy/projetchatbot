import json
import os
from dotenv import load_dotenv
import chainlit as cl
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fuzzywuzzy import process

# Charger les variables d'environnement
load_dotenv()
api_key_groq = os.getenv("GROQ_API_KEY")

# Charger les données
with open("datasetchatbot.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

# Définir le prompt avec RAG
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

# Fonction de récupération via fuzzy matching
def retrieve_info(user_query):
    instructions = [entry["instruction"] for entry in knowledge_base]
    best_match, score = process.extractOne(user_query, instructions)
    if score > 70:
        for entry in knowledge_base:
            if entry["instruction"] == best_match:
                return entry["output"]
    return "I couldn't find relevant information in my database, but I can still try to help!"

# Configuration du LLM (Groq)
llm = ChatGroq(
    api_key=api_key_groq,
    model_name="llama-3.1-8b-instant"
)

chain = prompt | llm | StrOutputParser()

@cl.on_chat_start
async def start():
    await cl.Message(
        content="Hello! I'm Téranga Tour 🌍, your travel assistant. How can I help you today?"
    ).send()
    cl.user_session.set("chat_history", [])

@cl.on_message
async def main(message: cl.Message):
    user_query = message.content
    chat_history = cl.user_session.get("chat_history")

    # Récupération de contexte depuis la base
    context = retrieve_info(user_query)

    # Appel du modèle
    response = chain.invoke({
        "chat_history": chat_history,
        "user_question": user_query,
        "context": context
    })

    # Mise à jour de l'historique
    chat_history.append(f"User: {user_query}")
    chat_history.append(f"Assistant: {response}")
    cl.user_session.set("chat_history", chat_history)

    await cl.Message(content=response).send()
