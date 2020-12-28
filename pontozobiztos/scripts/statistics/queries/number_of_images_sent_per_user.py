from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from pontozobiztos import chatmongo
from pontozobiztos import utils

from pontozobiztos.scripts.statistics.queries.messages_per_user import get_messages_per_user_by_year

msg_col = chatmongo.get_message_collection()


def get_number_of_images_per_user_by_year(year: int = None):
    start, end = utils.year_start_end(year)
    return _get_number_of_images_per_user(start, end)


def _get_number_of_images_per_user(start, end) -> list:
    result = msg_col.aggregate([
        {'$match': {'created_at': {'$gte': start, '$lte': end}}},
        {'$unwind': '$attachments'},
        {'$match': {'attachments.type': 'image'}},
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


def plot_all(year: int = None):
    year = year or datetime.today().year
    result = get_number_of_images_per_user_by_year(year)

    plt.rcdefaults()
    labels = [i['fullname'] for i in result]
    y_pos = np.arange(len(labels))
    values = [i['document_count'] for i in result]

    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:puke green')
    plt.yticks(y_pos, labels)
    plt.title(f'Küldött képek száma ({year})')
    plt.subplots_adjust(left=0.3)
    plt.savefig('results/number_of_messages.png')
    # plt.show()
    plt.close()


def plot_rate(year: int = None):
    year = year or datetime.today().year
    result_img_count = get_number_of_images_per_user_by_year(year)
    result_msg_count = get_messages_per_user_by_year(year)
    result = []
    for img_item in result_img_count:
        user_total_message_count = [i for i in result_msg_count if i['fullname'] == img_item['fullname']][0]['document_count']
        result.append({'fullname': img_item['fullname'],
                       'rate': img_item['document_count'] / user_total_message_count})
    result.sort(key=lambda i: i['rate'])
    plt.rcdefaults()
    labels = [i['fullname'] for i in result]
    y_pos = np.arange(len(labels))
    values = [i['rate'] for i in result]

    plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:puke green')
    plt.yticks(y_pos, labels)
    plt.title(f'képek száma / összes üzenetek száma ({year})')
    plt.subplots_adjust(left=0.3)
    plt.savefig('results/rate_of_images.png')
    # plt.show()
    plt.close()


def plot(year: int = None):
    plot_all(year)
    plot_rate(year)


if __name__ == '__main__':
    plot()
