import logging
from datetime import timedelta

from typing import List, Optional, Sequence

from homeassistant.const import (
    STATE_ON,
)
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.script import Script
from homeassistant.core import Context, HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


class HeatingPredicate:
    def __init__(self, hass:HomeAssistant, sensors: List[str], take, target: float, deviation: float):
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


class WorkInterval:
    def __init__(self, duration: timedelta, minimum: timedelta):
        self.tick_duration = 5
        self._total_cycles = round(duration.total_seconds() / self.tick_duration)
        self._minimum_work_cycles = round(minimum.total_seconds() / self.tick_duration)

    def should_work(self, tick: int, deviation: float):
        if deviation > 0:
            return tick < min(max(round(self._total_cycles * deviation), self._minimum_work_cycles), self._total_cycles)
        else:
            return False

    def should_restart(self, tick):
        return not tick < self._total_cycles

    def __repr__(self):
        return f"WorkInterval(" \
               f"tick_duration = {self.tick_duration}, " \
               f"_total_cycles = {self._total_cycles}, " \
               f"_minimum_work_cycles = {self._minimum_work_cycles}) "


class PresenceSensor:
    def __init__(self, hass: HomeAssistant, entity_id: str, on_state: str = STATE_ON):
        self._hass = hass
        self.entity_id = entity_id
        self.on_state = on_state

    def is_presence(self):
        return True

    def __repr__(self):
        return f"PresenceSensor(entity_id = {self.entity_id}, on_state = {self.on_state})"


class Action:
    def __init__(
            self,
            script: Script,
            name: str
    ) -> None:
        self._name = name
        self._script = script

    async def run(
            self,
            variables: Optional[Sequence] = None,  # todo is it required ?
            context: Optional[Context] = None  # todo is it required ?
    ) -> None:
        _LOGGER.info("Executing %s", self._name)
        try:
            await self._script.async_run(variables, context)
        except Exception as err:  # pylint: disable=broad-except
            self._script.async_log_exception(
                _LOGGER, f"Error while executing {self._name}", err
            )

    def __repr__(self):
        return f"Action(_name = {self._name}, _script = {self._script})"


class HeatingRadiator:
    def __init__(
            self,
            hass: HomeAssistant,
            name: str,
            heating_predicate: HeatingPredicate,
            work_interval: WorkInterval,
            switch_on_actions: Action,
            switch_off_actions: Action,
            presence_sensors=List[PresenceSensor]
    ):
        self._hass = hass
        self._name = name
        self._heating_predicate = heating_predicate
        self._work_interval = work_interval
        self._switch_on_actions = switch_on_actions
        self._switch_off_actions = switch_off_actions
        self._presence_sensors = presence_sensors
        self._tick = 0
        self._heaterEnabled = False

    async def start(self):
        # async_track_time_change
        async_track_time_change(self._hass, self._worker, second=f"/{self._work_interval.tick_duration}")
        _LOGGER.info(f"Started {self._name}")
        return True

    async def _worker(self, now):
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
