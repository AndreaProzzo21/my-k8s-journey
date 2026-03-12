FROM python:3.9-slim

WORKDIR /app

# Installazione dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Installazione librerie Python
COPY inference/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia dei modelli e del codice
COPY models/ /app/models/
COPY inference/src/ /app/src/

# PYTHONPATH serve a Python per trovare i tuoi moduli in /app/src
ENV PYTHONPATH="/app/src"

# Lancio dell'app (i parametri verranno dalle ENV di Kubernetes)
CMD ["python", "/app/src/main.py"]