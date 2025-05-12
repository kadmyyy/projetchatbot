# Dockerfile

# Image de base
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY . /app

# Installer les dépendances
RUN pip install --upgrade pip && pip install -r requirements.txt

# Exposer le port utilisé par Chainlit
EXPOSE 8000

# Lancer l'app avec Chainlit
CMD ["chainlit", "run", "app.py", "-w"]
