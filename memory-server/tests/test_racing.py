import unittest
from racing import RacingRoom


class Socket:
    closed = False

    async def send_json(self, data):
        pass


class RacingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = RacingRoom()
        self.room.players = [Socket(), Socket()]

    async def startRace(self):
        await self.room.move(0, {"type": "ready"})
        self.room.advance(1)
        self.assertEqual(self.room.phase, "waiting")
        await self.room.move(1, {"type": "ready"})
        self.assertEqual(self.room.phase, "countdown")
        for _ in range(31):
            if self.room.phase == "racing":
                break
            self.room.advance(.1)
        self.assertEqual(self.room.phase, "racing")

    async def test_start_and_steering_validation(self):
        await self.room.move(0, {"type": "steer", "direction": -1})
        self.assertEqual(self.room.lanes, [1, 1])
        await self.startRace()
        for invalid in (True, "1", 0, 2, None):
            await self.room.move(0, {"type": "steer", "direction": invalid})
        self.assertEqual(self.room.lanes, [1, 1])
        await self.room.move(0, {"type": "steer", "direction": -1})
        await self.room.move(0, {"type": "steer", "direction": 1})
        self.assertEqual(self.room.lanes, [0, 1])
        self.room.advance(.2)
        await self.room.move(0, {"type": "steer", "direction": -1})
        self.assertEqual(self.room.lanes, [0, 1])

    async def test_collision_and_pause_resume(self):
        await self.startRace()
        self.room.obstacles = [{"distance": 3, "lane": 1}]
        self.room.lanes[1] = 0
        self.room.advance(.1)
        self.assertEqual(self.room.slow, [1.2, 0])
        self.room.advance(.1)
        self.assertLess(self.room.distances[0], self.room.distances[1])
        previous = self.room.distances.copy()
        self.room.players[1] = None
        self.room.ready[1] = False
        self.room.advance(.2)
        self.assertEqual(self.room.distances, previous)
        self.room.players[1] = Socket()
        self.room.advance(.2)
        self.assertEqual(self.room.distances, previous)
        await self.room.move(1, {"type": "ready"})
        self.room.advance(.2)
        self.assertGreater(self.room.distances[0], previous[0])

    async def test_finish_tie_and_rematch(self):
        await self.startRace()
        self.room.obstacles = []
        self.room.distances = [999, 999]
        self.room.advance(.1)
        self.assertEqual(self.room.phase, "finished")
        self.assertEqual(self.room.winners, [0, 1])
        await self.room.move(0, {"type": "restart"})
        self.assertEqual(self.room.phase, "waiting")
        self.assertEqual(self.room.ready, [False, False])
        self.assertEqual(self.room.distances, [0, 0])

    async def test_finish_order_within_same_tick(self):
        await self.startRace()
        self.room.obstacles = []
        self.room.distances = [998, 999]
        self.room.advance(.1)
        self.assertEqual(self.room.winners, [1])
        positions = self.room.distances.copy()
        self.room.advance(.2)
        self.assertEqual(self.room.distances, positions)

    async def test_restart_cannot_interrupt_race(self):
        await self.startRace()
        await self.room.move(1, {"type": "restart"})
        self.assertEqual(self.room.phase, "racing")


if __name__ == '__main__':
    unittest.main()
