import logging
from datetime import timedelta
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class WorkInterval:
    def __init__(self, duration: timedelta, minimum: timedelta, maximum: timedelta, warmup: Optional[timedelta], tick_duration: timedelta):
        self._tick_duration = tick_duration.seconds
        self._total_cycles = round(duration.total_seconds() / self._tick_duration)
        self._minimum_work_cycles = round(minimum.total_seconds() / self._tick_duration)
        self._warmup_cycles = 0 if warmup is None else round(warmup.total_seconds() / self._tick_duration)
        if maximum is None:
            self._maximum_work_cycles = self._total_cycles
        else:
            self._maximum_work_cycles = min(round(maximum.total_seconds() / self._tick_duration), self._total_cycles)

    def should_work(self, tick: int, deviation: float, should_warmup: bool):
        if deviation > 0 and tick < self._maximum_work_cycles:
            calculate_cycles = round(self._maximum_work_cycles * deviation) + (self._warmup_cycles if should_warmup else 0)
            return tick < min(max(calculate_cycles, self._minimum_work_cycles), self._maximum_work_cycles)
        else:
            return False

    def should_restart(self, tick):
        return not tick < self._total_cycles

    def __repr__(self):
        return f"WorkInterval(" \
               f"tick_duration = {self._tick_duration}, " \
               f"_total_cycles = {self._total_cycles}, " \
               f"_minimum_work_cycles = {self._minimum_work_cycles}) "
