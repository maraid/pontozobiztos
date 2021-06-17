from datetime import datetime
from pontozobiztos import chatmongo


def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)

        Returns:
            bool
    """

    if not message.text.startswith('!shortcut '):
        return False

    params = [x for x in message.text[10:].split(' ') if x]

    date = None
    if len(params) == 1:
        try:
            date = datetime.strptime(' '.join(params), '%Y.%m.%d')
        except ValueError:
            pass
    elif len(params) == 2:
        try:
            date = datetime.strptime(' '.join(params), '%Y.%m.%d %H:%M:%S')
        except ValueError:
            pass

    if date is None:
        message.react('🤷‍♂️')
        return True

    if date > datetime.now():
        message.react('🔮')
        return True

    try:
        closest_message = chatmongo.find_closest_message_to_date(date)
    except StopIteration:
        return True

    message.thread.send_text(text='^', reply_to_id=closest_message['_id'])
    return True





