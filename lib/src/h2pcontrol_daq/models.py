from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Callable, Literal


class PayloadEncoding(StrEnum):
    JSON_DICT = "json_dict"


@dataclass(frozen=True, slots=True)
class PendingEvent:
    run_id: str
    producer_id: str
    source: str
    method: str
    direction: Literal["in", "out", "error"]
    sequence: int
    message: Any
    serializer: Callable[[Any], dict[str, Any]]
    wall_time_ns: int = field(default_factory=time.time_ns)
    monotonic_ns: int = field(default_factory=time.monotonic_ns)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    quality: int = 0


@dataclass(frozen=True, slots=True)
class DAQEvent:
    event_id: str
    run_id: str
    producer_id: str
    source: str
    method: str
    direction: Literal["in", "out", "error"]
    sequence: int
    wall_time_ns: int
    monotonic_ns: int
    payload: dict[str, Any]
    payload_encoding: PayloadEncoding = PayloadEncoding.JSON_DICT
    quality: int = 0

    def to_wire_dict(self) -> dict[str, Any]:
        return asdict(self)
