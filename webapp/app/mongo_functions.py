import pymongo
import logging
from datetime import datetime
import copy

logger = logging.getLogger("chatbot.chatmongo")
client = pymongo.MongoClient(host='mongo', port=27017)
db = client.chat
user_coll = db.users
message_coll = db.messages

def get_daily_links(day: datetime=None):
    day = day or datetime.today()

    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day.replace(hour=23, minute=59, second=59, microsecond=999)

    res = message_coll.aggregate([
        {'$match': {'created_at': {'$gte': day_start, '$lt': day_end}}},
        {'$unwind': '$attachments'},
        {'$match': {'attachments.type': 'share'}},
        {'$lookup':
        {
            'from': 'users',
            'localField': 'author',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$project': {'created_at': 1, 'author_name': '$user.fullname', 'url': '$attachments.original_url'}}
    ])
    return tuple(sorted(res, key=lambda x: x['created_at']))



if __name__ == "__main__":
    res = get_daily_links()
    for link in res:
        print(link)
