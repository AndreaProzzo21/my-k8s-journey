FROM python:3.9-slim

# 1. Imposta una cartella di lavoro
WORKDIR /app

# 2. Copia il file dei requisiti PRIMA del codice
COPY requirements.txt .

# 3. Installa usando il flag -r (CORREZIONE QUI)
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia lo script
COPY sensor.py .

CMD ["python", "main.py"]

