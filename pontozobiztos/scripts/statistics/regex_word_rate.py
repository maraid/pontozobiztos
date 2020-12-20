from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from pontozobiztos.scripts.statistics.messages_per_user import get_messages_per_user_by_year
from pontozobiztos.scripts.statistics.regex_per_user import get_regex_sent_count_per_user


def plot(regex, year: int = None):
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

    plt.rcdefaults()
    plt.barh(y_pos, values, align='center', alpha=0.5)
    plt.yticks(y_pos, labels)
    # plt.title(f'{title} ({year})')
    plt.subplots_adjust(left=0.3)
    plt.show()


if __name__ == '__main__':
    plot(['^[ ]*$'])
