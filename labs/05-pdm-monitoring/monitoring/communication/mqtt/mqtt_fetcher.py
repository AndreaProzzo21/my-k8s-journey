import paho.mqtt.client as mqtt
import json
import logging

class MQTTFetcher:
    def __init__(self, broker, port, topic, core_manager):
        self.logger = logging.getLogger(__name__)
        self.broker = broker
        self.port = port
        self.topic = topic
        self.core_manager = core_manager
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info(f"✅ Connected to Broker")
            self.client.subscribe(self.topic)
        else:
            self.logger.error(f"❌ Connection failed: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.core_manager.process_message(payload)
        except Exception as e:
            self.logger.error(f"❌ Decode error: {e}")

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()