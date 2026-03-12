import os
import logging
import warnings
from predictor import PumpPredictor
from mqtt_fetcher import MQTTPumpFetcher
from inference_manager import InferenceManager

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")

def main():
    logger.info("🚀 Avvio Inference Service (Stateless Mode)")

    broker = os.getenv("MQTT_BROKER", "mosquitto-service")
    port = int(os.getenv("MQTT_PORT", 1883))
    input_topic = os.getenv("MQTT_INPUT_TOPIC", "factory/pumps/+/telemetry")
    model_dir = os.getenv("MODEL_DIR", "/app/models")

    try:
        predictor = PumpPredictor(model_dir)
        fetcher = MQTTPumpFetcher(broker, port, input_topic)
        
        manager = InferenceManager(
            predictor=predictor, 
            mqtt_client=fetcher.client
        )
        
        logger.info(f"📡 Subscription: {input_topic}")
        fetcher.start(callback_function=manager.process_data)
        
    except Exception as e:
        logger.error(f"❌ Errore: {e}")

if __name__ == "__main__":
    main()