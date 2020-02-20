from typing import List, Optional
from unittest.mock import MagicMock

from homeassistant.core import State

from custom_components.heating_radiator.HassFacade import HassFacade


class HassFacadeStub(HassFacade):

    def __init__(self):
        self.reset()

    def reset(self):
        self.states = {}
        self.actions = {}
        self.condition = MagicMock()

    def get_state(self, sensor: str) -> Optional[State]:
        return State(sensor, self.states[sensor])

    async def create_action(self, name: str, raw_config: List) -> ():
        self.actions[name] = MagicMock()
        return self.actions[name]

    async def create_condition(self, raw_config) -> ():
        return self.condition
