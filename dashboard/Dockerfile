FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Streamlit fonctionne sur le port 8501 par défaut
EXPOSE 8501

# La commande pour lancer le site web
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]