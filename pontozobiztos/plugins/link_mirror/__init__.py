from fbchat import Message, GroupData
from pontozobiztos.models.User import User

from fbchat import GroupData

from pontozobiztos.plugins.link_mirror import Converter


def on_message(thread, author, message):
    """On message callback

    Args:
        thread (GroupData): a proxy fbchat.Client
        author (User): pontozobiztos.models.User object
        message (Message): Received fbchat.Message object
    """
    if message.text[:8] != 'https://':
        return False

    converter = Converter.create_converter(message.text)
    if converter is None:
        return False

    try:
        converted_uris = converter.convert()
    except Converter.PluginException as e:
        thread.send_text(str(e), reply_to_id=message.id)
        return True
    except ValueError:
        return False

    for uri in converted_uris:
        thread.send_uri(uri=uri)
    return True
