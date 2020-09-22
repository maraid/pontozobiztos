from num2words import num2words
from unidecode import unidecode
from fuzzywuzzy import fuzz
from fbchat import Message
from pontozobiztos import chatmongo
from pontozobiztos import utils

FUZZY_LIMIT = 90
MIN_PLAYERS = 1
expected_number = 1
is_running = True
scores = {}
last_n = []

accepted_languages = ['hu', 'en', 'fr', 'it', 'de']
numbers_0_to_500 = {}
for n in range(500):
    numbers_0_to_500.update({unidecode(num2words(n, lang=l)): n
                             for l in accepted_languages})


def fuzzy_compare_to_all(text):
    for k in numbers_0_to_500.keys():
        if fuzz.ratio(k, text) > FUZZY_LIMIT:
            return numbers_0_to_500[k] == expected_number
    return None


def format_scores():
    text = "GAME OVER\n\nScores:\n"
    mentions = []
    for uid, score in scores.items():
        user_ptr = chatmongo.user_coll.find({'_id': uid}, {'fullname': 1})
        text += r"{}: " + str(score) + "\n"
        mentions.append((uid, utils.get_monogram(user_ptr.next()['fullname'])))
    return Message.formatMentions(text, *mentions)


def on_message(client, author, message):
    global expected_number
    global is_running
    global scores
    global last_n

    text = unidecode(message.text).lower()
    if author.is_admin:
        if text == '1':
            is_running = True
        if text == '/stop':
            is_running = False

    if not is_running:
        return
    elif len(text) == 0:
        return
    elif '_' in text:
        return
    elif text[0] == '0' and len(text) > 1:
        return

    try:
        accepted = (int(message.text) == expected_number)
    except ValueError:
        accepted = fuzzy_compare_to_all(text)

    if accepted is None:
        return
    elif not accepted or author.uid in last_n:
        client.react_to_message(message.uid, 'NO')
        client.send(format_scores())
        # reset
        expected_number = 1
        scores = {}
        last_n = []
        # start new
        client.send_text('1')
        return

    last_n.append(author.uid)
    if len(last_n) >= MIN_PLAYERS:
        last_n = last_n[-MIN_PLAYERS:]

    scores.update({author.uid: scores.get(author.uid, 0) + 1})
    expected_number += 1
    return client.react_to_message(message.uid, 'YES')
