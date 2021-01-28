from pontozobiztos.MyClient import ClientProxy
from pontozobiztos.models.User import User
import fbchat
from pontozobiztos import chatmongo
from pontozobiztos import utils
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger("chatbot")

_NAME = "utility"


def add_points(thread, author, message, *args):
    """Add points to user

    Args:
        thread (fbchat.Thread)
        author (User)
        message (fbchat.Message)

    Returns:
        bool: True if any of the commands succeeded, False otherwise.
    """
    if len(args) != 2:
        thread.send_text(f"Incorrect amount of arguments on /addpoints. "
                         f"Expected 2, got {len(args)}",
                         reply_to_id=message.id)
        logger.debug(f"Incorrect amount of arguments on /addpoints. "
                     f"Expected 2, got {len(args)}")
        return False

    try:
        value = args[1].replace(',', '.')
        value = float(value)
    except ValueError:
        thread.send_text(f"Could not convert {args[1]} to float.",
                         reply_to_id=message.id)
        logger.debug(f"Could not convert {args[1]} to float.")
        return False

    user_id = args[0]
    try:
        recipient = User(user_id)
    except ValueError:
        thread.send_text(f'User with id "{user_id}" was not found.',
                         reply_to_id=message.id)
        logger.debug(f'User with id "{user_id}" was not found.')
        return False
    return recipient.add_points(value, "utility.addpoints", message.id,
                                f"given by {author.uid}", True)


def points(thread, author, message, *args):
    """Retrieves current sum of points
    Args:
        thread(fbchat.Thread)
        author(User)
        message(fbchat.Message)
    """
    thread.send_text(f'Pontok: {str(author.points_sum)}\n'
                     f'Szorzó: {str(author.multiplier)}',
                     reply_to_id=message.id)
    return True


def points_all(thread, author, message, *args):
    """Prints points for all
    Args:
        thread(fbchat.Thread)
        author(User)
        message(fbchat.Message)
    """
    user_ids = chatmongo.get_user_ids()
    point_list = []
    for uid in user_ids:
        user = User(uid)
        point_list.append((user.fullname, user.points_sum, user.multiplier))
    point_list.sort(key=lambda x: x[1], reverse=True)
    text = "Összesített pontok:\n"
    for name, point, mult in point_list:
        text += f'{name}: {point} pts - {mult}x\n'
    thread.send_text(text, reply_to_id=message.id)
    return True


def set_multiplier(thread, author, message, *args):
    """Sets the multiplier to a user specified by user_id. `duration`
    should come in the form of _d_h_m, where the underscores are
    integers. Any of them can be left out. (0 by default)

    Args:
        thread (fbchat.Thread)
        author (User)
        message (fbchat.Message)

    Returns:
        bool: True if the request is successful, False otherwise.
    """

    if len(args) != 4:
        thread.send_text(f"Incorrect number of parameters. "
                         f"Expected 4, got {len(args)}",
                         reply_to_id=message.id)
        logger.debug(f"Incorrect number of parameters. "
                     f"Expected 4, got {len(args)}")
        return False

    recipient = args[0]
    typename = args[1]

    try:
        value = args[2].replace(',', '.')
        value = float(value)
    except ValueError:
        thread.send_text(f'Couldn\'t convert "{args[3]}" to float',
                         reply_to_id=message.id)
        logger.debug(f'Couldn\'t convert "{args[3]}" to float')
        return False

    lasts_until = utils.parse_duration_to_expiration_date(args[3])
    return chatmongo.set_multiplier(recipient, value, typename, lasts_until)


def transfer(thread, author, message, *args):
    """Transfers points from author to user specified by user_id.

    Args:
        thread (fbchat.Thread)
        author (User)
        message (fbchat.Message)

    Returns:
        bool: True if the transaction went through, False otherwise
    """
    # value has to be positive
    if len(args) != 2:
        thread.send_text(f'Incorrect amount of parameters. '
                         f'Expected 2, got {len(args)}')
        logger.debug(f"Transfer initiated with incorrect number of "
                     f"arguments by user {author.uid}. "
                     f"Expected 3, got {len(args)}. "
                     f"No changes were made")
        return False

    try:
        value = args[1].replace(',', '.')
        value = float(value)
    except ValueError:
        thread.send_text(f"Transfer initiated with incorrect value: {args[1]}",
                         reply_to_id=message.id)
        logger.debug(f"Transfer initiated with incorrect value: {args[1]}")
        return False

    user_id = args[0]

    if value <= 0:
        thread.send_text(f"Transfer initiated with negative value. "
                         f"No changes were made.",
                         reply_to_id=message.id)
        logger.debug(f"Transfer initiated with negative value. "
                     f"No changes were made.")
        return False

    # :class:`User` will return None if the uid is not found in the db
    try:
        recipient = User(user_id)
    except ValueError:
        thread.send_text(f'User with id "{user_id}" was not found',
                         reply_to_id=message.id)
        logger.debug(f'User with id "{user_id}" was not found')
        return False

    # sender must have enough points
    if author.points_sum < value:
        thread.send_text(f"Transfer failed. Insufficient funds.\n"
                         f"Current balance: {author.points_sum}",
                         reply_to_id=message.id)
        logger.debug(f"Transfer failed. Insufficient funds.\n"
                     f"Current balance: {author.points_sum}")
        return False

    # this breaks ACID principles but oh well...
    withdraw_ok = chatmongo.add_points(
        author.uid, (-1) * value, 'utility.transfer', mid=message.id,
        desc=f'transfer to {recipient.uid}')

    # withdraw failed
    if not withdraw_ok:
        logger.error(f"Something went wrong during withdrawal."
                     f"sender: {author.uid}; recipient: {recipient.uid}; "
                     f"message: {message.text}")
        return False

    # Demonstrating that :class:`User` has add_points. Same as before.
    # Care for the apply_multiplier flag. True by default.
    deposit_ok = recipient.add_points(
        value, 'utility.transfer', message.id,
        desc=f"transfer received from {author.uid}", apply_multiplier=False)

    if not deposit_ok:
        chatmongo.add_points(
            author.uid, value, 'utility.transfer', mid=message.id,
            desc=f'Revert for message {message.id}')
        logger.debug('Reverted last transaction')
        return False
    return True


def set_pontozo(thread, author, message, *args):
    """Sets is_pontozo flag in the database for the given user,
    making them be able to acces extra commands

    Args:
        thread (fbchat.Thread)
        author (User)
        message (fbchat.Message)
    """
    if len(args) != 2:
        thread.send_text('Incorrect number of parameters. '
                         f'Expected 1, got {len(args)}',
                         reply_to_id=message.id)
        logger.debug('Incorrect number of parameters. '
                     f'Expected 1, got {len(args)}')
        return False

    try:
        user = User(args[0])
    except ValueError:
        thread.send_text(f'No chatlako with id {args[0]}',
                         reply_to_id=message.id)
        logger.debug(f'No chatlako with id {args[0]}')
        return False

    if args[1] == '0':
        user.is_pontozo = False
    else:
        user.is_pontozo = True
    return True


def help_(thread, author, message, *args):
    """Prints help message

    Args:
        thread (fbchat.Thread)
        author (User)
        message (fbchat.Message)
    """
    command_texts = "Elérhető segítő parancsok:\n"
    for command in commands:
        words = ', '.join(['!' + x for x in command['cmd']])
        words += ": " + command['help']
        words += f"\nSzükséges flagek (vagy): {', '.join(command['allowed_for'])}"
        command_texts += words + "\n\n"
    thread.send_text(command_texts)
    return True


commands = [
    {
        'cmd': ['totalpoints', 'tp'],
        'function': points_all,
        'allowed_for': ['pontozo', 'admin'],
        'help': 'Összes pont táblázatszerűen'
    },
    {
        'cmd': ['addpoints', 'ap'],
        'function': add_points,
        'allowed_for': ['pontozo', 'admin'],
        'help': 'Pontok adása vagy elvonása valakitől. '
                'Az aktuális szorzók automatikusan érvényesülnek'
                ' pozitív érték esetében.\n'
                '!addpoints @user érték\n'
                'pl: !addpoints @Pusztai Máté -10'
    },
    {
        'cmd': ['points', 'p'],
        'function': points,
        'allowed_for': [],
        'help': 'Saját pontok összege és szorzók szorzata'
    },
    {
        'cmd': ['setmultiplier', 'sm'],
        'function': set_multiplier,
        'allowed_for': ['pontozo', 'admin'],
        'help': 'Multiplier beállítása valakinek. '
                'Egy típus megadása kötelező, amivel később hivatkozhatsz rá\n'
                '!setmultiplier <@user> <mult_tipus> <érték> <időtartam>\n'
                'pl: !setmultiplier @Pusztai Máté mert_cukros 1.75 3d2h30m'
    },
    {
        'cmd': ['transfer', 't'],
        'function': transfer,
        'allowed_for': [],
        'help': 'Pontok átutalása egy másik chatlakónak.\n'
                '!transfer <@user> <érték>'
    },
    {
        'cmd': ['setpontozo'],
        'function': set_pontozo,
        'allowed_for': ['admin'],
        'help': 'Pontozói privilégiumok adása vagy elvétele.\n'
                '!setpontozo @Benjamin Papp 1'
    },
    {
        'cmd': ['help', 'h'],
        'function': help_,
        'allowed_for': [],
        'help': 'Ezen üzenet kiíratása'
    }
]


def on_message(thread, author, message):
    """On message callback

    Args:
        thread (fbchat.Thread):
        author (User): Facebook id of the message author
        message (fbchat.MessageData): Message object

    Returns:
        None
    """
    if not message.text or not message.text.startswith('!'):
        return False

    # replace mention with user_id
    replaced_text = utils.replace_mentions(message)
    replaced_text = replaced_text[1:]  # remove bang from start
    command_parts = [x for x in replaced_text.split(' ') if x]
    logger.debug(f'Command parts {str(command_parts)}')

    command_list = []
    for cmd in commands:
        command_list += cmd['cmd']
    if command_parts and command_parts[0] not in command_list:
        return False

    try:
        selected_command = [x for x in commands if command_parts[0] in x['cmd']][0]
    except IndexError:
        thread.send_text('Unkown command. Type !help to show help message')
        return False

    parameters = command_parts[1:]  # remove the actual command
    result = None
    if not selected_command['allowed_for']:
        logger.debug(f'Executing command {command_parts[0]}')
        result = selected_command['function'](thread, author, message, *parameters)
    elif 'pontozo' in selected_command['allowed_for'] and author.is_pontozo:
        logger.debug(f'Executing command {command_parts[0]} as pontozo')
        result = selected_command['function'](thread, author, message, *parameters)
    elif 'admin' in selected_command['allowed_for'] and author.is_admin:
        logger.debug(f'Executing command {command_parts[0]} as admin')
        result = selected_command['function'](thread, author, message, *parameters)

    # it can also be None which is not handled
    if result is True:
        logger.info(f"Command '{message.text}' was successfully executed")
        message.react('👍')
    elif result is False:
        logger.info(f"Failed to execute '{message.text}'")
        message.react('👎')
