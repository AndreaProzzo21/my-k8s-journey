import paho.mqtt.client as mqtt
import time
import random
import os

# Allineamento con i nomi esatti della ConfigMap
BROKER_ADDRESS = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
TOPIC_BASE = os.getenv("MQTT_BASE_TOPIC", "factory/assembly")
SENSOR_ID = os.getenv("HOSTNAME", "generic-sensor")
INTERVAL = int(os.getenv("SENSOR_INTERVAL", 5))

print(f"--- Avvio Sensore: {SENSOR_ID} ---", flush=True)

client = mqtt.Client(SENSOR_ID)

def connect_to_broker():
    while True:
        try:
            print(f"Tentativo di connessione al broker: {BROKER_ADDRESS}...", flush=True)
            client.connect(BROKER_ADDRESS, 1883)
            print("Connesso!", flush=True)
            break
        except Exception as e:
            print(f"Broker non raggiungibile ({e}). Riprovo tra 5 secondi...", flush=True)
            time.sleep(5)

connect_to_broker()

while True:
    # Simulazione dati
    temp = round(random.uniform(20.0, 35.0), 2)
    vibration = round(random.uniform(0.1, 1.5), 2)
    
    payload = f'{{"id": "{SENSOR_ID}", "temp": {temp}, "vibr": {vibration}}}'
    # Costruzione topic: factory/assembly/nome-pod
    topic = f"{TOPIC_BASE}/{SENSOR_ID}"
    
    client.publish(topic, payload)
    print(f"Inviato a {topic}: {payload}", flush=True)
    
    time.sleep(INTERVAL)