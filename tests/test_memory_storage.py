import unittest

from app.errors.storage import (
    StateAccessDeniedError,
    StateExpiredError,
    StateNotFoundError,
    StateStorageClosedError,
)
from app.models.media import TrackInfo
from app.storage.memory import MemoryStateStorage
from app.storage.models import TrackSelectionState


class FakeClock:
    def __init__(self) -> None:
        self.current = 100.0

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def make_state(title: str = "Track") -> TrackSelectionState:
    return TrackSelectionState((
        TrackInfo(
            title=title,
            artist="Artist",
            cover_url=None,
            duration_seconds=180,
        ),
    ))


class MemoryStateStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_and_get_state(self) -> None:
        storage = MemoryStateStorage()
        state = make_state()

        request_id = await storage.create(owner_id=10, payload=state)

        self.assertEqual(await storage.get(10, request_id), state)

    async def test_state_is_available_only_to_owner(self) -> None:
        storage = MemoryStateStorage()
        request_id = await storage.create(10, make_state())

        with self.assertRaises(StateAccessDeniedError):
            await storage.get(20, request_id)

    async def test_expired_state_is_removed(self) -> None:
        clock = FakeClock()
        storage = MemoryStateStorage(ttl_seconds=10, clock=clock)
        request_id = await storage.create(10, make_state())

        clock.advance(10)

        with self.assertRaises(StateExpiredError):
            await storage.get(10, request_id)
        with self.assertRaises(StateNotFoundError):
            await storage.get(10, request_id)

    async def test_oldest_user_state_is_evicted_at_limit(self) -> None:
        clock = FakeClock()
        storage = MemoryStateStorage(
            max_entries_per_user=2,
            clock=clock,
        )

        first = await storage.create(10, make_state("First"))
        clock.advance(1)
        second = await storage.create(10, make_state("Second"))
        clock.advance(1)
        third = await storage.create(10, make_state("Third"))

        with self.assertRaises(StateNotFoundError):
            await storage.get(10, first)
        self.assertEqual(await storage.get(10, second), make_state("Second"))
        self.assertEqual(await storage.get(10, third), make_state("Third"))

    async def test_delete_removes_state(self) -> None:
        storage = MemoryStateStorage()
        request_id = await storage.create(10, make_state())

        await storage.delete(10, request_id)

        with self.assertRaises(StateNotFoundError):
            await storage.get(10, request_id)

    async def test_close_clears_and_disables_storage(self) -> None:
        storage = MemoryStateStorage()
        request_id = await storage.create(10, make_state())

        await storage.close()
        await storage.close()

        with self.assertRaises(StateStorageClosedError):
            await storage.get(10, request_id)
        with self.assertRaises(StateStorageClosedError):
            await storage.create(10, make_state())


if __name__ == "__main__":
    unittest.main()
