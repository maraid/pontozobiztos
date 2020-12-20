from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from pontozobiztos import chatmongo
from pontozobiztos import utils

msg_col = chatmongo.get_message_collection()


def get_messages_per_user_by_year(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_messages_per_user(start, end)


def _get_messages_per_user(start, end) -> list:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {'$sort': {'created_at': 1}},
        {'$group': {'_id': {'user_id': '$author'},
                    'document_count': {'$sum': 1}}},
        {"$lookup": {
            "from": "users",
            "localField": "_id.user_id",
            "foreignField": "_id",
            "as": "user_data"
        }},
        {"$unwind": "$user_data"},
        {"$replaceWith": {
            "_id": "$_id",
            "document_count": "$document_count",
            "fullname": "$user_data.fullname"
        }}
    ])
    result_list = list(result)
    for item in result_list:
        del item['_id']
    return sorted(result_list, key=lambda i: i['document_count'])


def plot(year: int = None):
    year = year or datetime.today().year
    result = get_messages_per_user_by_year(year)

    plt.rcdefaults()
    labels = [i['fullname'] for i in result]
    y_pos = np.arange(len(labels))
    values = [i['document_count'] for i in result]

    plt.barh(y_pos, values, align='center', alpha=0.5)
    plt.yticks(y_pos, labels)
    plt.title(f'Üzenetek száma per fő ({year})')
    plt.subplots_adjust(left=0.3)
    plt.show()


if __name__ == '__main__':
    plot()
