from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import pathlib
import glob
from PIL import Image
import imagehash
import logging

log = logging.getLogger('chatbot')


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


def get_saved_image_path(attachment_id):
    """Generates a list of paths for a message object where the images
    are (or will be) stored

    Args:
        attachment_id (str):
    Returns:
        pathlib.Path: List of paths of images in message
    """
    img_dir = pathlib.Path(os.getenv("IMAGE_DIRECTORY"))
    image_matches = [x for x in glob.glob(str(img_dir) + '/*a' + attachment_id + '*')]
    if (li := len(image_matches)) != 1:
        raise FileNotFoundError(f'Found {li} images with attachment id: {attachment_id}. Expected 1')
    return pathlib.Path(image_matches[0])


def hash_image(image_path: str, hashing_algorithm='phash', **kwargs) -> str:
    image = Image.open(image_path)
    if hashing_algorithm == 'phash':
        hash_ = imagehash.phash(image, **kwargs)
        log.info(f'Calculated hash for {image_path}: {hash_}')
        return hash_

