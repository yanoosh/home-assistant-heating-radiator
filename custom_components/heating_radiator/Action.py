import logging

from typing import Optional, Sequence

from homeassistant.core import Context
from homeassistant.helpers.script import Script

_LOGGER = logging.getLogger(__name__)


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