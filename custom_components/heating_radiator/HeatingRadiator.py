import logging
from datetime import timedelta
from typing import Any, Dict, Callable

from homeassistant.helpers.entity import Entity

from .HeatingPredicate import HeatingPredicate
from .Patches import Patches
from .WorkInterval import WorkInterval

STATE_HEATING = "heating"
STATE_PAUSE = "pause"
STATE_IDLE = "idle"

_LOGGER = logging.getLogger(__name__)


class HeatingRadiator(Entity):
    _state = STATE_IDLE
    _tick = 0
    _last_change_tick = 0
    _heater_enabled = False
    _deviation = None
    _target_temperature_patch = None
    _should_warmup = False
    _repeatAction = 2

    def __init__(
            self,
            name: str,
            heating_predicate: HeatingPredicate,
            work_interval: WorkInterval,
            turn_on_actions: Callable,
            turn_off_actions: Callable,
            patches: Patches,
            tick_period: timedelta,
            cooldown_period: timedelta,
            confirm_period: timedelta = timedelta(seconds=60),
    ):
        self._name = name
        self._heating_predicate = heating_predicate
        self._work_interval = work_interval
        self._turn_on_actions = turn_on_actions
        self._turn_off_actions = turn_off_actions
        self._patches = patches
        self._cooldown_ticks = round(cooldown_period.seconds / tick_period.seconds, 0)
        self._confirm_period = round(confirm_period.seconds / tick_period.seconds, 0)

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return self._state

    @property
    def state_attributes(self) -> Dict[str, Any]:
        return {
            "deviation": self._deviation,
            "current_temperature": self._heating_predicate.current_temperature,
            "target_temperature": self._heating_predicate.target_temperature,
            "target_temperature_patch": self._target_temperature_patch,
            "tick": self._tick,
            "sleep_tick": self._last_change_tick,
            "should_warmup": self._should_warmup,
        }

    async def async_update(self):
        await self._worker()

    async def _worker(self):
        self._target_temperature_patch = self._patches.get_change()
        self._deviation = self._heating_predicate.get_deviation_scale(
            self._target_temperature_patch
        )
        work_state = self._work_interval.should_work(self._tick, -self._deviation, self._should_warmup)
        if work_state != self._heater_enabled:
            self._last_change_tick = 0
            self._heater_enabled = work_state
            self._repeatAction = 2
            _LOGGER.debug("%s change state to %s", self._name, self._heater_enabled)

        if (self._last_change_tick % self._confirm_period) == 0 or self._last_change_tick == 1:
            _LOGGER.debug("%s turn %s, last change %s", self._name, self._heater_enabled, self._last_change_tick)
            if self._heater_enabled:
                self._state = STATE_HEATING
                if (self._repeatAction > 0):
                    self._turn_on_actions()
                    self._repeatAction -= 1
            else:
                self._state = STATE_PAUSE
                if (self._repeatAction > 0):
                    self._turn_off_actions()
                    self._repeatAction -= 1

        _LOGGER.debug(f"{self._name} tick: {self._tick}")
        self._last_change_tick += 1
        if self._tick != 0 or self._heater_enabled:
            self._tick += 1
            if self._work_interval.should_restart(self._tick):
                self._should_warmup = self._last_change_tick > self._cooldown_ticks
                self._tick = 0
        else:
            self._state = STATE_IDLE
            self._should_warmup = self._last_change_tick > self._cooldown_ticks
