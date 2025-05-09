import logging
import threading
import time
import requests

from messaging import ActuatorState
import common


class Actuator:

    def __init__(self, did):
        self.did = did
        self.state = ActuatorState('False')
        self.running = True

    def simulator(self):
        logging.info(f"Actuator {self.did} starting")

        while self.running:
            logging.info(f"Actuator {self.did}: {self.state.state}")
            time.sleep(common.LIGHTBULB_SIMULATOR_SLEEP_TIME)

    def client(self):
        logging.info(f"Actuator Client {self.did} starting")

        while self.running:
            try:
                response = requests.get(
                    url=f"{common.ACTUATOR_API_URL}/{self.did}",
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    new_state = data.get("value", "False")
                    self.state = ActuatorState(new_state)
                    logging.info(f"[CLIENT] Oppdatert tilstand: {self.state.state}")
                else:
                    logging.error(f"[CLIENT] Feil {response.status_code}: {response.text}")

            except requests.RequestException as e:
                logging.error(f"[CLIENT] HTTP-feil: {e}")

            time.sleep(common.LIGHTBULB_CLIENT_SLEEP_TIME)

        logging.info(f"Client {self.did} finishing")

    def run(self):
        threading.Thread(target=self.simulator, daemon=True).start()
        threading.Thread(target=self.client, daemon=True).start()



