"""UniLED Update Coordinator."""
from __future__ import annotations

import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UNILED_UPDATE_SECONDS, UNILED_REFRESH_DELAY
from .lib.device import UniledDevice

import logging

_LOGGER = logging.getLogger(__name__)


class UniledUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to gather data for a specific UniLED device."""

    def __init__(
        self, hass: HomeAssistant, device: UniledDevice, entry: ConfigEntry
    ) -> None:
        """Initialize DataUpdateCoordinator to gather data for specific device."""
        self.device: UniledDevice = device
        self.lock = asyncio.Lock()
        self.title = entry.title
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=f"{self.device.name}",
            update_method=self._async_update,
            update_interval=timedelta(seconds=UNILED_UPDATE_SECONDS),
            # We don't want an immediate refresh since the device
            # takes a moment to reflect the state change
            #request_refresh_debouncer=Debouncer(
            #    hass, _LOGGER, cooldown=UNILED_REFRESH_DELAY, immediate=False
            #),
        )

    def __del__(self):
        """Destroy the class"""
        _LOGGER.debug("Coordinator destroyed")

    async def _async_update(self) -> None:
        """Fetch all device and sensor data from api."""

        if self.entry.state == ConfigEntryState.NOT_LOADED:
            if self._listeners:
                _LOGGER.warning("Still have listeners: %s", self._listeners)

        async with self.lock:
            try:
                valid_states = (
                    ConfigEntryState.LOADED,
                    ConfigEntryState.SETUP_IN_PROGRESS,
                    ConfigEntryState.SETUP_RETRY,
                )

                if self.entry.state in valid_states:
                    if not await self.device.update():
                        raise UpdateFailed("Update failed")
                    return
                if self.device.available:
                    _LOGGER.debug("%s: Forcing stop", self.device.name)
                    await self.device.stop()
                raise UpdateFailed(f"{self.device.name}: Invalid entry state!")
            except Exception as ex:
                raise UpdateFailed(str(ex)) from ex
    