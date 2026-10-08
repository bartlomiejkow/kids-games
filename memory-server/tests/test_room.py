"""Run with: python -m unittest discover -s tests (aiohttp required)."""
import asyncio
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("server", Path(__file__).parents[1] / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class Socket:
    closed = False

    def __init__(self):
        self.messages = []

    async def send_json(self, message):
        self.messages.append(message)


class RoomTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.room = server.Room()
        self.room.players = [Socket(), Socket()]
        self.room.cards = list(range(8)) * 2

    async def test_turn_validation_and_hidden_cards(self):
        await self.room.move(1, {"type": "flip", "index": 0})
        self.assertEqual(self.room.revealed, [])
        for index in [-1, 16, True, "0"]:
            await self.room.move(0, {"type": "flip", "index": index})
        self.assertEqual(self.room.revealed, [])
        await self.room.move(0, {"type": "flip", "index": 0})
        state = self.room.players[1].messages[-1]
        self.assertEqual(state["cards"], [0] + [None] * 15)
        await self.room.move(0, {"type": "flip", "index": 0})
        self.assertEqual(self.room.revealed, [0])

    async def test_match_and_completion(self):
        for index in range(8):
            await self.room.move(0, {"type": "flip", "index": index})
            await self.room.move(0, {"type": "flip", "index": index + 8})
        self.assertEqual(self.room.scores, [8, 0])
        self.assertEqual(self.room.turn, 0)
        self.assertTrue(self.room.players[0].messages[-1]["finished"])

    async def test_mismatch_and_restart(self):
        await self.room.move(0, {"type": "flip", "index": 0})
        await self.room.move(0, {"type": "flip", "index": 1})
        await self.room.move(0, {"type": "flip", "index": 2})
        self.assertEqual(self.room.revealed, [0, 1])
        await asyncio.sleep(1)
        self.assertEqual(self.room.turn, 1)
        self.assertEqual(self.room.revealed, [])
        await self.room.move(1, {"type": "flip", "index": 0})
        await self.room.move(1, {"type": "flip", "index": 1})
        await self.room.move(0, {"type": "restart"})
        await asyncio.sleep(1)
        self.assertEqual(self.room.turn, 0)
        self.assertEqual(self.room.revealed, [])
        self.assertEqual(self.room.scores, [0, 0])

    async def test_disconnected_player_pauses_game(self):
        self.room.players[1] = None
        await self.room.move(0, {"type": "flip", "index": 0})
        self.assertEqual(self.room.revealed, [])


if __name__ == "__main__":
    unittest.main()
