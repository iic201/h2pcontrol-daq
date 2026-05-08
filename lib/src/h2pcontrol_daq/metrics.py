from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LocalDAQStats:
    published: int = 0
    serialized: int = 0
    written: int = 0
    dropped_ingress: int = 0
    dropped_outbound: int = 0
    serialization_errors: int = 0
    write_failures: int = 0
