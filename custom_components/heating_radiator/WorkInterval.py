import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


class WorkInterval:
    def __init__(self, duration: timedelta, minimum: timedelta, maximum: timedelta):
        self.tick_duration = 10
        self._total_cycles = round(duration.total_seconds() / self.tick_duration)
        self._minimum_work_cycles = round(minimum.total_seconds() / self.tick_duration)
        if maximum is None:
            self._maximum_work_cycles = self._total_cycles
        else:
            self._maximum_work_cycles = min(round(maximum.total_seconds() / self.tick_duration), self._total_cycles)

    def should_work(self, tick: int, deviation: float):
        if deviation > 0 and tick < self._maximum_work_cycles:
            return tick < min(
                max(round(self._maximum_work_cycles * deviation), self._minimum_work_cycles),
                self._maximum_work_cycles
            )
        else:
            return False

    def should_restart(self, tick):
        return not tick < self._total_cycles

    def __repr__(self):
        return f"WorkInterval(" \
               f"tick_duration = {self.tick_duration}, " \
               f"_total_cycles = {self._total_cycles}, " \
               f"_minimum_work_cycles = {self._minimum_work_cycles}) "
