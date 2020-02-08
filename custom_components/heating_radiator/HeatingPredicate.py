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

    def get_deviation_scale(self) -> float:
        results = []
        for sensor in self._sensors:
            state = self._hass.states.get(sensor)
            if isinstance(state, State):
                try:
                    results.append(float(state.state))
                except ValueError:
                    pass
        if len(results) > 0:
            result = round((self._take(results) - self._target) / self._deviation, 2)
        else:
            result = 0
        _LOGGER.debug(f"Temperature deviation {result}")
        return result

    def __repr__(self):
        return f"HeatingPredicate(_sensors = {self._sensors}, _target = {self._target}, _deviation = {self._deviation})"