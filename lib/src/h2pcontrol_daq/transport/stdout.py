from __future__ import annotations

import json
from collections.abc import Sequence

from h2pcontrol_daq.models import DAQEvent
from h2pcontrol_daq.transport.base import Transport


class StdoutTransport(Transport):
    """Legacy compatibility transport that prints JSON to stdout."""

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def send_batch(self, events: Sequence[DAQEvent]) -> None:
        for event in events:
            print(json.dumps(event.to_wire_dict(), default=str))

    async def healthy(self) -> bool:
        return True
