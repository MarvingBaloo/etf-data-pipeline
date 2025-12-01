# 1. On part d'une version légère de Python (comme installer Windows ou MacOS)
FROM python:3.9-slim

# 2. On crée un dossier de travail à l'intérieur du conteneur
WORKDIR /app

# 3. On copie nos fichiers (main.py, requirements.txt) de ton Mac vers le conteneur
COPY . /app

# 4. On installe les librairies listées dans requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. La commande à lancer quand le conteneur démarre
CMD ["python", "main.py"]