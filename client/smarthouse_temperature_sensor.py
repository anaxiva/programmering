import logging
import threading
import time
import math
import requests

from messaging import SensorMeasurement
import common


class Sensor:

    def __init__(self, did):
        self.did = did
        self.measurement = SensorMeasurement('0.0')
        self.running = True

    def simulator(self):
        logging.info(f"Sensor {self.did} starting")
        while self.running:
            temp = round(math.sin(time.time() / 10) * common.TEMP_RANGE, 1)
            logging.info(f"Sensor {self.did}: {temp}")
            self.measurement.set_temperature(str(temp))
            time.sleep(common.TEMPERATURE_SENSOR_SIMULATOR_SLEEP_TIME)

    def client(self):
        logging.info(f"Sensor Client {self.did} starting")
        while self.running:
            try:
                payload = {
                    "sensor_id": self.did,
                    "value": self.measurement.value
                }
                response = requests.post(
                    url=common.SENSOR_API_URL,
                    json=payload,
                    timeout=5
                )
                if response.status

