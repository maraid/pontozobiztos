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

    if len(params) == 1:
        date = datetime.strptime(' '.join(params), '%Y.%m.%d')
    elif len(params) == 2:
        date = datetime.strptime(' '.join(params), '%Y.%m.%d %H:%M:%S')
    else:
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





