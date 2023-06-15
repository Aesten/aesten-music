from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()
scheduler.start()


def schedule_delete(message, seconds):
    def delete_message():
        if message is not None:
            message.delete()

    scheduler.add_job(delete_message, 'date', run_date=datetime.now() + timedelta(seconds=seconds))
