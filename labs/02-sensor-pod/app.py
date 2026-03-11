from fastapi import FastAPI
import os
import random
import time

app = FastAPI()

# Leggiamo la config dalle variabili d'ambiente (ConfigMap)
SENSOR_NAME = os.getenv("SENSOR_NAME", "generic-sensor")
LOG_PATH = "/data/sensor_readings.log"

@app.get("/health")
def health_check():
    # Liveness: Se il file system non è scrivibile, il sensore è "rotto"
    if not os.access("/data", os.W_OK):
        return {"status": "unhealthy"}, 500
    return {"status": "alive"}

@app.get("/data")
def get_data():
    reading = random.uniform(20.0, 30.0)
    with open(LOG_PATH, "a") as f:
        f.write(f"{time.ctime()}: {reading}\n")
    return {"sensor": SENSOR_NAME, "value": reading}