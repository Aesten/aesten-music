import threading
import asyncio


async def _schedule_delete(seconds, message):
    await asyncio.sleep(seconds)
    await message.delete()


def delete_after(seconds, message):
    asyncio.run_coroutine_threadsafe(_schedule_delete(seconds, message), asyncio.get_event_loop())
