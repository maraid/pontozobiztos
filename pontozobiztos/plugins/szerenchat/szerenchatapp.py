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
    if message.text and message.text[0] != '!':
        return False

    command = message.text[1:]
    command_list = ['fvi', 'fví', 'd6', 'k52', 'roll', 'lapot',
                    'kő', 'ko', 'papír', 'papir', 'olló', 'ollo']
    if command.split()[0] not in command_list:
        return False

    if re.match(r'fv[ií]', command):
        response = flip_a_coin()
    elif match := re.match(r'fv[ií] +(\d+)', command):
        n = int(match.group(1))
        response = ', '.join(flip_n_coins(n))
    elif re.match(r'^\s*d6\s*$', command):
        response = str(d6())
    elif match := re.match(r'^\s*d6 +(\d+)', command):
        n = int(match.group(1))
        response = ' '.join(str(n) for n in d6_n(n))
    elif re.match(r'k52$', command) or re.match(r'lapot$', command):
        response = k52()
    elif match := re.match(r'k52 +(\d+)$', command):
        n = int(match.group(1))
        response = ' '.join(k52_n(n))
    elif re.match(r'roll$', command):
        response = roll()
    elif match := re.match(r'roll +(\d+)$', command):
        n = int(match.group(1))
        response = ' '.join(str(x) for x in roll_n(n))
    elif match := re.match(r'roll +(\d+) +(\d+)$', command):
        a = int(match.group(1))
        b = int(match.group(2))
        response = roll(a, b)
    elif match := re.match(r'roll +(\d+) +(\d+) +(\d+)$', command):
        n = int(match.group(1))
        a = int(match.group(2))
        b = int(match.group(3))
        response = ' '.join(str(x) for x in roll_n(n, a, b))
    elif command in ('kő', 'ko', 'papír', 'papir', 'olló', 'ollo'):
        response = rock_paper_scissors()
    else:
        response = "Invalid command format"

    thread.send_text(response, reply_to_id=message.id)
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


def d6():
    """Rolls n times with 6 sided dice. Returns a list of the results

    Returns:
        List[int]: list of dice rolls
    """
    return random.randint(1, 6)


def d6_n(n):
    return [d6() for _ in range(n)]


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


def k52_n(n, put_back=False):
    """Picks n cards from a 52 card deck. If put_back is True then the same
    card can be in the result multiple times.

    Args:
        n(int): number of cards to pick from the deck
        put_back(bool): marks whether the one card can be picked multiple times

    Returns:
        List[str]: Cards picked
    """
    if n > 52:
        return ["Csak 52 kártya van te nyomi"]
    if put_back:
        return [k52() for _ in range(n)]
    else:
        hand = set()
        while len(hand) != n:
            hand.add(k52())
        return list(hand)


def roll(a=1, b=100):
    return random.randint(a, b)


def roll_n(n, a=1, b=100):
    return [roll(a, b) for _ in range(n)]


def rock_paper_scissors():
    return random.choice(['🗿', '📄', '✂'])
