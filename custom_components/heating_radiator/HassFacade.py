import logging
from typing import List, Optional

from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import script, condition
from homeassistant.helpers.script import Script

_LOGGER = logging.getLogger(__name__)


class HassFacade:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    def get_state(self, sensor: str) -> Optional[State]:
        return self._hass.states.get(sensor)

    async def create_action(self, domain:str, name: str, raw_config: List) -> ():
        actions = []
        for action in raw_config:
            action = await script.async_validate_action_config(self._hass, action)
            actions.append(action)

        script_runner = Script(self._hass, actions, name, domain)
        return lambda: self._run_script(script_runner)

    async def create_condition(self, name, raw_config) -> ():
        try:
            conditions = []
            for conditionConfig in raw_config:
                conditions.append(await condition.async_from_config(self._hass, conditionConfig, False))

            return lambda: all(check(self._hass) for check in conditions)
        except HomeAssistantError as ex:
            _LOGGER.warning("Invalid condition for %s: %s", name, ex)

    def _run_script(self, script_runner: Script):
        self._hass.async_create_task(script_runner.async_run())
