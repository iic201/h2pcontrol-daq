from __future__ import annotations

import asyncio
import contextlib
import time

from .config import DAQConfig, OverflowPolicy
from .metrics import LocalDAQStats
from .models import DAQEvent, PendingEvent
from .spool.disk import DiskSpool


class LocalDAQ:
    """
    Lightweight producer-side DAQ pipeline.

    Design goals:
    - keep the service hot path thin
    - serialize in a background task
    - write JSON locally
    """

    def __init__(self, config: DAQConfig):
        self.config = config
        self.stats = LocalDAQStats()

        self._ingress_q: asyncio.Queue[PendingEvent] = asyncio.Queue(
            maxsize=config.ingress_maxsize
        )
        self._outbound_q: asyncio.Queue[DAQEvent] = asyncio.Queue(
            maxsize=config.outbound_maxsize
        )
        self._tasks: list[asyncio.Task] = []
        self._stopping = False
        self._spool = DiskSpool(config.resolved_jsonl_path())

    async def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._serializer_loop(), name="daq-serializer"),
            asyncio.create_task(self._writer_loop(), name="daq-writer"),
        ]

    async def stop(self) -> None:
        self._stopping = True
        await self._ingress_q.join()
        await self._outbound_q.join()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    def publish(self, event: PendingEvent) -> None:
        self.stats.published += 1
        self._queue_put_now(self._ingress_q, event, self.config.ingress_overflow, "ingress")

    def _queue_put_now(
        self,
        q: asyncio.Queue,
        item,
        policy: OverflowPolicy,
        queue_name: str,
    ) -> None:
        if not q.full():
            q.put_nowait(item)
            return

        if queue_name == "ingress":
            counter_name = "dropped_ingress"
        else:
            counter_name = "dropped_outbound"

        if policy == OverflowPolicy.DROP_NEWEST:
            setattr(self.stats, counter_name, getattr(self.stats, counter_name) + 1)
            return

        if policy == OverflowPolicy.DROP_OLDEST:
            with contextlib.suppress(asyncio.QueueEmpty):
                q.get_nowait()
                q.task_done()
                setattr(self.stats, counter_name, getattr(self.stats, counter_name) + 1)
            q.put_nowait(item)
            return

        # BLOCK_WITH_TIMEOUT: schedule async put without blocking the caller too long.
        asyncio.create_task(self._put_with_timeout(q, item, counter_name))

    async def _put_with_timeout(self, q: asyncio.Queue, item, counter_name: str) -> None:
        try:
            await asyncio.wait_for(q.put(item), timeout=self.config.queue_put_timeout_s)
        except asyncio.TimeoutError:
            setattr(self.stats, counter_name, getattr(self.stats, counter_name) + 1)

    async def _serializer_loop(self) -> None:
        while True:
            pending = await self._get_or_stop(self._ingress_q, timeout=0.2)
            if pending is None:
                if self._stopping:
                    break
                continue

            try:
                payload = pending.serializer(pending.message)
                event = DAQEvent(
                    event_id=pending.event_id,
                    run_id=pending.run_id,
                    producer_id=pending.producer_id,
                    source=pending.source,
                    method=pending.method,
                    direction=pending.direction,
                    sequence=pending.sequence,
                    wall_time_ns=pending.wall_time_ns,
                    monotonic_ns=pending.monotonic_ns,
                    payload=payload,
                    quality=pending.quality,
                )
                self.stats.serialized += 1
                self._queue_put_now(
                    self._outbound_q,
                    event,
                    self.config.outbound_overflow,
                    "outbound",
                )
            except Exception:
                self.stats.serialization_errors += 1
            finally:
                self._ingress_q.task_done()

    async def _writer_loop(self) -> None:
        batch: list[DAQEvent] = []
        last_flush = time.monotonic()

        while True:
            event = await self._get_or_stop(self._outbound_q, timeout=0.1)
            if event is not None:
                batch.append(event)
                self._outbound_q.task_done()

            flush_due = (time.monotonic() - last_flush) >= self.config.batch_flush_s
            batch_full = len(batch) >= self.config.batch_max_events

            if batch and (flush_due or batch_full or (self._stopping and self._outbound_q.empty())):
                try:
                    await self._spool.append_many(batch)
                    self.stats.written += len(batch)
                except Exception:
                    self.stats.write_failures += 1
                finally:
                    batch.clear()
                    last_flush = time.monotonic()

            if self._stopping and self._outbound_q.empty() and not batch:
                break

    async def _get_or_stop(self, queue: asyncio.Queue, timeout: float) -> PendingEvent | DAQEvent | None:
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
