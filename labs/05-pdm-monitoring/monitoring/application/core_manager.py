import logging

class CoreManager:
    def __init__(self, data_manager, log_interval=50):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.message_count = 0
        self.log_interval = log_interval

    def process_message(self, payload):
        try:
            # 1. Salvataggio su InfluxDB
            self.data_manager.save_prediction(payload)
            self.message_count += 1

            # 2. Logica Alerting testuale (per i log del Pod)
            state = payload.get("state", "UNKNOWN")
            pump_id = payload.get("device_id", "unknown")

            if state in ["WARNING", "FAULTY", "BROKEN"]:
                self.logger.warning(f"🚨 ALERT: {pump_id} is {state}! Score: {payload.get('health_percent')}%")
            elif self.message_count % self.log_interval == 0:
                self.logger.info(f"📊 Stats: Processed {self.message_count} predictions. Last: {pump_id}")

        except Exception as e:
            self.logger.error(f"❌ Error in CoreManager: {e}")