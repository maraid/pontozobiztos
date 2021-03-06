import requests
import fbchat
from webpreview import web_preview
import re


def on_message(thread: fbchat.Group, author, message):
    if not message.text.startswith('https://') or \
       message.text.startswith('https://facebook.com') or \
       message.text.startswith('https://www.facebook.com') or \
       message.text.startswith('https://m.facebook.com') or \
       message.text.startswith('https://music.youtube.com'):
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

    if image_url is not None:
        if image_url.startswith('/'):
            if match := re.search(r'^(https://[^/]+).*', message.text):
                image_url = match.group(1) + image_url
        r = requests.get(image_url)
        files = client.upload([("placeholder.png", r.content, "image/png")])
        thread.send_text(text=f'*{title}*\n{description}',
                         files=files,
                         reply_to_id=message.id)
    else:
        thread.send_text(text=f'*{title}*\n{description}',
                         reply_to_id=message.id)
