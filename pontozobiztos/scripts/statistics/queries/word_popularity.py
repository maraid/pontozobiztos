import unidecode
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from pontozobiztos import chatmongo
from pontozobiztos import utils


msg_col = chatmongo.get_message_collection()


def get_one_word_popularity(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_one_word_popularity(start, end)


def _get_one_word_popularity(start, end) -> List[Tuple]:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}}
    ])
    unique_domains_dct = {}
    for item in list(result):
        try:
            word_list = item['text'].split(' ')
        except AttributeError:
            continue
        for word in word_list:
            if not word:
                continue
            try:
                unique_domains_dct[word] += 1
            except KeyError:
                unique_domains_dct[word] = 1
    unique_domains = unique_domains_dct.items()
    return sorted(unique_domains, key=lambda i: i[1])


def plot(year: int = None):
    year = year or datetime.today().year
    result = get_one_word_popularity(year)
    first_20 = result[-60:]
    # print(' '.join([i[0] for i in first_20[::-1]]))

    plt.rcdefaults()
    labels = [i[0] for i in first_20]
    y_pos = np.arange(len(labels))
    values = [i[1] for i in first_20]

    plt.figure(figsize=(8, 20))
    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:aqua marine')
    plt.yticks(y_pos, labels)
    plt.title(f'Leggyakrabban használt szavak ({year})')
    plt.show()
    # plt.savefig('results/word_popularity.png')
    # plt.close()


if __name__ == '__main__':
    plot()
