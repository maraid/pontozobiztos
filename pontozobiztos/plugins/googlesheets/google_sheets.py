
def init(client, database, scheduler):
    scheduler.add_job(
        update_sheets, 'cron', args=[client, database], minute='*/10')


def update_sheets(client, database):
    return