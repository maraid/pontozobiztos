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
        {'$group': {'_id': {'$dayOfYear': '$created_at'},
                    'document_count': {'$sum': 1}}},
    ])
    result_list = list(result)
    for item in result_list:
        item['date'] = utils.day_of_year_to_date(start.year, item['_id'])
        del item['_id']
    result_list.sort(key=lambda i: i['date'])
    return result_list


def plot(year: int = None):
    year = year or datetime.datetime.today().year
    plt.rcdefaults()
    result = get_messages_per_day_by_year(year)

    months = ('Jan', 'Febr', 'Már', 'Ápr', 'Máj', 'Jún',
              'Júl', 'Aug', 'Szept', 'Okt', 'Nov',
              'Dec')

    labels = []
    xpos = []
    for i, day in enumerate(result):
        middle_day = int(calendar.monthrange(year, day['date'].month)[1] / 2)
        if day['date'].day == middle_day:
            labels.append(months[day['date'].month - 1])
            xpos.append(i + 1)
        elif day['date'].day == 1:
            labels.append('')
            xpos.append(i + 1)

    values = [i['document_count'] for i in result]
    y_pos = np.arange(len(values))

    plt.bar(y_pos, values, align='center', alpha=0.5, width=1.0)
    plt.xticks(xpos, labels)
    plt.title(f'Üzenetek száma napok szerint ({year})')
    plt.show()


if __name__ == '__main__':
    plot()
