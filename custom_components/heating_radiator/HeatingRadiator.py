import logging
from typing import Any, Dict

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant

from .HeatingPredicate import HeatingPredicate
from .Patches import Patches
from .WorkInterval import WorkInterval
from .Action import Action

_LOGGER = logging.getLogger(__name__)


class HeatingRadiator(Entity):
    def __init__(
            self,
            hass: HomeAssistant,
            name: str,
            heating_predicate: HeatingPredicate,
            work_interval: WorkInterval,
            switch_on_actions: Action,
            switch_off_actions: Action,
            patches: Patches
    ):
        self._hass = hass
        self._name = name
        self._heating_predicate = heating_predicate
        self._work_interval = work_interval
        self._switch_on_actions = switch_on_actions
        self._switch_off_actions = switch_off_actions
        self._patchs = patches
        self._tick = 0
        self._heater_enabled = False
        self._deviation = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return "heating" if self._heater_enabled else "idle"

    @property
    def state_attributes(self) -> Dict[str, Any]:
        return {
            "deviation": self._deviation,
            "current_temperature": self._heating_predicate.current_temperature,
            "target_temperature": self._heating_predicate.target_temperature,
            "target_temperature_patch": self._target_temperature_patch,
        }

    async def async_update(self):
        # https://developers.home-assistant.io/docs/en/entity_index.html
        await self._worker()

    async def _worker(self):
        self._target_temperature_patch = self._patchs.get_change()
        self._deviation = self._heating_predicate.get_deviation_scale(
            self._target_temperature_patch
        )
        if self._work_interval.should_work(self._tick, -self._deviation):
            if not self._heater_enabled:
                self._heater_enabled = True
                await self._switch_on_actions.run()
                _LOGGER.debug(f"{self._name} enabled")
        else:
            if self._heater_enabled:
                self._heater_enabled = False
                await self._switch_off_actions.run()
                _LOGGER.debug(f"{self._name} disabled")

        _LOGGER.debug(f"{self._name} tick: {self._tick}")
        if self._tick != 0 or self._heater_enabled is True:
            self._tick += 1
            if self._work_interval.should_restart(self._tick):
                self._tick = 0
