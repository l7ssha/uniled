"""UniLED Channel."""
from __future__ import annotations
from collections.abc import Callable
from typing import Any

from .attributes import UniledAttribute
from .const import UNILED_CHANNEL as CHANNEL, ATTR_UL_POWER

import logging

_LOGGER = logging.getLogger(__name__)


##
## UniLED Channel Status Class
##
class UniledStatus:
    """UniLED Channel Status Class"""

    _channel: UniledChannel
    _status: dict(str, Any)

    def __init__(self, channel: UniledChannel, status: dict(str, Any) = {}) -> None:
        self._channel = channel
        self._status = status

    def __getattr__(self, attr):
        if str(attr).startswith("_"):
            if attr in self.__dict__:
                return self.__dict__[attr]
            raise AttributeError(attr)
        elif attr in self._status:
            return self._status[attr]
        return None

    def __setattr__(self, attr, value):
        if str(attr).startswith("_"):
            self.__dict__[attr] = value
        else:
            self.set(attr, value)

    def get(self, attr: str, default: Any = None) -> Any:
        """Get a single status attribute"""
        if attr in self._status:
            return self._status[attr]
        return default

    def set(self, attr: str, value: Any, always: bool = False) -> None:
        """Set a single status attribute"""
        if always or not value == None:
            self._status[attr] = value
        else:
            self._status.pop(attr, None)

    def has(self, attr: str) -> bool:
        """Does a single status attribute exist"""
        return True if attr in self._status else False

    def replace(self, status: dict(str, Any), refresh: bool = False) -> None:
        """Replace the status attributes"""
        self._status = status
        if refresh:
            _LOGGER.debug("%s: Status replace: %s", self._channel.title, self._status)
            self.refresh()

    def update(self, status: dict(str, Any), refresh: bool = False) -> None:
        """Update the status attributes"""
        self._status.update(status)
        if refresh:
            _LOGGER.debug("%s: Status replace: %s", self._channel.title, self._status)
            self.refresh()

    def refresh(self) -> None:
        """Refresh the channel"""
        self._channel.refresh()

    def dump(self) -> dict:
        """Get the status dictionary"""
        return self._status

##
## UniLED Channel Class
##
class UniledChannel:
    """UniLED Channel Class"""

    _number: int = 0
    _status: UniledStatus
    _features: list[UniledAttribute] = []
    _callbacks: list[Callable[[UniledChannel], None]] = []
    _context: Any

    def __init__(self, number: int) -> None:
        self._number = number
        self._status = UniledStatus(self)
        _LOGGER.debug("Inititalized: %s", self.title)

    def __del__(self):
        self._status = None
        self._callbacks.clear()
        _LOGGER.debug("Deleted: %s", self.title)

    @property
    def is_on(self) -> bool:
        """Is the channel on or off"""
        return self.get(ATTR_UL_POWER, False)

    @property
    def name(self) -> str:
        """Returns the channel name."""
        return self.title

    @property
    def title(self) -> str:
        """Returns the channel title."""
        return f"{CHANNEL} {self.number}"

    @property
    def number(self) -> int:
        """Returns the channel name."""
        return self._number

    @property
    def status(self) -> UniledStatus:
        """Returns the channel status."""
        return self._status

    @status.setter
    def status(self, status: dict(str, Any)):
        """Set the channels status."""
        self._status.replace(status, True)

    @property
    def features(self) -> list[UniledAttribute]:
        """Get the channels feature list."""
        return self._features

    @features.setter
    def features(self, value: list[UniledAttribute]):
        """Set the channels feature list."""
        self._features = value

    @property
    def context(self) -> Any:
        """Get the channels feature list."""
        return self._context

    @context.setter
    def context(self, value: Any):
        """Set the channels feature list."""
        self._context = value

    def get(self, attr: str, default: Any = None) -> Any:
        """Get a single status attribute"""
        return self._status.get(attr, default)

    def set(self, attr: str, value: Any, refresh: bool = False) -> None:
        """Set a single status attribute"""
        self._status.set(attr, value)
        if refresh:
            self.refresh()

    def has(self, attr: str) -> bool:
        """Does a single status attribute exist"""
        return self._status.has(attr)

    def refresh(self) -> None:
        """Refresh channels status."""
        _LOGGER.debug("%s: Refresh", self.title)
        self._fire_callbacks()

    def register_callback(
        self, callback: Callable[[UniledChannel], None]
    ) -> Callable[[], None]:
        """Register a callback to be called when the state changes."""

        def unregister_callback() -> None:
            self._callbacks.remove(callback)

        self._callbacks.append(callback)
        return unregister_callback

    def _fire_callbacks(self) -> None:
        """Fire the callbacks."""
        for callback in self._callbacks:
            callback(self)
