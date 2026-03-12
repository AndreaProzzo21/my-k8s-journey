import os
import logging
import time
from communication.mqtt.mqtt_fetcher import MQTTFetcher
from application.core_manager import CoreManager
from data.data_manager import DataManager


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MonitoringWorker")

def main():
    logger.info("🚀 Starting Monitoring Worker (Bridge MQTT -> InfluxDB)...")

    # 1. Configurazione da Environment Variables (K8s ConfigMap)
    mqtt_broker = os.getenv("MONITOR_MQTT_BROKER", "mosquitto-service")
    mqtt_port = int(os.getenv("MONITOR_MQTT_PORT", 1883))
    mqtt_topic = os.getenv("MONITOR_TOPIC", "factory/pumps/+/predictions")

    influx_url = os.getenv("INFLUX_URL", "http://influxdb-service:8086")
    influx_token = os.getenv("INFLUX_TOKEN")
    influx_org = os.getenv("INFLUX_ORG")
    influx_bucket = os.getenv("INFLUX_BUCKET")

    try:
        
        data_manager = DataManager(influx_url, influx_token, influx_org, influx_bucket)
        core_manager = CoreManager(data_manager)
        fetcher = MQTTFetcher(mqtt_broker, mqtt_port, mqtt_topic, core_manager)

        fetcher.start()
        logger.info(f"📡 Worker connected to broker {mqtt_broker} and listening...")

        while True:
            time.sleep(10)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        logger.info("🛑 Shutting down worker...")
        if 'data_manager' in locals():
            data_manager.close()

if __name__ == "__main__":
    main()