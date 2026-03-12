from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions

class DataManager:
    def __init__(self, url, token, org, bucket):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.bucket = bucket
        self.write_api = self.client.write_api(write_options=WriteOptions(
            batch_size=50,
            flush_interval=5_000
        ))

    def save_prediction(self, data: dict):
        """Converte il JSON dell'Inference in un punto InfluxDB"""
        point = Point("pump_diagnostics") \
            .tag("device_id", data.get("device_id", "unknown")) \
            .field("state", data.get("state", "UNKNOWN")) \
            .field("health_score", float(data.get("health_percent", 0.0))) \
            .field("vibration_rms", float(data.get("vibration_rms", 0.0))) \
            .field("temperature", float(data.get("temperature", 0.0))) \
            .field("pressure", float(data.get("pressure", 0.0)))
        
        self.write_api.write(bucket=self.bucket, record=point)

    def close(self):
        if self.client:
            self.client.close()