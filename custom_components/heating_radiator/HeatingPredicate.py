import logging

from typing import List

from homeassistant.core import HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


class HeatingPredicate:
    def __init__(self, hass: HomeAssistant, sensors: List[str], take, target: float, minimum: float, deviation: float):
        self._hass = hass
        self._sensors = sensors
        self._take = take
        self._target = target
        self._minimum = minimum
        self._deviation = deviation

    def get_deviation_scale(self, presence: bool) -> float:
        temperature = self._minimum if presence else self._target
        results = self._get_sensors_temperature()
        if len(results) > 0:
            result = round((self._take(results) - temperature) / self._deviation, 2)
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
               f"_minimum = {self._minimum}, " \
               f"_deviation = {self._deviation})"