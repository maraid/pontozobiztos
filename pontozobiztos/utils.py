from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_season_start():
    """Calculates season start (10th day 20:00)

    :returns: date of season start
    :rtype: datetime
    """
    today = datetime.today()
    start_rd = relativedelta(day=10, hour=20, minute=0, second=0, microsecond=0)
    from_date = today + start_rd
    if from_date < datetime.today():
        return from_date
    else:
        return from_date + relativedelta(months=-1)


def get_season_end():
    """Calculates season end (10th day 20:00)

    :returns: date of season end
    :rtype: datetime
    """
    today = datetime.today()
    start_rd = relativedelta(day=10, hour=19, minute=50, second=0, microsecond=0)
    to_date = today + start_rd
    if to_date > today:
        return to_date
    else:
        return to_date + relativedelta(months=1)


def get_current_season():
    """Returns a tuple containing the start and end
    of the current season.

    :returns: (season_start, season_end)
    :rtype: tuple(datetime, datetime)
    """
    return get_season_start(), get_season_end()


def get_later_datetime(days, hours, minutes, seconds=0):
    """Calculates a date displaced by the parameters relative to now.
     All parameters can be both negative and positive.

     :param days: days displacement
     :type days: int
     :param hours: hours displacement
     :type hours: int
     :param minutes: minutes displacement
     :type minutes: int
     :param seconds: seconds displacement
     :type seconds: int
     :returns: a datetime object relative to now.
     :rtype: datetime
     """
    today = datetime.today()
    dt = relativedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return today + dt


def get_monogram(name):
    return '.'.join(n[0] for n in name.split(' ')) + '.'