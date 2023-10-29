"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any, Coroutine

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
import logging

_LOGGER = logging.getLogger(__name__)


from .const import DOMAIN
from .api import UnifiAccessApi, UnifiAccessCoordinator, UnifiAccessDoor


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Binary Sensor for passed config entry"""
    api: UnifiAccessApi = hass.data[DOMAIN][config_entry.entry_id]

    coordinator = UnifiAccessCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        UnifiDoorLockEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data)
    )


class UnifiDoorLockEntity(CoordinatorEntity, LockEntity):
    def __init__(self, coordinator, idx) -> None:
        super().__init__(coordinator, context=idx)
        self.idx = idx
        door: UnifiAccessDoor = self.coordinator.data[idx]
        self._attr_unique_id = door.id
        self._attr_name = door.name
        self._attr_is_locked = door.is_locked
        self._attr_is_locking = door.is_locking
        self._attr_is_unlocking = door.is_unlocking

    @property
    def available(self) -> bool:
        return self.coordinator.data[self.idx].is_locked

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            model="UAH",
            manufacturer="Unifi",
        )

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock all or specified locks. A code to unlock the lock with may optionally be specified."""
        await self.hass.async_add_executor_job(self.coordinator.data[self.idx].unlock)

    def _handle_coordinator_update(self) -> None:
        self._attr_is_locked = self.coordinator.data[self.idx].is_locked
        self._attr_is_locking = self.coordinator.data[self.idx].is_locking
        self._attr_is_unlocking = self.coordinator.data[self.idx].is_unlocking
        self.async_write_ha_state()
