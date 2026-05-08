from __future__ import annotations

import asyncio
import json
from pathlib import Path

from h2pcontrol_daq.models import DAQEvent


class DiskSpool:
    """
    Tiny JSONL writer for local event persistence.

    This is deliberately simple. Good enough for a first version and easy to
    reason about in a thesis.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    async def append_many(self, events: list[DAQEvent]) -> None:
        await asyncio.to_thread(self._append_many_sync, events)

    def _append_many_sync(self, events: list[DAQEvent]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event.to_wire_dict(), default=str) + "\n")
