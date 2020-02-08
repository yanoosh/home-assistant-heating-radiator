"""
Automation for heating radiator
"""
import logging
# import time
import voluptuous as vol
from typing import Dict, List, Any, Union
from statistics import mean

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_MINIMUM,
    CONF_MAXIMUM,
    STATE_ON
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import script, condition
from homeassistant.helpers.script import Script
from homeassistant.core import HomeAssistant

from .HeatingRadiator import HeatingRadiator
from .HeatingPredicate import HeatingPredicate
from .WorkInterval import WorkInterval
from .PresenceSensor import PresenceSensor
from .Action import Action

DOMAIN = "heating_radiator"
CONF_TEMPERATURE = "temperature"
CONF_TAKE = "take"
CONF_TARGET = "target"
CONF_MAX_DEVIATION = "max_deviation"
CONF_WORK_INTERVAL = "work_interval"
CONF_DURATION = "duration"
CONF_SENSORS = "sensors"
CONF_SWITCH_ON = "switch_on"
CONF_SWITCH_OFF = "switch_off"
CONF_PRESENCE = "presence"

_LOGGER = logging.getLogger(__name__)


def entity_to_condition(value: Any) -> Union[Dict, Any]:
    if isinstance(value, str):
        return {
            "condition": "state",
            "entity_id": value,
            "state": STATE_ON
        }
    else:
        return value


PLACE_SCHEMA = vol.Schema({
    vol.Required(CONF_TEMPERATURE): {
        vol.Required(CONF_SENSORS): vol.All(
            cv.ensure_list,
            [cv.entity_id]
        ),
        vol.Optional(CONF_TAKE, default="mean"): vol.All(vol.Lower, vol.Any("min", "max", "mean")),
        vol.Required(CONF_TARGET): vol.Coerce(float),
        vol.Required(CONF_MINIMUM): vol.Coerce(float),
        vol.Optional(CONF_MAX_DEVIATION, default=2): vol.All(vol.Coerce(float), vol.Range(min=0))
    },
    vol.Optional(CONF_WORK_INTERVAL, default={}): {
        vol.Optional(CONF_DURATION, default="00:05:00"): cv.time_period,
        vol.Optional(CONF_MINIMUM, default="00:01:00"): cv.time_period,
        vol.Optional(CONF_MAXIMUM, default=None): cv.time_period
    },
    vol.Required(CONF_SWITCH_ON): cv.SCRIPT_SCHEMA,
    vol.Required(CONF_SWITCH_OFF): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_PRESENCE): vol.All(
        cv.ensure_list,
        [vol.Any(vol.All(cv.entity_id, entity_to_condition), cv.CONDITION_SCHEMA)]
    )
})

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: cv.schema_with_slug_keys(PLACE_SCHEMA)}, extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config):
    for place, placeConfig in config[DOMAIN].items():
        _LOGGER.debug("Detected place %s", place)
        heating_predicate = config_heating_predicate(hass, placeConfig[CONF_TEMPERATURE])
        work_interval = config_work_interval(placeConfig[CONF_WORK_INTERVAL])
        switch_on_actions = await config_action(
            hass, placeConfig[CONF_SWITCH_ON], place, CONF_SWITCH_ON
        )
        switch_off_actions = await config_action(
            hass, placeConfig[CONF_SWITCH_OFF], place, CONF_SWITCH_OFF
        )
        presence_sensors = await config_presence_sensors(
            hass, placeConfig[CONF_PRESENCE]
        )
        _LOGGER.debug(heating_predicate)
        _LOGGER.debug(work_interval)
        _LOGGER.debug(switch_on_actions)
        _LOGGER.debug(switch_off_actions)
        _LOGGER.debug(presence_sensors)

        heating_radiator = HeatingRadiator(
            hass, f"{DOMAIN}.{place}",
            heating_predicate,
            work_interval,
            switch_on_actions,
            switch_off_actions,
            presence_sensors
        )
        hass.add_job(heating_radiator.start)

    return True


def config_heating_predicate(hass: HomeAssistant, config: Dict) -> HeatingPredicate:
    if config[CONF_TAKE] == "min":
        take = min
    elif config[CONF_TAKE] == "max":
        take = max
    else:
        take = mean

    return HeatingPredicate(
        hass,
        config[CONF_SENSORS],
        take,
        config[CONF_TARGET],
        config[CONF_MAX_DEVIATION]
    )


def config_work_interval(config: Dict) -> WorkInterval:
    return WorkInterval(
        config[CONF_DURATION],
        config[CONF_MINIMUM],
        config[CONF_MAXIMUM]
    )


async def config_presence_sensors(hass: HomeAssistant, if_configs: Dict):
    checks = []
    for if_config in if_configs:
        try:
            checks.append(await condition.async_from_config(hass, if_config, False))
        except HomeAssistantError as ex:
            _LOGGER.warning("Invalid condition: %s", ex)
            return None

    return PresenceSensor(hass, checks)


async def config_action(hass: HomeAssistant, config: List, place: str, operation: str) -> Action:
    name = f"{DOMAIN}.{place}.{operation}"
    actions = []
    for action in config:
        action = await script.async_validate_action_config(hass, action)
        actions.append(action)

    return Action(
        Script(hass, actions, name),
        name
    )
