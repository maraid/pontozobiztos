import unidecode
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from pontozobiztos import chatmongo
from pontozobiztos import utils


msg_col = chatmongo.get_message_collection()
WORD_LIST = [
    'zoli', 'zoltan', 'amfetamin',
    'labda', 'latyo', 'laszti', 'extasy', 'mdma', 'kristaly',
    'fuvez', 'moki', 'besziv', 'marihuana', 'hasis',
    'cetli', 'papir', 'belyeg', 'lsd', 'acid', 'gomba'
    'drog', 'kabszi', 'kabitoszer',
]


def get_one_word_popularity(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_one_word_popularity(start, end)


def _get_one_word_popularity(start, end) -> List[Tuple]:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}}
    ])
    unique_domains_dct = {}
    for item in list(result):
        for word in WORD_LIST:
            if item['text'] and word in unidecode.unidecode(item['text'].lower()):
                try:
                    unique_domains_dct[word] += 1
                except KeyError:
                    unique_domains_dct[word] = 1
    print(unique_domains_dct)
    unique_domains = unique_domains_dct.items()
    return sorted(unique_domains, key=lambda i: i[1])


def plot(year: int = None):
    year = year or datetime.today().year
    result = get_one_word_popularity(year)
    first_20 = result[-30:]
    print(' '.join([i[0] for i in first_20[::-1]]))

    plt.rcdefaults()
    labels = [i[0] for i in first_20]
    y_pos = np.arange(len(labels))
    values = [i[1] for i in first_20]

    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:aqua marine')
    plt.yticks(y_pos, labels)
    plt.title(f'"Bizonyos" szavak száma ({year})')
    plt.subplots_adjust(left=0.2)
    plt.show()
    # plt.savefig('results/weird_word_popularity.png')
    # plt.close()


if __name__ == '__main__':
    plot()
