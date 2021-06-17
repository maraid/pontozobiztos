import requests
import fbchat


def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """
    if message.text == '!link':
        ip = requests.get("https://api.ipify.org/?format=json").json()['ip']
        message.thread.send_text('http://' + ip + '/daily_links', reply_to_id=message.id)
        return True
    return False