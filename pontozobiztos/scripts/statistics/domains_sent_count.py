import re
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

from pontozobiztos import chatmongo
from pontozobiztos import utils


msg_col = chatmongo.get_message_collection()


def get_domains_sent_count(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_domains_sent_count(start, end)


def _get_domains_sent_count(start, end) -> List[Tuple]:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {"$addFields": {"url": {"$regexMatch": {"input": "$text", "regex": "https://"}}}},
        {"$match": {"url": True}}
    ])
    unique_domains_dct = {}
    for item in list(result):
        if match := re.search(r'https://([^/?\s]*)', item['text']):
            try:
                unique_domains_dct[match.group(1)] += 1
            except KeyError:
                unique_domains_dct[match.group(1)] = 1
    unique_domains = unique_domains_dct.items()
    return sorted(unique_domains, key=lambda i: i[1])


def plot(year: int = None):
    year = year or datetime.today().year
    result = get_domains_sent_count(year)
    first_20_and_other = result[-20:]
    first_20_and_other.insert(
        0, (f'egyéb össz. ({len(result[:-20])} db)',
            sum(i[1] for i in result[:-20])))

    plt.rcdefaults()
    labels = [i[0] for i in first_20_and_other]
    y_pos = np.arange(len(labels))
    values = [i[1] for i in first_20_and_other]

    plt.barh(y_pos, values, align='center', alpha=0.5)
    plt.yticks(y_pos, labels)
    plt.title(f'Leggyakrabban linkelt oldalak ({year})')
    plt.subplots_adjust(left=0.3)
    plt.show()


if __name__ == '__main__':
    plot()
