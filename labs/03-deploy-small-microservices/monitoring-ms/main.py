import paho.mqtt.client as mqtt
import os
import json
import sys
import time

# Forza l'output immediato
def log(msg):
    print(msg, flush=True)
    
BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "factory/assembly")
TOPIC_FILTER = f"{BASE_TOPIC}/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log(f"✅ Monitor connesso al broker: {BROKER}")
        client.subscribe(TOPIC_FILTER)
        log(f"📡 Sottoscritto al filtro: {TOPIC_FILTER}")
    else:
        log(f"❌ Connessione fallita con codice: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        # Estraiamo l'ID del sensore dal payload o dal topic
        sensor_id = data.get('id', 'unknown')
        id_breve = sensor_id[-5:] 
        
        log(f"📊 [DATA] Sensore: {id_breve} | Temp: {data['temp']}°C | Vibra: {data['vibr']}")
    except Exception as e:
        log(f"⚠️ Errore decodifica su {msg.topic}: {e}")

# Generiamo un ID unico basato sul timestamp per evitare conflitti se il Pod riavvia velocemente
client_id = f"monitor-service-{int(time.time())}"
client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message

log(f"🔄 Avvio monitor ({client_id})...")

client.connect(BROKER, 1883, 60)
client.loop_forever()