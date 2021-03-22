import requests
import fbchat
from webpreview import web_preview
import re
import logging

logger = logging.getLogger("chatbot")


def on_message(thread: fbchat.Group, author, message):
    if not message.text.startswith('https://'):
        return False

    client = fbchat.Client(session=thread.session)
    try:
        title, description, image_url = web_preview(
            message.text, parser='html.parser', timeout=2000,
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
        if match := re.search(r'^(https://[^/]+).*', message.text):
            image_url = match.group(1) + image_url
    r = requests.get(image_url)

    files = client.upload([("foobar.png", r.content, "image/png")])
    title = '*' + title + '*\n' if title else ''
    description = description + '\n' if description else ''

    thread.send_text(text=f'{title}{description}',
                     files=files,
                     reply_to_id=message.id)
    return True
