import json
import os
import asyncpg
from dotenv import load_dotenv
import chainlit as cl
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fuzzywuzzy import process
import aiohttp

# Charger les variables d'environnement
load_dotenv()
api_key_groq = os.getenv("GROQ_API_KEY")

# Charger les données du chatbot
with open("datasetchatbot.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

# Connexion à PostgreSQL
async def get_pg_connection():
    try:
        conn = await asyncpg.connect(
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database=os.getenv("PG_DATABASE"),
            host=os.getenv("PG_HOST"),
            port=int(os.getenv("PG_PORT"))
        )
        return conn
    except Exception as e:
        print(f"[ERREUR] Connexion PostgreSQL échouée : {e}")
        return None

# Charger un profil utilisateur depuis PostgreSQL
async def load_user_profile(user_id):
    conn = await get_pg_connection()
    if not conn:
        return None
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "lang": row["lang"],
                "preferences": row["preferences"],
                "budget": row["budget"]
            }
        return None
    except Exception as e:
        print(f"[ERREUR] lors de la lecture du profil : {e}")
        return None
    finally:
        await conn.close()

# Créer un profil utilisateur dans PostgreSQL
async def create_user_profile(user_id, name, lang="fr", preferences=None, budget="standard"):
    conn = await get_pg_connection()
    if not conn:
        return
    if preferences is None:
        preferences = []
    try:
        await conn.execute("""
            INSERT INTO users (id, name, lang, preferences, budget) 
            VALUES ($1, $2, $3, $4, $5)
        """, user_id, name, lang, preferences, budget)
    except Exception as e:
        print(f"[ERREUR] lors de la création du profil : {e}")
    finally:
        await conn.close()

# Obtenir le contexte du profil utilisateur
def get_user_profile():
    profile = cl.user_session.get("user_profile")
    if not profile:
        return {
            "name": "user_profile_context",
            "description": "Profil inconnu",
            "content": "Aucun profil utilisateur chargé."
        }
    content = f"Nom : {profile['name']}. Langue : {profile['lang']}. " \
              f"Préférences : {', '.join(profile['preferences'])}. Budget : {profile['budget']}."
    return {
        "name": "user_profile_context",
        "description": "Profil de l'utilisateur",
        "content": content
    }

# Recherche floue dans la base de connaissances
def retrieve_info(user_query):
    instructions = [entry["instruction"] for entry in knowledge_base]
    best_match, score = process.extractOne(user_query, instructions)
    if score > 70:
        for entry in knowledge_base:
            if entry["instruction"] == best_match:
                return entry["output"]
    return "Je n'ai pas trouvé d'information très précise dans mes données, mais je vais essayer de t'aider quand même !"

# Appel Nominatim pour géolocalisation
async def get_coordinates_from_place(place_name):
    url = f"https://nominatim.openstreetmap.org/search?q={place_name}&format=json"
    headers = {"User-Agent": "teranga-tour-bot"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    return None, None, None

# Prompt
template = """
You are a friendly and knowledgeable travel assistant chatbot named Téranga Tour. 
Use the following retrieved knowledge and user profile to enhance your answers, while keeping the conversation natural and engaging.

User Profile:
{user_profile}

Retrieved knowledge:
{context}

Chat history:
{chat_history}

User question:
{user_question}

Provide a well-structured and informative response, making it sound natural and conversational.
"""

prompt = ChatPromptTemplate.from_template(template)

# Modèle LLM
llm = ChatGroq(api_key=api_key_groq, model_name="llama-3.1-8b-instant")
chain = prompt | llm | StrOutputParser()

# Début de la conversation
@cl.on_chat_start
async def start():
    await cl.Message(content="Bienvenue sur Téranga Tour 🌍. Pour commencer, entre ton identifiant utilisateur :").send()
    cl.user_session.set("chat_history", [])
    cl.user_session.set("awaiting_user_id", True)

# Gestion des messages utilisateur
@cl.on_message
async def main(message: cl.Message):
    if cl.user_session.get("awaiting_user_id"):
        user_id = message.content.strip()
        user_profile = await load_user_profile(user_id)
        if user_profile:
            cl.user_session.set("user_profile", user_profile)
            cl.user_session.set("awaiting_user_id", False)
            await cl.Message(content=f"Bienvenue {user_profile['name']} ! 🎉 Tu peux me poser ta question maintenant.").send()
        else:
            cl.user_session.set("awaiting_name", True)
            cl.user_session.set("temp_user_id", user_id)
            cl.user_session.set("awaiting_user_id", False)  # Empêche répétition
            await cl.Message(content="Identifiant non trouvé 😕. Créons ton profil ! Quel est ton prénom ?").send()
        return

    if cl.user_session.get("awaiting_name"):
        name = message.content.strip()
        user_id = cl.user_session.get("temp_user_id") or "user_" + name.lower()
        await create_user_profile(user_id, name)
        cl.user_session.set("user_profile", {
            "id": user_id,
            "name": name,
            "lang": "fr",
            "preferences": [],
            "budget": "standard"
        })
        cl.user_session.set("awaiting_name", False)
        cl.user_session.set("awaiting_user_id", False)
        cl.user_session.set("temp_user_id", None)
        await cl.Message(content=f"Profil créé ! Bienvenue {name} ! 🎉 Tu peux maintenant poser ta question.").send()
        return

    # Traitement de la question
    user_query = message.content
    chat_history = cl.user_session.get("chat_history")

    if "où se trouve" in user_query.lower() or "localisation" in user_query.lower():
        lieu = user_query.replace("où se trouve", "").replace("localisation de", "").strip("? ")
        lat, lon, display_name = await get_coordinates_from_place(lieu)
        if lat and lon:
            map_url = f"https://www.google.com/maps?q={lat},{lon}"
            await cl.Message(content=f"📍 **{display_name}** se trouve ici : [Voir sur la carte]({map_url})").send()
            return

    context = retrieve_info(user_query)
    user_profile_context = get_user_profile()

    response = chain.invoke({
        "chat_history": chat_history,
        "user_question": user_query,
        "context": context,
        "user_profile": user_profile_context["content"]
    })

    chat_history.append(f"User: {user_query}")
    chat_history.append(f"Assistant: {response}")
    cl.user_session.set("chat_history", chat_history)

    await cl.Message(content=response).send()
