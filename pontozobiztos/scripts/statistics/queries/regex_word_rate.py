from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from pontozobiztos.scripts.statistics.queries.messages_per_user import get_messages_per_user_by_year
from pontozobiztos.scripts.statistics.queries.regex_per_user import get_regex_sent_count_per_user


def _plot(regex, title, year: int = None):
    year = year or datetime.today().year
    sent = get_messages_per_user_by_year(year)
    matched = get_regex_sent_count_per_user(regex, year)

    result = []
    for item in matched:
        sent_item = [i for i in sent if i['fullname'] == item['fullname']][0]
        result.append({'fullname': item['fullname'],
                       'rate': item['document_count'] / sent_item['document_count']})
    result.sort(key=lambda i: i['rate'])

    labels = [i['fullname'] for i in result]
    values = [i['rate'] for i in result]
    y_pos = np.arange(len(labels))

    # fig, ax = plt.subplots(nrows=1, ncols=1)
    plt.rcdefaults()
    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:teal')
    plt.yticks(y_pos, labels)
    plt.title(f'{title} ({year})')
    # plt.set_facecolor('xkcd:salmon')
    plt.subplots_adjust(left=0.3)
    # plt.savefig(f'results/regex_rate_{"-".join(regex)}.png')
    # plt.close()
    plt.show()


def plot(year: int = None):
    _plot(['^[^ ]+ [^ ]+$'], '(egyszavas üzenet)/(összes üzenet)', year)


if __name__ == '__main__':
    _plot(['^[^ ]+ [^ ]+ [^ ]+$'], 'háromszavas per összes megvan a sweetspot amivel lehet mollit basztatni')  # one word
