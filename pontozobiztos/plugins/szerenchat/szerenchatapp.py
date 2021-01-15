import fbchat
from pontozobiztos.models.User import User
import random
import logging
from typing import List
import re

logger = logging.getLogger("chatbot")


def on_message(thread=None, author=None, message=None):
    """On message callback

    Args:
        thread (fbchat.GroupData): a proxy fbchat.Client
        author (User): pontozobiztos.models.User object
        message (fbchat.Message): Received fbchat.Message object
    """
    if not message.text.startswith('!'):
        return False

    logger.debug('Got potential szerenchat command: ' + message.text)

    if match := re.search(r'!d(\d+)( (\d+))?', message.text):
        func = dice
        params = [
            {
                'name': 'sides',
                'value': int(match.group(1)),
                'limits': (2, 1000),
            },
            {
                'name': 'count',
                'value': int(match.group(3) or 1),
                'limits': (1, 1000)
            },
        ]
    elif match := re.search(r'!k52( (\d+))?', message.text):
        func = k52_n
        params = [
            {
                'name': 'count',
                'value': int(match.group(2) or 1),
                'limits': (1, 52)
            }
        ]
    elif message.text == '!szerenchat':
        thread.send_text('Elérhető szerenchat parancsok. () => optional:\n'
                         'N oldalú dobókocka M-szer:\n!d<N> (M)\n\n'
                         '52 lapos pakliból M db húzás:\n!k52 (M)')
        return True
    else:
        return False

    kwargs = {}
    for p in params:
        if p['value'] < p['limits'][0] or p['value'] > p['limits'][1]:
            thread.send_text('You went full Ákos man. Never go full Ákos',
                             reply_to_id=message.id)
            return True
        kwargs[p['name']] = p['value']

    try:
        result = func(**kwargs)
    except ValueError as e:
        thread.send_text(str(e), reply_to_id=message.id)
        return True

    thread.send_text(str(' '.join(str(x) for x in result)),
                     reply_to_id=message.id)
    return True


def flip_a_coin():
    """Flips a coin

    Returns:
        str: heads or tails
    """
    return random.choice(['fej', 'írás'])


def flip_n_coins(n):
    """Flips n coins

    Args:
        n(int): times to flip the coin

    Returns:
        List[str]: list of heads and tails
    """
    return [flip_a_coin() for _ in range(n)]


def dice(sides, count):
    return [random.randint(1, sides) for _ in range(count)]


SYMBOLS = ['♠', '♣', '♥', '♦']
NUMBERS = ['A', '1', '2', '3', '4', '5', '6',
           '7', '8', '9', '10', 'J', 'Q', 'K']


def k52():
    """Picks n cards from a 52 cards deck. If put back is set to True
    then tha same card can be in the result multiple times.

    Returns:
        str: Card picked
    """
    return random.choice(SYMBOLS) + random.choice(NUMBERS)


def k52_n(count, put_back=False):
    """Picks n cards from a 52 card deck. If put_back is True then the same
    card can be in the result multiple times.

    Args:
        n(int): number of cards to pick from the deck
        put_back(bool): marks whether the one card can be picked multiple times

    Returns:
        List[str]: Cards picked
    """

    if put_back:
        return [k52() for _ in range(count)]
    else:
        if count > 52:
            raise ValueError(f'Az 52 lapos pakliból nem tudsz {count}-t húzni')
        hand = set()
        while len(hand) != count:
            hand.add(k52())
        return list(hand)


def roll(a=1, b=100):
    return random.randint(a, b)


def roll_n(n, a=1, b=100):
    return [roll(a, b) for _ in range(n)]


def rock_paper_scissors():
    return random.choice(['🗿', '📄', '✂'])
