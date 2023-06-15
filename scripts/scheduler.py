import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()


def start():
    scheduler.start()


async def delete_message(message):
    if message is not None:
        await message.delete()


def schedule_delete(s, message):
    async def run_job():
        await asyncio.sleep(s)
        await delete_message(message)

    scheduler.add_job(lambda: asyncio.ensure_future(run_job()), 'date', run_date=datetime.now() + timedelta(seconds=s))
