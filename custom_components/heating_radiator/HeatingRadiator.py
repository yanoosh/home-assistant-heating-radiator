import logging

from homeassistant.helpers.event import async_track_time_change
from homeassistant.core import HomeAssistant

from .HeatingPredicate import HeatingPredicate
from .WorkInterval import WorkInterval
from .PresenceSensor import PresenceSensor
from .Action import Action

_LOGGER = logging.getLogger(__name__)


class HeatingRadiator:
    def __init__(
            self,
            hass: HomeAssistant,
            name: str,
            heating_predicate: HeatingPredicate,
            work_interval: WorkInterval,
            switch_on_actions: Action,
            switch_off_actions: Action,
            presence_sensor=PresenceSensor
    ):
        self._hass = hass
        self._name = name
        self._heating_predicate = heating_predicate
        self._work_interval = work_interval
        self._switch_on_actions = switch_on_actions
        self._switch_off_actions = switch_off_actions
        self._presence_sensor = presence_sensor
        self._tick = 0
        self._heaterEnabled = False

    async def start(self):
        async_track_time_change(self._hass, self._worker, second=f"/{self._work_interval.tick_duration}")
        _LOGGER.info(f"Started {self._name}")
        return True

    async def _worker(self, now):
        if self._tick == 0 and not self._presence_sensor.is_presence():
            _LOGGER.debug(f"{self._name} no presence skip")
            return

        deviation = self._heating_predicate.get_deviation_scale()
        if self._work_interval.should_work(self._tick, -deviation):
            if not self._heaterEnabled:
                self._heaterEnabled = True
                await self._switch_on_actions.run()
                _LOGGER.debug(f"{self._name} enabled")
        else:
            if self._heaterEnabled:
                self._heaterEnabled = False
                await self._switch_off_actions.run()
                _LOGGER.debug(f"{self._name} disabled")

        _LOGGER.debug(f"{self._name} tick: {self._tick}")
        if self._tick != 0 or self._heaterEnabled is True:
            self._tick += 1
            if self._work_interval.should_restart(self._tick):
                self._tick = 0
