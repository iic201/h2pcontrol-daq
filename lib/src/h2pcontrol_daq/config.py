from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OverflowPolicy(StrEnum):
    DROP_NEWEST = "drop_newest"
    DROP_OLDEST = "drop_oldest"
    BLOCK_WITH_TIMEOUT = "block_with_timeout"


@dataclass(slots=True)
class DAQConfig:
    producer_id: str
    run_id: str
    ingress_maxsize: int = 10_000
    outbound_maxsize: int = 10_000
    ingress_overflow: OverflowPolicy = OverflowPolicy.DROP_NEWEST
    outbound_overflow: OverflowPolicy = OverflowPolicy.DROP_NEWEST
    queue_put_timeout_s: float = 0.05
    batch_max_events: int = 250
    batch_flush_s: float = 0.25
    jsonl_path: str | None = None
    spool_path: str | None = None

    def resolved_jsonl_path(self) -> str:
        return self.jsonl_path or self.spool_path or "daq_events.jsonl"
