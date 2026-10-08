"""Server-authoritative race with a separate, shared two-player room."""
import asyncio
import random
import time


class RacingRoom:
    finishDistance = 1000

    def __init__(self):
        self.players = [None, None]
        self.reset()

    def reset(self):
        self.ready = [False, False]
        self.lanes = [1, 1]
        self.distances = [0.0, 0.0]
        self.slow = [0.0, 0.0]
        self.lastMove = [-1.0, -1.0]
        self.elapsed = 0.0
        self.countdown = 3.0
        self.phase = "waiting"
        self.winners = []
        self.obstacles = [{"distance": distance, "lane": random.randrange(3)}
                          for distance in range(100, self.finishDistance, 70)]

    def connected(self):
        return [s is not None and not s.closed for s in self.players]

    async def broadcast(self):
        for player, socket in enumerate(self.players):
            if socket is not None and not socket.closed:
                try:
                    await socket.send_json({
                        "player": player, "connected": self.connected(),
                        "ready": self.ready, "phase": self.phase,
                        "countdown": self.countdown, "lanes": self.lanes,
                        "distances": self.distances, "slow": self.slow,
                        "obstacles": self.obstacles, "finish": self.finishDistance,
                        "winners": self.winners,
                    })
                except ConnectionError:
                    pass

    async def move(self, player, data):
        action = data.get("type")
        if action == "ready":
            self.ready[player] = True
            if all(self.connected()) and all(self.ready) and self.phase == "waiting":
                self.phase = "countdown"
        elif action == "restart":
            # Both players must agree to start again via their ready buttons.
            if self.phase != "finished":
                return
            self.reset()
        elif action == "steer":
            direction = data.get("direction")
            if (self.phase != "racing" or not all(self.connected()) or not all(self.ready)
                    or type(direction) is not int or direction not in (-1, 1)
                    or self.elapsed - self.lastMove[player] < .12):
                return
            self.lanes[player] = max(0, min(2, self.lanes[player] + direction))
            self.lastMove[player] = self.elapsed
        else:
            return
        await self.broadcast()

    def advance(self, delta):
        if not all(self.connected()) or not all(self.ready):
            return
        if self.phase == "countdown":
            self.countdown = max(0, self.countdown - delta)
            if self.countdown == 0:
                self.phase = "racing"
            return
        if self.phase != "racing":
            return
        self.elapsed += delta
        finishTimes = []
        for player in range(2):
            previous = self.distances[player]
            speed = 12 if self.slow[player] > 0 else 30
            distance = previous + speed * delta
            self.slow[player] = max(0, self.slow[player] - delta)
            for obstacle in self.obstacles:
                if previous < obstacle["distance"] <= distance and self.lanes[player] == obstacle["lane"]:
                    self.slow[player] = 1.2
            self.distances[player] = min(self.finishDistance, distance)
            if distance >= self.finishDistance:
                finishTimes.append(((self.finishDistance - previous) / speed, player))
        if finishTimes:
            firstTime = min(t for t, _ in finishTimes)
            self.winners = [p for t, p in finishTimes if abs(t - firstTime) < .000001]
            self.phase = "finished"

    async def run(self):
        previous = time.monotonic()
        while True:
            await asyncio.sleep(.1)
            now = time.monotonic()
            self.advance(min(now - previous, .2))
            previous = now
            if any(self.connected()):
                await self.broadcast()
