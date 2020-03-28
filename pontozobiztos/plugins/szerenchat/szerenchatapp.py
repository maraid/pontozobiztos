from fbchat import Message
from pontozobiztos.models.User import User
from pontozobiztos.MyClient import ClientProxy
import random
import logging
from pontozobiztos import chatmongo

logger = logging.getLogger("chatbot")


def on_message(client=None, author=None, message=None):
    """On message callback

    Args:
        client (ClientProxy): a proxy fbchat.Client
        author (User): pontozobiztos.models.User object
        message (Message): Received fbchat.Message object
    """


def roll(client, author, message):
    def success():
        return client.react_to_message(message.uid, 'YES')

    def failure():
        return client.react_to_message(message.uid, 'NO')

    arg_list = message.text.split(' ')

    limit_low = 1
    limit_high = 100

    if not arg_list or arg_list[0] != "/roll":
        return

    if len(arg_list) > 1:
        try:
            limit_high = int(arg_list[1])
        except ValueError:
            logger.error(f"Could not convert '{arg_list[1]}' to int.")
            return

    if len(arg_list) > 2:
        limit_low = limit_high



if __name__ == "__main__":
    print(chatmongo.get_points_sum("100002385331635"))

    attis = User("100002385331635")
    print(attis)
    attis.add_points(4.0, "szerenchat", "asd")
    print(attis)
