"""One shared Memory room. Only the server decides turns and card matches."""
import asyncio
import json
import random
from aiohttp import web, WSMsgType
from racing import RacingRoom


class Room:
    def __init__(self):
        self.players = [None, None]
        self.pending = None
        self.reset()

    def reset(self):
        if self.pending:
            self.pending.cancel()
        self.pending = None
        self.cards = list("🐶🐱🦊🐸🐼🦁🐵🐧") * 2
        random.shuffle(self.cards)
        self.revealed = []
        self.matched = set()
        self.scores = [0, 0]
        self.turn = 0

    async def broadcast(self):
        for player, socket in enumerate(self.players):
            if socket is not None and not socket.closed:
                try:
                    await socket.send_json({
                        "player": player,
                        "connected": [s is not None and not s.closed for s in self.players],
                        "cards": [symbol if i in self.revealed or i in self.matched else None
                                  for i, symbol in enumerate(self.cards)],
                        "matched": sorted(self.matched), "scores": self.scores,
                        "turn": self.turn, "locked": len(self.revealed) == 2,
                        "finished": len(self.matched) == 16,
                    })
                except ConnectionError:
                    pass

    async def hide_pair(self):
        await asyncio.sleep(.9)
        self.revealed = []
        self.turn = 1 - self.turn
        self.pending = None
        await self.broadcast()

    async def move(self, player, data):
        if data.get("type") == "restart":
            self.reset()
        elif data.get("type") == "flip":
            index = data.get("index")
            if (not all(s is not None and not s.closed for s in self.players)
                    or player != self.turn or len(self.revealed) == 2
                    or type(index) is not int or not 0 <= index < 16
                    or index in self.matched or index in self.revealed):
                return
            self.revealed.append(index)
            if len(self.revealed) == 2:
                first, second = self.revealed
                if self.cards[first] == self.cards[second]:
                    self.matched.update(self.revealed)
                    self.revealed = []
                    self.scores[player] += 1
                else:
                    self.pending = asyncio.create_task(self.hide_pair())
        else:
            return
        await self.broadcast()


room = Room()
racingRoom = RacingRoom()


async def websocket(request):
    activeRoom = racingRoom if request.path == '/racing-ws' else room
    origin = request.headers.get("Origin")
    if origin and origin not in (f"http://{request.host}", f"https://{request.host}"):
        raise web.HTTPForbidden()
    socket = web.WebSocketResponse(heartbeat=20, max_msg_size=1024)
    await socket.prepare(request)
    if None not in activeRoom.players:
        await socket.send_json({"error": "Pokój jest pełny. Grają już dwie osoby."})
        await socket.close()
        return socket
    player = activeRoom.players.index(None)
    activeRoom.players[player] = socket
    await activeRoom.broadcast()
    try:
        async for message in socket:
            if message.type == WSMsgType.TEXT:
                try:
                    data = json.loads(message.data)
                except (ValueError, TypeError):
                    continue
                if isinstance(data, dict):
                    await activeRoom.move(player, data)
    finally:
        activeRoom.players[player] = None
        if isinstance(activeRoom, RacingRoom):
            activeRoom.ready[player] = False
        if all(s is None for s in activeRoom.players):
            activeRoom.reset()
        await activeRoom.broadcast()
    return socket


app = web.Application()
app.router.add_get('/memory-ws', websocket)
app.router.add_get('/racing-ws', websocket)


async def racingClock(app):
    task = asyncio.create_task(racingRoom.run())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app.cleanup_ctx.append(racingClock)
if __name__ == '__main__':
    web.run_app(app, port=8080)
