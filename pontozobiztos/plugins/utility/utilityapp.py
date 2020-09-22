from pontozobiztos.MyClient import ClientProxy
from pontozobiztos.models.User import User
import fbchat
from pontozobiztos import chatmongo
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger("chatbot")

_NAME = "utility"


def admin_stuff(client, author, message, text):
    """Admin commands. Currently implemented::
        - addpoints
        - setmultiplier

    Args:
        client (ClientProxy): proxy for fbchat.Client
        author (User): User object of the author
        message (Message): Message object
        text (str): message.string mentions replaced with ids

    Returns:
        bool: True if any of the commands succeeded, False otherwise.
    """
    del client
    del author

    logger.debug(f"Running admin stuff, with command {text}")
    split_text = text.split(' ')
    if not split_text:
        return False

    elif split_text[0] == '/addpoints':
        # /addpoints <user_id> <value>

        if len(split_text) != 3:
            logger.info(f"Incorrect amount of arguments on /addpoints. Expected"
                        f" 3, got {len(split_text)}")
            return False
        try:
            value = float(split_text[2])
        except ValueError:
            logger.info(f"Could not convert {split_text[2]} to float.")
            return False

        user_id = split_text[1]
        user = User(user_id)
        if user is not None:
            return user.add_points(value, "utility.addpoints",
                                   message.uid, "given by admin", True)
        else:
            return False

    elif split_text[0] == "/setmultiplier":
        # /setmultiplier <user_id> <typename> <value> <duration>
        # /setmultiplier @Kiss Jozsef kakie 1.3 1d12h30m

        if len(split_text) != 5:
            logger.info(f"Incorrect number of arguments."
                        f"Expected 5, got {len(split_text)}")
            return False

        try:
            value = float(split_text[3])
        except ValueError:
            logger.info(f"Couldn't convert {split_text[3]} to float")
            return False

        user_id = split_text[1]
        typename = split_text[2]
        duration = split_text[4]
        return set_multiplier(user_id, typename, value, duration)


def set_multiplier(user_id, typename, value, duration):
    """Sets the multiplier to a user specified by user_id. `duration`
    should come in the form of _d_h_m, where the underscores are
    integers. Any of them can be left out. (0 by default)

    Args:
        user_id (str): facebook user id
        typename (str): name of the multiplier
        value (float): value of the multiplier
        duration (str): duration string. see description for details

    Returns:
        bool: True if the request is successful, False otherwise.
    """
    def parse_duration_to_expiration_date():
        days = hours = minutes = 0

        match = re.search(r"(\d+)d", duration)
        if match is not None:
            days = int(match.group(1))

        match = re.search(r"(\d+)h", duration)
        if match is not None:
            hours = int(match.group(1))

        match = re.search(r"(\d+)m", duration)
        if match is not None:
            minutes = int(match.group(1))

        return datetime.today() + timedelta(days=days, hours=hours, minutes=minutes)

    return chatmongo.set_multiplier(user_id, value, typename,
                                    parse_duration_to_expiration_date())


def transfer(author, message, user_id, amount):
    """Transfers points from author to user specified by user_id.

    Args:
        author (User): User object of the requester
        message (fbchat.Message): message object
        user_id (str): recipient's facebook user id
        amount (int): amount of points to be transferred

    Returns:
        bool: True if the transaction went through, False otherwise
    """
    # value has to be positive
    if amount <= 0:
        logger.info(f"Transfer init iated with negative value by "
                    f"{author.uid}. No changes were made.")
        return False

    # :class:`User` will return None if the uid is not found in the db
    receiver_user = User(user_id)
    if receiver_user is None or not author:
        logger.info(f"Transfer could not be made because {user_id} "
                    f"does not exist. No changes were made.")
        return False

    # sender must have enough points
    if author.points_sum < amount:
        logger.info(f"Transfer failed. Insufficient funds {author.uid}")
        return False

    # this breaks ACID principles but oh well...
    withdraw_ok = chatmongo.add_points(
        author.uid, (-1) * amount, 'utility.transfer', mid=message.uid,
        desc=f'transfer to {receiver_user.uid}')

    # withdraw failed
    if not withdraw_ok:
        logger.error(f"Something went wrong during withdrawal."
                     f"sender: {author.uid}; receiver: {receiver_user.uid}; "
                     f"message: {message.text}")
        return False

    # Demonstrating that :class:`User` has add_points. Same as before.
    # Care for the apply_multiplier flag. True by default.
    deposit_ok = receiver_user.add_points(
        amount, 'utility.transfer', message.uid,
        desc=f"transfer received from {author.uid}", apply_multiplier=False)

    return deposit_ok


def common_stuff(client, author, message, text):
    """ Common commands. Currently implemented:
        - transfer

    Args:
        client (ClientProxy): fbchat.Client proxy
        author (User): User object of the author
        message (fbchat.Message): Message object
        text: message.text with mentions replaced with ids

    Returns:
        bool: True if command went through, False otherwise
    """
    del client

    split_text = text.split(' ')

    if not split_text:
        return False

    if split_text[0] == '/transfer':
        if len(split_text) != 3:
            logger.info(f"Transfer initiated with incorrect number of "
                        f"arguments by user {author.uid}. "
                        f"Expected 3, got {len(split_text)}. "
                        f"No changes were made")
            return False

        try:
            value = int(split_text[2])
        except ValueError:
            logger.info(f"Transfer initiated with non-numeric value by "
                        f"{author.uid}. No changes were made.")
            return False

        user_id = split_text[1]
        return transfer(author, message, user_id, value)


def on_message(client, author, message):
    """On message callback

    Args:
        client (ClientProxy): Proxy for fbchat.client
        author (User): Facebook id of the message author
        message (fbchat.Message): Message object

    Returns:
        None
    """
    if not message.text or not message.text.startswith('/'):
        return

    # replace mention with user_id
    replaced_text = message.text
    offset_correction = 0
    for mention in message.mentions:
        replaced_text = replaced_text[:(mention.offset + offset_correction)] \
                                      + str(mention.thread_id) \
                                      + replaced_text[(mention.offset
                                                       + offset_correction
                                                       + mention.length):]
        offset_correction += len(mention.thread_id) - mention.length

    success = common_stuff(client, author, message, replaced_text)
    if author.is_admin and not success:
        success = admin_stuff(client, author, message, replaced_text)

    if success:
        logger.info(f"Command '{message.text}' was successfully executed")
        client.react_to_message(message.uid, 'YES')
    else:
        logger.info(f"Failed to execute '{message.text}'")
        client.react_to_message(message.uid, 'NO')
