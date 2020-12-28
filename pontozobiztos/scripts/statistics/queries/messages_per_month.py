import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from pontozobiztos import chatmongo
from pontozobiztos import utils

msg_col = chatmongo.get_message_collection()


def get_messages_per_month_by_year(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_messages_per_month(start, end)


def _get_messages_per_month(start, end) -> list:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {'$sort': {'created_at': 1}},
        {'$group': {'_id': {'$month': '$created_at'},
                    'document_count': {'$sum': 1}}},
    ])
    return list(result)


def plot(year: int = None):
    plt.rcdefaults()
    year = year or datetime.today().year
    result = get_messages_per_month_by_year(year)
    months = ('Jan', 'Febr', 'Már', 'Ápr', 'Máj', 'Jún',
              'Júl', 'Aug', 'Szept', 'Okt', 'Nov',
              'Dec')
    y_pos = np.arange(len(months))
    values = [i['document_count'] for i in result]
    values += [0] * (12 - len(result))

    plt.bar(y_pos, values, align='center', alpha=0.5, color='xkcd:brownish orange')
    plt.xticks(y_pos, months)
    plt.title(f'Üzenetek száma hónapok szerint ({year})')
    for i, v in enumerate(values):
        plt.text(i, max(values) * 0.02, str(v),
                 horizontalalignment="center", rotation=90)
    plt.savefig('results/messages_per_month.png')
    plt.close()
    # plt.show()


if __name__ == '__main__':
    plot(2018)
