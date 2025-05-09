import tkinter as tk
from tkinter import ttk

import logging
import requests

from messaging import SensorMeasurement
import common


def refresh_btn_cmd(temp_widget, did):
    logging.info("Temperature refresh")

    try:
        # Send forespørsel til sky-tjenesten for å hente temperatur
        response = requests.get(
            url=f"{common.SENSOR_API_URL}/{did}",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            # Forvent at data inneholder et felt som heter 'value'
            sensor_measurement = SensorMeasurement(value=data.get("value", "-273.15"))
            logging.info(f"Mottatt temperatur: {sensor_measurement.value}")
        else:
            logging.error(f"Feil ved henting: {response.status_code} - {response.text}")
