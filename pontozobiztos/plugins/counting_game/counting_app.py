from num2words import num2words
from unidecode import unidecode
from fuzzywuzzy import fuzz
from fbchat import Message
from pontozobiztos import chatmongo
from pontozobiztos import utils
from pontozobiztos import chatscheduler
import fbchat
from datetime import datetime
from datetime import timedelta
from apscheduler.jobstores.base import JobLookupError

GRACE_PERIOD = 2 * 60  # seconds
SHOW_GAME_OVER = False
FUZZY_LIMIT = 90
MIN_PLAYERS = 1
expected_number = 1
is_running = False
scores = {}
last_n = []
last_message = None
current_thread: fbchat.GroupData

game_over_job = None

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


def format_scores(reason="GAME OVER"):
    text = reason + "\n\nScores:\n"
    mentions = []
    for uid, score in scores.items():
        user_ptr = chatmongo.user_coll.find({'_id': uid}, {'fullname': 1})
        text += r"{}: " + str(score) + "\n"
        mentions.append((uid, utils.get_monogram(user_ptr.next()['fullname'])))
    return Message.format_mentions(text, *mentions)


def on_message(message, author):
    """
        Args:
            message (fbchat.MessageData)
            author(models.User.User)
    """

    global expected_number
    global is_running
    global scores
    global last_n
    global current_thread
    global last_message

    print('counting_game.on_message called')
    text = unidecode(message.text).lower()
    if text == '1':
        if not is_running:
            is_running = True
            current_thread = message.thread
        else:
            message.react('👎')
            do_game_over()
            return True
    elif not is_running:
        return False
    elif len(text) == 0:
        return False
    elif '_' in text:
        return False
    elif text[0] == '0' and len(text) > 1:
        return False

    try:
        accepted = (int(text) == expected_number)
    except ValueError:
        accepted = fuzzy_compare_to_all(text)

    if accepted is None:
        return
    elif not accepted or author.uid in last_n:
        message.react('🤦')
        do_game_over(timeout=False)
    else:
        last_n.append(author.uid)
        if len(last_n) >= MIN_PLAYERS:
            last_n = last_n[-MIN_PLAYERS:]

        scores.update({author.uid: scores.get(author.uid, 0) + 1})
        expected_number += 1
        message.react('👌')
        last_message = message
        schedule_game_over()
    return True


def do_game_over(reason="GAME OVER", timeout=True):
    global scores
    global last_n
    global expected_number
    global is_running

    try:
        game_over_job.remove()
    except (JobLookupError, AttributeError):
        pass

    if timeout:
        try:
            last_message.react('⌛')
        except AttributeError:
            pass

    if SHOW_GAME_OVER:
        text, mentions = format_scores(reason)
        current_thread.send_text(text=text, mentions=mentions)
    # reset
    expected_number = 1
    scores = {}
    last_n = []
    is_running = False


def schedule_game_over():
    global game_over_job

    sc = chatscheduler.get_scheduler()
    dt = datetime.now() + timedelta(seconds=GRACE_PERIOD)
    try:
        game_over_job.reschedule('date', run_date=dt)
    except (JobLookupError, AttributeError):
        game_over_job = sc.add_job(
            do_game_over,
            'date',
            ["TIME'S UP"],
            run_date=dt
        )
