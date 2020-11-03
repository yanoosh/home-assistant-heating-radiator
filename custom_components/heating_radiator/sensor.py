"""
Automation for heating radiator
"""
import logging
from datetime import timedelta
from statistics import mean
from typing import Dict, List, Callable, Optional

from homeassistant.const import (
    CONF_MINIMUM,
    CONF_MAXIMUM,
    CONF_CONDITION)
from homeassistant.core import HomeAssistant

from . import DOMAIN, CONF_TEMPERATURE, CONF_TAKE, CONF_TARGET, CONF_MAX_DEVIATION, CONF_WORK_INTERVAL, CONF_DURATION, \
    CONF_SENSORS, CONF_TURN_ON, CONF_TURN_OFF, CONF_CHANGE, CONF_PATCHES, CONF_WARMUP
from .HassFacade import HassFacade
from .HeatingPredicate import HeatingPredicate
from .HeatingRadiator import HeatingRadiator
from .Patches import Patch, Patches, PatchesEmpty
from .WorkInterval import WorkInterval

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_platform(hass: HomeAssistant, config, async_add_devices, discovery_info=None):
    return await add_heating_radiator_to_hass(HassFacade(hass), async_add_devices, discovery_info)


async def add_heating_radiator_to_hass(hass_facade: HassFacade, async_add_devices, discovery_info: Optional[Dict]):
    if not discovery_info or not discovery_info["devices"]:
        return
    entities = []
    for place, placeConfig in discovery_info["devices"].items():
        _LOGGER.debug("Detected place %s", place)
        _LOGGER.debug("Place config %s", placeConfig)
        heating_predicate = config_heating_predicate(hass_facade, placeConfig[CONF_TEMPERATURE])
        work_interval = config_work_interval(placeConfig[CONF_WORK_INTERVAL])
        turn_on_actions = await config_action(
            hass_facade, placeConfig[CONF_TURN_ON], place, CONF_TURN_ON
        )
        turn_off_actions = await config_action(
            hass_facade, placeConfig[CONF_TURN_OFF], place, CONF_TURN_OFF
        )
        patches = await config_patches(
            hass_facade, placeConfig[CONF_PATCHES], discovery_info[CONF_PATCHES]
        )
        _LOGGER.debug(heating_predicate)
        _LOGGER.debug(work_interval)
        _LOGGER.debug(turn_on_actions)
        _LOGGER.debug(turn_off_actions)
        _LOGGER.debug(patches)

        heating_radiator = HeatingRadiator(
            f"{DOMAIN}_{place}",
            heating_predicate,
            work_interval,
            turn_on_actions,
            turn_off_actions,
            patches,
            SCAN_INTERVAL,
            timedelta(minutes=30),
            timedelta(minutes=1)
        )
        entities.append(heating_radiator)
    async_add_devices(entities)
    return True


def config_heating_predicate(hass_facade: HassFacade, config: Dict) -> HeatingPredicate:
    if config[CONF_TAKE] == "min":
        take = min
    elif config[CONF_TAKE] == "max":
        take = max
    else:
        take = mean
    _LOGGER.debug(str(config))
    return HeatingPredicate(
        hass_facade,
        config[CONF_SENSORS],
        take,
        config[CONF_TARGET],
        config[CONF_MAX_DEVIATION]
    )


def config_work_interval(config: Dict) -> WorkInterval:
    return WorkInterval(
        config[CONF_DURATION],
        config[CONF_MINIMUM],
        config[CONF_MAXIMUM],
        config[CONF_WARMUP],
        SCAN_INTERVAL
    )


async def config_patches(hass_facade: HassFacade, config: Dict, config_global: Dict) -> Patches:
    patches = []
    for name, patch_config in config.items():
        if not isinstance(patch_config, Dict):
            if name in config_global:
                patch_config = config_global[name]
            else:
                _LOGGER.warning("Global patch %s does not exist.", name)
                continue
        conditions = await hass_facade.create_condition(name, patch_config[CONF_CONDITION])
        patches.append(Patch(patch_config[CONF_CHANGE], conditions))

    if len(patches) > 0:
        return Patches(patches)
    else:
        return PatchesEmpty()


async def config_action(hass_facade: HassFacade, config: List, place: str, operation: str) -> Callable:
    name = f"{DOMAIN}.{place}.{operation}"
    return await hass_facade.create_action(DOMAIN, name, config)
