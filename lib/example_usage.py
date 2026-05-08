import asyncio

from h2pcontrol_daq import DAQConfig, LocalDAQ, capture


class Msg:
    def __init__(self, **data):
        self._data = data

    def to_dict(self):
        return self._data


class FakeService:
    def __init__(self, daq: LocalDAQ):
        self.daq = daq

    @capture(source="fake_scope", direction="both")
    async def acquire(self, message: Msg) -> Msg:
        await asyncio.sleep(0.01)
        return Msg(status="ok", points=1024)


async def main() -> None:
    daq = LocalDAQ(
        DAQConfig(
            producer_id="producer-1",
            run_id="run-001",
            jsonl_path="/tmp/daq_events.jsonl",
        ),
    )
    await daq.start()

    svc = FakeService(daq)
    await svc.acquire(Msg(channel=1, trigger="rising"))

    await asyncio.sleep(0.5)
    await daq.stop()
    print(daq.stats)


if __name__ == "__main__":
    asyncio.run(main())
