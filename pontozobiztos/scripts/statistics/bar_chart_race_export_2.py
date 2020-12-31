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
        {'$group': {'_id': {'user_id': '$author',
                            'dayOfYear': {'$dayOfYear': '$created_at'}},
                    'document_count': {'$sum': 1}}},
        {"$replaceWith": {
            "_id": "$_id.user_id",
            "dayOfYear": "$_id.dayOfYear",
            "document_count": "$document_count",
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "_id",
            "as": "user_data"
        }},
        {"$unwind": "$user_data"},
        {"$replaceWith": {
            "_id": "$_id",
            "document_count": "$document_count",
            "dayOfYear": "$dayOfYear",
            "fullname": "$user_data.fullname"
        }},
        {'$sort': {'dayOfYear': 1}}
    ])
    result_list = list(result)
    for item in result_list:
        item['date'] = utils.day_of_year_to_date(start.year, item['dayOfYear'])
        del item['dayOfYear']
        del item['_id']

    user_res = list(chatmongo.get_user_collection().find({}))
    user_list = [x['fullname'] for x in user_res]
    user_count = len(user_list)

    cumulative_sums = {fullname: 0 for fullname in user_list}
    used_dates = []
    sum_result = []
    for item in result_list:
        if item['date'] not in used_dates:
            used_dates.append(item['date'])
            for name, count in cumulative_sums.items():
                sum_result.append({
                    'date': item['date'],
                    'fullname': name,
                    'count': count
                })

        item_in_sum = [x for x in sum_result[-user_count:] if x['fullname'] == item['fullname']][0]
        item_in_sum['count'] += item['document_count']
        cumulative_sums[item['fullname']] = item_in_sum['count']

    another_result_dict = {x: [] for x in user_list}  # this one will act as a table for flourish

    for item in sum_result:
        another_result_dict[item['fullname']].append(item['count'])

    date_list = sorted(list({x['date'] for x in sum_result}))
    date_str_list = [x.strftime('%Y-%m-%d') for x in date_list]
    with open('results/flourish.csv', 'w', encoding='utf-8') as f:
        f.write(','.join(['Fullname', 'Image URL', *date_str_list]))
        f.write('\n')
        for name, count_list in another_result_dict.items():
            image_url = [x['profile_picture'] for x in user_res if x['fullname'] == name][0]
            f.write(','.join([name, image_url, *[str(i) for i in count_list]]))
            f.write('\n')


def export(year: int = None):
    year = year or datetime.today().year
    result = get_messages_per_user_by_year(year)
    #
    # with open('results/bar_chart_race_data.csv', 'w', encoding="utf-8") as f:
    #     for item in result:
    #         f.write(', '.join([
    #             item['date'].strftime('%Y-%m-%d'),
    #             item['fullname'],
    #             str(item['count'])
    #         ]))
    #         f.write('\n')

    # plt.rcdefaults()
    # labels = [i['fullname'] for i in result]
    # y_pos = np.arange(len(labels))
    # values = [i['document_count'] for i in result]
    #
    # plt.barh(y_pos, values, align='center', alpha=0.5, color='xkcd:dusty blue')
    # plt.yticks(y_pos, labels)
    # plt.title(f'Üzenetek száma per fő ({year})')
    # plt.subplots_adjust(left=0.3)
    # plt.savefig('results/messages_per_user.png')
    # plt.close()
    # plt.show()


if __name__ == '__main__':
    export()
