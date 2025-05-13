FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Installation des dépendances
RUN pip install --upgrade pip \
    && pip install streamlit chainlit \
    && pip install -r requirements.txt

# Vérifier que streamlit est installé (ligne temporaire pour debug)
RUN which streamlit && streamlit --version

# Exposer les ports
EXPOSE 8501

# Commande de lancement
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
