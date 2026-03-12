import json
from datetime import datetime
import logging

logger = logging.getLogger("InferenceManager")

class InferenceManager:
    def __init__(self, predictor, mqtt_client=None):
        self.predictor = predictor
        self.mqtt_client = mqtt_client
        self.message_counter = 0 

    def process_data(self, data):
        self.message_counter += 1
        pump_id = data.get('device_id', 'unknown_device')
        
        # Esecuzione Inferenza
        prediction = self.predictor.predict(data)
        
        if prediction:
            data['state_pred'] = prediction['state']
            data['health_score_pred'] = prediction['health']
            data['is_ai_prediction'] = True 
        else:
            return

        data['inference_timestamp'] = datetime.now().isoformat()
        
        # Logging strategico
        if data['state_pred'] != "HEALTHY":
            logger.warning(f"🚨 ALERT: [{pump_id}] State: {data['state_pred']} | Score: {data['health_score_pred']}%")
        elif self.message_counter % 100 == 0:
            logger.info(f"✅ Stream OK: {self.message_counter} inferenze elaborate.")

        # Rilancio su MQTT per Monitoring/Grafana
        if self.mqtt_client:
            output_topic = f"factory/predictions/{pump_id}"
            self.mqtt_client.publish(output_topic, json.dumps(data))