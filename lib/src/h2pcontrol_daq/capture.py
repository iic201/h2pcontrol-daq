from __future__ import annotations

import functools
import itertools
from collections.abc import Callable
from typing import Any

from .models import PendingEvent


def default_serializer(message: Any) -> dict[str, Any]:
    if hasattr(message, "to_dict"):
        return message.to_dict()
    if isinstance(message, dict):
        return message
    return {"value": repr(message)}


def capture(
    source: str,
    direction: str = "both",
    daq_attr: str = "daq",
    serializer: Callable[[Any], dict[str, Any]] | None = None,
):
    """
    Decorate an async service method.

    The decorated object must expose `self.<daq_attr>` and that object must be a
    `LocalDAQ` instance.

    Compared with the old pipeline, this decorator tries to keep the hot path
    smaller: it only creates a `PendingEvent` and enqueues it. The actual
    message-to-dict serialization happens in a background serializer task.
    """

    log_in = direction in ("in", "both")
    log_out = direction in ("out", "both")
    serializer_fn = serializer or default_serializer

    def decorator(func):
        counters: dict[str, itertools.count] = {}

        @functools.wraps(func)
        async def wrapper(self_svc, *args, **kwargs):
            daq = getattr(self_svc, daq_attr, None)
            if daq is None:
                print(f"Warning: {self_svc} has no attribute '{daq_attr}', skipping capture for {source}.{func.__name__}. Daq is NONE")
                return await func(self_svc, *args, **kwargs)

            key = f"{source}.{func.__name__}"
            if key not in counters:
                counters[key] = itertools.count()
            sequence = next(counters[key])

            if log_in and args:
                daq.publish(
                    PendingEvent(
                        run_id=daq.config.run_id,
                        producer_id=daq.config.producer_id,
                        source=source,
                        method=func.__name__,
                        direction="in",
                        sequence=sequence,
                        message=args[0],
                        serializer=serializer_fn,
                    )
                )

            try:
                result = await func(self_svc, *args, **kwargs)
            except Exception as exc:
                daq.publish(
                    PendingEvent(
                        run_id=daq.config.run_id,
                        producer_id=daq.config.producer_id,
                        source=source,
                        method=func.__name__,
                        direction="error",
                        sequence=sequence,
                        message={"error": repr(exc)},
                        serializer=serializer_fn,
                        quality=1,
                    )
                )
                raise

            if log_out:
                daq.publish(
                    PendingEvent(
                        run_id=daq.config.run_id,
                        producer_id=daq.config.producer_id,
                        source=source,
                        method=func.__name__,
                        direction="out",
                        sequence=sequence,
                        message=result,
                        serializer=serializer_fn,
                    )
                )

            return result

        return wrapper

    return decorator
