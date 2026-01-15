import asyncio
import websockets

USERS = set()

async def broadcast(msg):
    if USERS:
        print(f"Broadcast to {len(USERS)} clients: {msg}")
        await asyncio.gather(*(u.send(msg) for u in USERS))

async def handler(ws):
    USERS.add(ws)
    print(f"Client connected. Total: {len(USERS)}")
    try:
        async for msg in ws:
            await broadcast(msg)
    finally:
        USERS.remove(ws)
        print(f"Client disconnected. Total: {len(USERS)}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket server running on ws://127.0.0.1:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
