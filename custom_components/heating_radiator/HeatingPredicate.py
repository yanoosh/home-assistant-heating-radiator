import logging

from typing import List

from homeassistant.core import HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


class HeatingPredicate:
    def __init__(self, hass: HomeAssistant, sensors: List[str], take, target: float, deviation: float):
        self._hass = hass
        self._sensors = sensors
        self._take = take
        self._target = target
        self._deviation = deviation
        self.current_temperature = None
        self.target_temperature = None

    def get_deviation_scale(self, change: float = 0) -> float:
        self.target_temperature = self._target + change
        results = self._get_sensors_temperature()
        if len(results) > 0:
            self.current_temperature = self._take(results)
            result = round((self.current_temperature - self.target_temperature) / self._deviation, 2)
        else:
            result = 0
        _LOGGER.debug(f"Temperature deviation {result}")
        return result

    def _get_sensors_temperature(self):
        results = []
        for sensor in self._sensors:
            state = self._hass.states.get(sensor)
            if isinstance(state, State):
                try:
                    results.append(float(state.state))
                except ValueError:
                    pass
        return results

    def __repr__(self):
        return f"HeatingPredicate(" \
               f"_sensors = {self._sensors}, " \
               f"_take = {self._take}, " \
               f"_target = {self._target}, " \
               f"_deviation = {self._deviation})"
