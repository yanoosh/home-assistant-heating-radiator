"""heating radiator"""
import logging
from typing import Dict, Any, Union

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import (
    CONF_MINIMUM,
    CONF_MAXIMUM,
    STATE_ON
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .Action import Action
from .HeatingPredicate import HeatingPredicate
from .HeatingRadiator import HeatingRadiator
from .PresenceSensor import PresenceSensor
from .WorkInterval import WorkInterval

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'heating_radiator'

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
        vol.Optional(CONF_MINIMUM, default=None): vol.Any(vol.Coerce(float), None),
        vol.Optional(CONF_MAX_DEVIATION, default=2): vol.All(vol.Coerce(float), vol.Range(min=0))
    },
    vol.Optional(CONF_WORK_INTERVAL, default={}): {
        vol.Optional(CONF_DURATION, default="00:05:00"): cv.time_period,
        vol.Optional(CONF_MINIMUM, default="00:00:10"): cv.time_period,
        vol.Optional(CONF_MAXIMUM, default=None): vol.Any(cv.time_period, None)
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

async def async_setup(hass: HomeAssistant, config: Dict):
    hass.data[DOMAIN] = {}
    _LOGGER.debug(config[DOMAIN])
    hass.async_create_task(async_load_platform(hass, SENSOR_DOMAIN, DOMAIN, config[DOMAIN], config))

    return True
