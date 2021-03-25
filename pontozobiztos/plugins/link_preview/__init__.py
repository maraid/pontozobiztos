import requests
import fbchat
from webpreview import web_preview
import re
import logging
import ytmusicapi

logger = logging.getLogger("chatbot")

MAX_RETRIES = 3

youtube = ytmusicapi.YTMusic()

def upload_with_retries(client, image):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return client.upload([("foobar.png", image, "image/png")])
        except fbchat.HTTPError:
            logger.error('Failed to upload image. Retrying...')
            retries += 1


def get_ytvideo_length(url):
    if match := re.search(r'(youtube\.com/watch\?.*v=([^&]+)|youtu\.be/([^?]+))', url):
        video_id = match.groups()[1]
        try:
            duration_in_s = int(youtube.get_song(video_id)['lengthSeconds'])
        except KeyError:
            logger.info('Couldn\'t retrieve YouTube video with url: ' + url)
            return ''
        hours = int(duration_in_s / (60 * 60))
        minutes = int((duration_in_s % 3600) / 60)
        seconds = int(duration_in_s % 60)
        sec_str = ('0' if seconds < 10 else '') + str(seconds)
        return ':'.join([(hours or ''), str(minutes), sec_str]).strip(':')
    return ''


def on_message(thread: fbchat.Group, author, message):
    if match := re.search(r'(https://[^\s]*)', message.text):
        url = match.group(1)
        logger.info('Extracted url: ' + url)
        client = fbchat.Client(session=thread.session)
        try:
            title, description, image_url = web_preview(
                url, parser='html.parser', timeout=2000,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'})
        except requests.exceptions.InvalidURL:
            return False
        except requests.exceptions.Timeout:
            return True

        logger.info(f'Fetched preview. Title: "{title}".'
                    f' Description: "{description}"'
                    f' Image URL: "{image_url}"')

        if not (title and image_url):
            logger.debug(f'Incorrect preview data.')
            return False

        if image_url.startswith('/'):
            if match := re.search(r'^(https://[^/]+).*', url):
                image_url = match.group(1) + image_url
        r = requests.get(image_url)

        files = upload_with_retries(client, r.content)
        title = '*' + title + '*\n' if title else ''
        duration = get_ytvideo_length(url)
        description = 'Időtartam: ' + duration + '\n' if description else ''

        # thread.send_text(text=f'{title}',
        thread.send_text(text=f'{title}{description}',
                         files=files,
                         reply_to_id=message.id)
        return True
