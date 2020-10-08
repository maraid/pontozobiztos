"""Place for the scheduler singleton. Further functionality might be
added here later."""

from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()
scheduler.start()


def get_scheduler():
    return scheduler
