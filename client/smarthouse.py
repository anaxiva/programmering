import threading
import time
import requests
import logging

from messaging import ActuatorState
import common


class Actuator:
    def __init__(self, actuator_id):
        self.actuator_id = actuator_id
        self.state = None
        self.running = True

    def simulator(self):
        """Simulerer lyspærestatus endringer lokalt."""
        while self.running:
            logging.info(f"[SIMULATOR] Aktuatorstatus: {self.state}")
            time.sleep(5)

    def client(self):
        """Henter tilstand fra sky-tjenesten i et passende intervall."""
        while self.running:
            try:
                response = requests.get(
                    url=f"{common.ACTUATOR_API_URL}/{self.actuator_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self.state = data.get("value", "Unknown")
                    logging.info(f"[CLIENT] Hentet tilstand: {self.state}")
                else:
                    logging.error(f"[CLIENT] Feil {response.status_code}: {response.text}")
            except requests.RequestException as e:
                logging.error(f"[CLIENT] HTTP-feil: {e}")

            time.sleep(10)  # Juster intervall som passer

    def run(self):
        """Starter tråder for simulator og klient."""
        sim_thread = threading.Thread(target=self.simulator, daemon=True)
        client_thread = threading.Thread(target=self.client, daemon=True)

        sim_thread.start()
        client_thread.start()



