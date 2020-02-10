"""
Automation for heating radiator
"""
import logging
from datetime import timedelta
from statistics import mean
# import time
from typing import Dict, List

from homeassistant.const import (
    CONF_MINIMUM,
    CONF_MAXIMUM
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import script, condition
from homeassistant.helpers.script import Script

from . import DOMAIN, CONF_TEMPERATURE, CONF_TAKE, CONF_TARGET, CONF_MAX_DEVIATION, CONF_WORK_INTERVAL, CONF_DURATION, \
    CONF_SENSORS, CONF_SWITCH_ON, CONF_SWITCH_OFF, CONF_PRESENCE
from .Action import Action
from .HeatingPredicate import HeatingPredicate
from .HeatingRadiator import HeatingRadiator
from .PresenceSensor import PresenceSensor
from .WorkInterval import WorkInterval

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_platform(hass: HomeAssistant, config, async_add_devices, discovery_info=None):
    if not discovery_info:
        return

    entities = []
    for place, placeConfig in discovery_info.items():
        _LOGGER.debug("Detected place %s", place)
        _LOGGER.debug("Place config %s", placeConfig)
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
            hass,
            f"{DOMAIN}_{place}",
            heating_predicate,
            work_interval,
            switch_on_actions,
            switch_off_actions,
            presence_sensors
        )
        entities.append(heating_radiator)

    async_add_devices(entities)
    return True


def config_heating_predicate(hass: HomeAssistant, config: Dict) -> HeatingPredicate:
    if config[CONF_TAKE] == "min":
        take = min
    elif config[CONF_TAKE] == "max":
        take = max
    else:
        take = mean
    _LOGGER.debug(str(config))
    return HeatingPredicate(
        hass,
        config[CONF_SENSORS],
        take,
        config[CONF_TARGET],
        config[CONF_MINIMUM],
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
