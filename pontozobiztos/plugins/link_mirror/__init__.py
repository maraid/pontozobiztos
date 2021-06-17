from fbchat import Message, GroupData
from pontozobiztos.models.User import User

from fbchat import GroupData

from pontozobiztos.plugins.link_mirror import Converter

import logging
log = logging.getLogger("chatbot")


def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """

    if not message.text.startswith('https://'):
        return False

    try:
        converted_uris = Converter.convert_uri(message.text)
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

    for uri in converted_uris:
        log.debug(f'Sending URL: {uri}')
        # thread.send_uri(uri=uri)
        message.thread.send_text(text=uri)
    return True
