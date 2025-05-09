import tkinter as tk
from tkinter import ttk
import logging
import requests

from messaging import ActuatorState
import common


def lightbulb_cmd(state, did):
    new_state = state.get()
    logging.info(f"Dashboard: {new_state}")

    # Lag et ActuatorState-objekt
    actuator_state = ActuatorState(
        actuator_id=did,
        value=new_state
    )

    try:
        # Send som JSON til sky-tjenesten
        response = requests.post(
            url=common.ACTUATOR_API_URL,
            json=actuator_state.__dict__,
            timeout=5
        )

        if response.status_code == 200:
            logging.info("Lyspærestatus sendt til sky-tjeneste")
        else:
            logging.error(f"Feil ved sending: {response.status_code} - {res_
