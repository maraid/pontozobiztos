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
    # for r in result:
    #     print(r['text'])
    return sorted(result, key=lambda i: i['document_count'])


def _plot(regex, title: str = None, year: int = None):
    title = title or ', '.join(regex)
    year = year or datetime.today().year
    result = get_regex_sent_count_per_user(regex, year)
    plt.rcdefaults()
    labels = [i['fullname'] for i in result]
    y_pos = np.arange(len(labels))
    values = [i['document_count'] for i in result]

    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:dull red')
    plt.yticks(y_pos, labels)
    plt.title(f'{title} ({year})')
    plt.subplots_adjust(left=0.3)
    # plt.savefig(f'results/regex_per_user_{"-".join(regex)}.png')
    # plt.close()
    plt.show()


def plot(year: int = None):
    _plot(['^[^ ]+$'], 'Egyszavas üzenetek száma', year)
    _plot(['zsapex', 'apex', 'ugrás', 'ugras', 'ugrabugra', 'zsapi'], 'zsapex', year)


if __name__ == '__main__':
    # plot(['^[ ]*$'], 'Egyszavas üzenetek száma')
    # _plot([':\^\)'], ':^)')
    # _plot(['hype', 'Hype', 'HYPE'], 'HYPE')
    # _plot(['open\.spotify\.com'], 'spotify')
    # _plot(['youtube\.com', 'youtu.be'], 'youtube')
    _plot(['9gag\.com'], '9gag')
    # plot(['zsapex', 'apex'])
    # plot(['zsapex', 'apex', 'ugrás', 'ugras', 'ugrabugra', 'zsapi'])
