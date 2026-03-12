import time
import json
import random
import math
import os
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

class PumpSimulator:
    def __init__(self, pump_id, broker, port, base_topic, mode="NOMINAL"):
        self.pump_id = pump_id
        self.broker = broker
        self.port = port
        self.topic = f"{base_topic}/{pump_id}/telemetry"
        self.mode = mode

        # Data manutenzione fissa generata all'avvio
        random_days_ago = random.randint(10, 200)
        self.last_maintenance = (datetime.now() - timedelta(days=random_days_ago)).strftime("%Y-%m-%d")

        self._setup_mode_params()
        self.health_percent = 100.0
        self.cycle_count = 0

        self.baseline = {
            "temp": 38.0 + random.uniform(-2, 2),
            "current": 7.8 + random.uniform(-0.5, 0.5),
            "pressure": 4.2 + random.uniform(-0.3, 0.3),
            "rpm": 2850 + random.randint(-15, 15),
            "vib_x": 1.1, "vib_y": 0.7, "vib_z": 0.9
        }
        self.client = mqtt.Client(client_id=f"Sim-{pump_id}")

    def _setup_mode_params(self):
        if self.mode == "STRESS":
            self.total_life_cycles = random.randint(120, 200)
        elif self.mode == "ACCELERATED":
            self.total_life_cycles = random.randint(500, 800)
        else: # NOMINAL
            self.total_life_cycles = random.randint(8000, 12000)

    def update_degradation(self):
        self.cycle_count += 1
        life_consumed = min(self.cycle_count / self.total_life_cycles, 1.0)
        factor = pow(life_consumed, 2.5)
        self.health_percent = max(0.0, 100.0 * (1.0 - factor))

    def generate_data(self):
        wear_f = (100.0 - self.health_percent) / 100.0
        wear_vib = pow(wear_f, 2.0) * 10.0
        v_x = self.baseline["vib_x"] + random.uniform(-0.1, 0.1) + (wear_vib * 1.2)
        v_y = self.baseline["vib_y"] + random.uniform(-0.1, 0.1) + (wear_vib * 0.8)
        v_z = self.baseline["vib_z"] + random.uniform(-0.1, 0.1) + (wear_vib * 0.6)
        v_rms = math.sqrt(v_x**2 + v_y**2 + v_z**2)
        temp = self.baseline["temp"] + (wear_f * 40.0) + (v_rms * 0.3)
        curr = self.baseline["current"] + (wear_f * 5.0)
        pres = self.baseline["pressure"] - (wear_f * 1.5)
        rpm = self.baseline["rpm"] - int(wear_f * 50)
        
        # Aggiunta caos casuale
        if random.random() < 0.02: v_x += 10.0; v_rms += 8.0
        if random.random() < 0.01: temp += 15.0
        
        return v_x, v_y, v_z, v_rms, temp, curr, pres, rpm

    def run_step(self):
        v_x, v_y, v_z, v_rms, t, curr, p, rpm = self.generate_data()
        payload = {
            "measurement_id": self.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "device_id": self.pump_id,
            "vibration_x": round(v_x, 2),
            "vibration_y": round(v_y, 2),
            "vibration_z": round(v_z, 2),
            "vibration_rms": round(v_rms, 2),
            "temperature": round(t, 1),
            "current": round(curr, 2),
            "pressure": round(p, 2),
            "rpm": int(rpm),
            "health_percent": round(self.health_percent, 1),
            "last_maintenance": self.last_maintenance 
        }
        self.client.publish(self.topic, json.dumps(payload))

if __name__ == "__main__":
    # --- VARIABILI DA CONFIGMAP ---
    BROKER = os.getenv("MQTT_BROKER", "mosquitto-service")
    PORT = int(os.getenv("MQTT_PORT", 1883))
    MODE = os.getenv("SIMULATION_MODE", "NOMINAL")
    BASE_TOPIC = os.getenv("BASE_TOPIC", "factory/pumps")
    PUMPS_PER_POD = int(os.getenv("PUMPS_PER_POD", 2))
    INTERVAL = int(os.getenv("INTERVAL_SECONDS", 5))
    POD_NAME = os.getenv("HOSTNAME", "simulator-pod")

    print(f"🏗️  Starting Simulator on {POD_NAME} | Mode: {MODE} | Pumps: {PUMPS_PER_POD}")

    fleet = []
    for i in range(PUMPS_PER_POD):
        p_id = f"{POD_NAME}-P-{i+1:02d}"
        sim = PumpSimulator(p_id, BROKER, PORT, BASE_TOPIC, mode=MODE)
        try:
            sim.client.connect(BROKER, PORT)
            fleet.append(sim)
        except Exception as e:
            print(f"❌ Failed to connect {p_id}: {e}")

    while True:
        for sim in fleet:
            sim.update_degradation()
            sim.run_step()
            if sim.cycle_count % 50 == 0:
                print(f"📊 {sim.pump_id} Reporting: Health {sim.health_percent}%")
        time.sleep(INTERVAL)