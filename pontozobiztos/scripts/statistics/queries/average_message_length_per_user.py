import numpy as np
import matplotlib.pyplot as plt
import calendar
import datetime

from pontozobiztos import chatmongo
from pontozobiztos import utils

msg_col = chatmongo.get_message_collection()


def get_average_text_length_by_year(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_average_text_length(start, end)


def _get_average_text_length(start, end) -> list:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {"$match": {
            "text": {
                "$exists": True,
                "$ne": None
            }
        }},
        {'$project': {
            'author': 1,
            'text_len':  {'$strLenCP': "$text"}
        }},
        {'$group': {'_id': '$author',
                    'avg_text_len': {'$avg': '$text_len'}}},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "_id",
            "as": "user_data"
        }},
        {"$unwind": "$user_data"},
        {"$replaceWith": {
            "_id": "$_id",
            "avg_text_len": "$avg_text_len",
            "fullname": "$user_data.fullname"
        }}
    ])
    return sorted(list(result), key=lambda i: i['avg_text_len'])


def plot(year: int = None):
    year = year or datetime.datetime.today().year
    plt.rcdefaults()
    result = get_average_text_length_by_year(year)
    labels = [i['fullname'] for i in result]
    values = [i['avg_text_len'] for i in result]
    y_pos = np.arange(len(labels))

    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:mustard')
    plt.yticks(y_pos, labels)
    plt.title(f'Üzenetek átlagos hossza ({year})')
    plt.subplots_adjust(left=0.3)
    plt.savefig('results/average_message_length.png')
    # plt.show()
    plt.close()


if __name__ == '__main__':
    plot()
