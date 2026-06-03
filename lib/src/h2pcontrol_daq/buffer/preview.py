from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any


@dataclass(slots=True)
class PreviewFrame:
    source: str
    producer_id: str
    timestamp: str
    data: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    sequence_id: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "producer_id": self.producer_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "sequence_id": self.sequence_id,
        }


class PreviewBuffer:
    def __init__(self, max_history: int = 100) -> None:
        self._lock = Lock()
        self._latest = {}
        self._history = {}
        self._sequence = {}
        self.max_history = max_history

    def update(
        self,
        source: str,
        producer_id: str,
        data: Any,
        metadata: dict[str, Any] | None = None,
    ) -> PreviewFrame:
        with self._lock:
            seq = self._sequence.get(source, 0) + 1
            self._sequence[source] = seq

            frame = PreviewFrame(
                source=source,
                producer_id=producer_id,
                timestamp=datetime.now().isoformat(),
                data=data,
                metadata=metadata or {},
                sequence_id=seq,
            )

            self._latest[source] = frame
            history = self._history.setdefault(source, [])
            history.append(frame)

            if len(history) > self.max_history:
                del history[0:len(history) - self.max_history]

            return frame

    def latest(self, source: str) -> PreviewFrame | None:
        with self._lock:
            return self._latest.get(source)

    def sources(self) -> list[str]:
        with self._lock:
            return list(self._latest.keys())

    def history(self, source: str, limit: int | None = None) -> list[PreviewFrame]:
        with self._lock:
            frames = list(self._history.get(source, []))
        if limit is None:
            return frames
        return frames[-limit:]
