import json
import logging
import time
from paho.mqtt import client as mqtt_client

logger = logging.getLogger("InferenceFetcher")

class MQTTPumpFetcher:
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic
        # Generiamo un Client ID univoco per evitare conflitti se scaliamo l'Inference
        self.client = mqtt_client.Client(client_id=f"inference-service-{int(time.time())}")
        self._setup_callbacks()

    def _setup_callbacks(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info(f"✅ Connesso al Broker MQTT ({self.broker})")
                # IMPORTANTE: Subscribe qui dentro garantisce che venga rifatta 
                # automaticamente in caso di riconnessione
                client.subscribe(self.topic)
                logger.info(f"📡 Subscription attiva su: {self.topic}")
            else:
                logger.error(f"❌ Connessione fallita, codice: {rc}")

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                logger.warning("⚠️ Disconnessione inaspettata dal broker. Tentativo di riconnessione...")

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

    def start(self, callback_function):
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                callback_function(payload)
            except Exception as e:
                logger.error(f"⚠️ Errore decodifica JSON: {e}")

        self.client.on_message = on_message
        
        # Gestione errori di connessione iniziale
        connected = False
        while not connected:
            try:
                self.client.connect(self.broker, self.port, keepalive=60)
                connected = True
            except Exception as e:
                logger.error(f"⌛ Broker non raggiungibile ({e}). Riprovo tra 5s...")
                time.sleep(5)

        
        self.client.loop_forever()