class SensorMeasurement:
    def __init__(self, value):
        self.value = value

    def set_temperature(self, temp):
        self.value = temp


class ActuatorState:
    def __init__(self, actuator_id, value):
        self.actuator_id = actuator_id
        self.value = value

