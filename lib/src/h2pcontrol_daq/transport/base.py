from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from h2pcontrol_daq.models import DAQEvent


class Transport(ABC):
    """Legacy transport interface kept for compatibility."""

    @abstractmethod
    async def open(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def send_batch(self, events: Sequence[DAQEvent]) -> None: ...

    @abstractmethod
    async def healthy(self) -> bool: ...
