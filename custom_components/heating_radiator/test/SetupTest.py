import asyncio
import unittest
from datetime import timedelta
from typing import List, Dict

from custom_components.heating_radiator import HeatingRadiator
from custom_components.heating_radiator.sensor import add_heating_radiator_to_hass
from custom_components.heating_radiator.test.HassFacadeStub import HassFacadeStub


class SetupTest(unittest.TestCase):
    devices: Dict[str, HeatingRadiator] = {}
    configuration = {
        "test_room0": {
            "temperature": {
                "sensors": ["input_number.temp0"],
                "target": 20,
                "max_deviation": 2,
                "take": "mean"
            },
            "work_interval": {
                "duration": timedelta(minutes=5),
                "minimum": timedelta(seconds=30),
                "maximum": timedelta(minutes=2),
                "warmup": timedelta(seconds=20),
            },
            "turn_on": [
                {
                    "service": "input_boolean.turn_on",
                    "entity_id": "input_boolean.device0"
                }
            ],
            "turn_off": [
                {
                    "service": "input_boolean.turn_off",
                    "entity_id": "input_boolean.device0"
                }
            ],
            "patches": []
            # "patches": [
            #     {
            #         "change": 2,
            #         "condition": [
            #             {"condition": "state", "entity_id": "input_boolean.test0", "state": "on"}
            #         ]
            #     },
            #     {
            #         "change": -10,
            #         "condition": [
            #             {"condition": "state", "entity_id": "input_boolean.test1", "state": "on"}
            #         ]
            #     }
            # ]
        }
    }
    loop = asyncio.new_event_loop()

    def setUp(self) -> None:
        self.hassFacade = HassFacadeStub()
        self.loop.run_until_complete(
            add_heating_radiator_to_hass(self.hassFacade, self._add_device, self.configuration)
        )

    def _add_device(self, entities: List[HeatingRadiator]):
        for entity in entities:
            self.devices[entity.name] = entity
