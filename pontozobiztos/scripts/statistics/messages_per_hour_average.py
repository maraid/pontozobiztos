import numpy as np
import matplotlib.pyplot as plt
import calendar
import datetime

from pontozobiztos import chatmongo
from pontozobiztos import utils

msg_col = chatmongo.get_message_collection()


def get_messages_per_day_by_year(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_messages_per_day(start, end)


def _get_messages_per_day(start, end) -> list:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {'$sort': {'created_at': 1}},
        {'$group': {'_id': {'$hour': '$created_at'},
                    'document_count': {'$sum': 1}}},
    ])
    return sorted(list(result), key=lambda i: i['_id'])


def plot(year: int = None):
    year = year or datetime.datetime.today().year
    plt.rcdefaults()
    result = get_messages_per_day_by_year(year)
    labels = [i['_id'] for i in result]
    values = [i['document_count'] / 365 for i in result]
    y_pos = np.arange(len(values))

    plt.bar(y_pos, values, align='center', alpha=0.5)
    plt.xticks(y_pos, labels)
    plt.xlabel('Óra')
    plt.ylabel('Üzenet átlagos száma')
    plt.title(f'Üzenetek száma órákra bontva ({year})')
    plt.show()


if __name__ == '__main__':
    plot()
