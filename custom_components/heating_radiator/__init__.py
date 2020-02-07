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
    CONF_ENTITY_ID,
    CONF_STATE,
    CONF_MINIMUM,
    STATE_ON
)
from homeassistant.helpers import script
from homeassistant.helpers.script import Script
from homeassistant.core import HomeAssistant

from .HeatingRadiator import PresenceSensor, HeatingRadiator, Action, HeatingPredicate, WorkInterval

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
CONF_PRESENCE_SENSORS = "presence_sensors"

_LOGGER = logging.getLogger(__name__)


def entity_to_condition(value: Any) -> Union[Dict, Any]:
    if isinstance(value, str):
        return {
            "platform": "state",
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
        vol.Optional(CONF_MAX_DEVIATION, default=2): vol.All(vol.Coerce(float), vol.Range(min=0))
    },
    vol.Optional(CONF_WORK_INTERVAL, default={}): {
        vol.Optional(CONF_DURATION, default="00:05:00"): cv.time_period,
        vol.Optional(CONF_MINIMUM, default="00:01:00"): cv.time_period
    },
    vol.Required(CONF_SWITCH_ON): cv.SCRIPT_SCHEMA,
    vol.Required(CONF_SWITCH_OFF): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_PRESENCE_SENSORS): vol.All(cv.ensure_list, entity_to_condition, [cv.CONDITION_SCHEMA])
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
        presence_sensors = config_presence_sensors(
            placeConfig[CONF_PRESENCE_SENSORS]
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
        config[CONF_MINIMUM]
    )


def config_presence_sensors(config: Dict):
    if isinstance(config, list):
        presence_sensors_config = config
    else:
        presence_sensors_config = [config]
    presence_sensors = []
    for sensor in presence_sensors_config:
        if isinstance(sensor, dict):
            presence_sensors.append(PresenceSensor(
                sensor[CONF_ENTITY_ID], sensor[CONF_STATE]
            ))
        else:
            presence_sensors.append(PresenceSensor(sensor))

    return presence_sensors


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
