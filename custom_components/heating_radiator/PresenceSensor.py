from typing import List

from homeassistant.core import HomeAssistant


class PresenceSensor:
    def __init__(self, hass: HomeAssistant, checks: List):
        self._hass = hass
        if len(checks) > 0:
            self._check_algorithm = lambda: all(check(self._hass) for check in checks)
        else:
            self._check_algorithm = lambda: True

    def is_presence(self):
        return self._check_algorithm()

    def __repr__(self):
        return f"PresenceSensor(_check_algorithm = {self._check_algorithm})"