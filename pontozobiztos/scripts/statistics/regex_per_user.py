from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from pontozobiztos import chatmongo
from pontozobiztos import utils


msg_col = chatmongo.get_message_collection()


def get_regex_sent_count_per_user(regex, year: int = None):
    start, end = utils.year_start_end(year)
    return _get_regex_sent_count_per_user(regex, start, end)


def _get_regex_sent_count_per_user(regex, start, end) -> List[Tuple]:
    regex_str = '(' + '|'.join(regex) + ')'
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {"$addFields": {"match": {"$regexMatch": {"input": "$text", "regex": regex_str}}}},
        {"$match": {"match": True}},
        {'$group': {'_id': '$author', 'document_count': {'$sum': 1}}},
        {'$lookup': {
            'from': 'users',
            'localField': '_id',
            'foreignField': '_id',
            'as': 'user_data'
        }},
        {'$unwind': '$user_data'},
        {'$replaceWith': {
            '_id': '$_id',
            'document_count': '$document_count',
            'fullname': '$user_data.fullname'
        }}
    ])
    return sorted(result, key=lambda i: i['document_count'])


def plot(regex, title: str = None, year: int = None):
    title = title or ', '.join(regex)
    year = year or datetime.today().year
    result = get_regex_sent_count_per_user(regex, year)
    plt.rcdefaults()
    labels = [i['fullname'] for i in result]
    y_pos = np.arange(len(labels))
    values = [i['document_count'] for i in result]

    plt.barh(y_pos, values, align='center', alpha=0.5)
    plt.yticks(y_pos, labels)
    plt.title(f'{title} ({year})')
    plt.subplots_adjust(left=0.3)
    plt.show()


if __name__ == '__main__':
    plot(['^[ ]*$'], 'Egyszavas üzenetek száma')
    # plot(['zsapex', 'apex'])
