from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import pathlib
import glob
from PIL import Image, UnidentifiedImageError
import imagehash
import logging
import re

log = logging.getLogger('chatbot.utils')


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
    try:
        image = Image.open(image_path)
    except UnidentifiedImageError:
        return ''
    if hashing_algorithm == 'phash':
        hash_ = str(imagehash.phash(image, **kwargs))
        log.info(f'Calculated hash for {image_path}: {hash_}')
        return hash_


def replace_mentions(message) -> str:
    replaced_text = message.text
    offset_correction = 0
    for mention in message.mentions:
        replaced_text = replaced_text[:(mention.offset + offset_correction)] \
                                      + str(mention.thread_id) \
                                      + replaced_text[(mention.offset
                                                       + offset_correction
                                                       + mention.length):]
        offset_correction += len(mention.thread_id) - mention.length
    log.debug(f'Original text: "{message.text}" '
              f'substituted text: "{replaced_text}"')
    return replaced_text


def parse_duration_to_expiration_date(duration):
    days = hours = minutes = 0

    match = re.search(r"(\d+)d", duration)
    if match is not None:
        days = int(match.group(1))

    match = re.search(r"(\d+)h", duration)
    if match is not None:
        hours = int(match.group(1))

    match = re.search(r"(\d+)m", duration)
    if match is not None:
        minutes = int(match.group(1))

    return datetime.today() + timedelta(days=days, hours=hours, minutes=minutes)

