from datetime import timedelta


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