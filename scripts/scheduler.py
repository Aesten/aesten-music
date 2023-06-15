import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
loop = asyncio.get_event_loop()


def start():
    scheduler.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown()
        loop.close()


async def delete_message(message):
    if message is not None:
        await message.delete()


def schedule_delete(seconds, message):
    async def run_job():
        await asyncio.sleep(seconds)
        await delete_message(message)

    loop.create_task(run_job())
