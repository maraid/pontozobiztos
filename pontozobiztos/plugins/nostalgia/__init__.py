import fbchat
from datetime import datetime, timedelta
from pontozobiztos import chatmongo, chatscheduler
import pytz
import re
import random


group_thread: fbchat.GroupData


def init(thread, *args, **kwargs):
    global group_thread
    group_thread = thread

    sched = chatscheduler.get_scheduler()
    sched.add_job(callback, 'cron', hour='7,20', minute=30)


def on_message(thread: fbchat.Group, author, message):
    pass


def top_n_most_reactions(year: int, n=3):
    from_date = datetime.today().replace(year=year, hour=0, minute=0, second=0,
                                         microsecond=0, tzinfo=pytz.UTC)
    to_date = from_date + timedelta(days=1)
    res = chatmongo.get_message_collection().aggregate([
        {'$match': {'created_at': {'$gte': from_date, '$lt': to_date}}},
        {"$project": {
            "_id": 1,
            "author": 1,
            "reactions": {"$objectToArray": "$reactions"}}},
        {"$unwind": "$reactions"},
        {"$sort": {"_id": 1}},
        {"$group": {
            "_id": "$_id",
            "react_count": {"$sum": 1}}},
        {"$sort": {"react_count": -1}},
        {"$limit": n},
    ])
    return list(res)


def top_n_legacy_emojis(year, n=3):
    from_date = datetime.today().replace(year=year, hour=0, minute=0, second=0,
                                         microsecond=0, tzinfo=pytz.UTC)
    to_date = from_date + timedelta(days=1)
    res = chatmongo.get_message_collection().aggregate([
        {'$match': {'created_at': {'$gte': from_date, '$lt': to_date}}},
    ])
    res = list(res)

    smile_patterns = [r':d+', r'xd+', r'^lol.*']
    pat = re.compile(r'(?:' + '|'.join(smile_patterns) + ')')

    for i in range(len(res)):
        smile_count = 0
        for msg_later in res[i+1:]:
            if pat.search(msg_later['text'].lower()):
                smile_count += 1
            else:
                res[i]['smile_count'] = smile_count
                i += smile_count
                break

    res = [x for x in res if x.get('smile_count', 0) != 0]
    res.sort(key=lambda x: x.get('smile_count', 0), reverse=True)
    return res[:n]


def callback():
    top3 = []
    year = 0
    while not top3:
        year = random.randint(2014, datetime.today().year - 1)
        top3 = top_n_most_reactions(year) or top_n_legacy_emojis(year)
    selected_msg = random.choice(top3)

    reply_text = f'Úgy számoltam, hogy ez vicces volt {year} ezen napján.'
    group_thread.send_text(text=reply_text, reply_to_id=selected_msg['_id'])
