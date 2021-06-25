from fbchat import Message, GroupData
from pontozobiztos.models.User import User

from fbchat import GroupData
import fbchat
import requests
from pontozobiztos.plugins.link_mirror import Converter

import logging
log = logging.getLogger("chatbot")

MAX_RETRIES = 3


def upload_with_retries(client, file, ftype):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            if ftype == 'png':
                return client.upload([("foobar.png", file, 'image/png')])
            elif ftype == 'mp3':
                return client.upload([("foobar.mp3", file, 'audio/mpeg')])
        except fbchat.HTTPError:
            log.error('Failed to upload image. Retrying...')
            retries += 1


def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """

    if not message.text.startswith('https://'):
        return False

    client = fbchat.Client(session=message.thread.session)

    try:
        converted_uris, album_cover, preview_url = \
            Converter.extract_track_info(message.text)
        log.info(f'Successfully converted {message.text}. '
                 f'Results: {converted_uris}')
    except Converter.InnenTudodHogyJoException as e:
        message.thread.send_text(str(e), reply_to_id=message.id)
        log.info(f'Link: {message.text} detected as music, '
                 f'but could not be converted.')
        return True
    except Converter.PluginException as e:
        log.info(f'Could not convert {message.text}. Reason: {e}')
        return False

    fb_album = []
    if album_cover:
        album_cover_file = requests.get(album_cover).content
        fb_album = upload_with_retries(client, album_cover_file, 'png')

    fb_preview = []
    if preview_url:
        preview_url_file = requests.get(preview_url).content
        fb_preview = upload_with_retries(client, preview_url_file, 'mp3')

    msg_text = '\n\n'.join(converted_uris)
    log.debug(f'Sending URL: {msg_text}')
    files = fb_album + fb_preview
    message.thread.send_text(text=msg_text, files=files)
    return True
