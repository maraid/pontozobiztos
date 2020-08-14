from pontozobiztos import chatmongo
import re

def most_messages_toplist():
    res = chatmongo.get_message_collection().aggregate([
        {"$sort": {"author": 1}},
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {
            "$lookup":
            {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_data"
            }
        },
        {"$unwind": "$user_data"}
    ], allowDiskUse=True)
    return [x for x in res]


def print_most_messages_top3():
    for i, user in enumerate(most_messages_toplist()[:3]):
        print(str(i + 1) + ". " + user["user_data"]["fullname"] + ": " + str(user["count"]))


def _first_message_from_each_user():
    msg_col = chatmongo.get_message_collection()
    ret = msg_col.aggregate(
        [
            {"$sort": {"timestamp": 1}},
            {"$group":
                {
                    "_id": "$author",
                    "timestamp": {"$first": "$created_at"}
                }},
            {"$sort": {"timestamp": 1}},
            {"$lookup":
                {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_data"
                }},
            {"$unwind": "$user_data"},
            {
                "$replaceWith":
                    {
                        "_id": "$_id",
                        "timestamp": "$timestamp",
                        "fullname": "$user_data.fullname"
                    }
            }
        ],
        allowDiskUse=True
    )
    return [x for x in ret]


def who_joined_last_3():
    users = _first_message_from_each_user()[-3:]
    for i, user in enumerate(reversed(users)):
        print(str(i + 1) + ". " + user.get("fullname") + ": " + str(user.get("timestamp")))


def _number_of_reacts_per_user():
    msg_col = chatmongo.get_message_collection()
    ret =msg_col.aggregate([
        {"$project":
            {
                "_id": 1,
                "author": 1,
                "reactions": {"$objectToArray": "$reactions"}
            }
        },
        {"$unwind": "$reactions"},
        {"$sort": {"reactions.k": 1}},
        {
            "$group":
            {
                "_id": "$reactions.k",
                "react_count":
                {
                    "$sum": 1
                }
            }
        },
        {"$lookup":
            {
              "from": "users",
              "localField": "_id",
              "foreignField": "_id",
              "as": "user_data"
            }},
        {"$unwind": "$user_data"},
        {
            "$replaceWith":
            {
                "_id": "$_id",
                "react_count": "$react_count",
                "fullname": "$user_data.fullname"
            }
        },
        {"$sort": {"react_count": -1}}
    ], allowDiskUse=True)
    return [x for x in ret]


def who_sent_the_most_reacts_top3():
    users = _number_of_reacts_per_user()[:3]
    for i, user in enumerate(users):
        print(str(i + 1) + ". " + user.get("fullname") + ": " + str(user.get("react_count")))


def _count_reacts_per_message(initial_filter=None, limit=None):
    initial_filter = initial_filter or []
    res = chatmongo.get_message_collection().aggregate(initial_filter + [
        {"$project":
            {
                "_id": 1,
                "author": 1,
                "reactions": {"$objectToArray": "$reactions"}
            }
        },
        {"$unwind": "$reactions"},
        {"$sort": {"_id": 1}},
        {
            "$group":
                {
                    "_id": "$_id",
                    "react_count": {"$sum": 1}
                }
        },
        {"$sort": {"react_count": -1}},
        {"$limit": 20},
        {
            "$lookup":
                {
                    "from": "messages",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "msg_data"
                }
        },
        {
            "$lookup":
                {
                    "from": "users",
                    "localField": "msg_data.author",
                    "foreignField": "_id",
                    "as": "user_data"
                }
        },
        {"$unwind": "$user_data"},
        {"$unwind": "$msg_data"},
    ], allowDiskUse=True)
    return res


def get_image_filter():
    """filter for _count_reacts_per_message()"""
    return [{"$match": {"attachments.type": "image"}}]


def get_text_filter():
    """filter for _count_reacts_per_message()"""
    return [
        {
            "$match":
            {
                "$and":
                [
                    {"attachments": []},
                    {"text": {"$ne": [""]}}
                ]
            }
        }
    ]


def _most_reacts_received_toplist(react_type=None):
    """React type can be:
        - SMILE
        - ANGRY
        - SAD
        - HEART
        ....
    """

    pipeline = [
        {
            "$project":
                {
                    "_id": 1,
                    "author": 1,
                    "reactions": {"$objectToArray": "$reactions"}
                }
        },
        {"$unwind": "$reactions"}
    ]

    if react_type:
        pipeline += [{"$match": {"reactions.v": react_type}}]

    pipeline += [
        {"$sort": {"author": 1}},
        {"$group":
            {
                "_id": "$author",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {
            "$lookup":
                {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_data"
                }
        },
        {"$unwind": "$user_data"}

    ]
    res = chatmongo.get_message_collection().aggregate(pipeline,
                                                       allowDiskUse=True)
    return [x for x in res]


def print_who_received_the_most_reacts_top3(react_type=None):
    users = _most_reacts_received_toplist(react_type)
    for i, user in enumerate(users[:3]):
        print(str(i + 1) + ". " + user["user_data"]["fullname"] + ": " + str(user["count"]))


def kicsekk_count():
    res = chatmongo.get_message_collection().aggregate([
        {"$addFields": {"kicsekk": {"$regexMatch": {"input": "$text", "regex": "kicsekk"}}}},
        {"$match": {"kicsekk": True}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    return res.next()["count"]


def kicsekkjel_count():
    res = chatmongo.get_message_collection().aggregate([
        {"$addFields": {"kicsekkjel": {"$regexMatch": {"input": "$text", "regex": r"<>"}}}},
        {"$match": {"kicsekkjel": True}},
        {"$group": {"_id": None, "count": {"$sum": 1}}}
    ])
    return res.next()["count"]


if __name__ == "__main__":
    print("Most messages sent TOP3")
    print_most_messages_top3()

    print("\nLast 3 joined")
    who_joined_last_3()

    print("\nMost reacts sent by TOP3")
    who_sent_the_most_reacts_top3()

    print("\nMost reacts received TOP3")
    print_who_received_the_most_reacts_top3()

    print("\nMost angry reacts received TOP3")
    print_who_received_the_most_reacts_top3("ANGRY")

    print("\nMost sad reacts received TOP3")
    print_who_received_the_most_reacts_top3("SAD")

    print("\nMost <3 reacts received TOP3")
    print_who_received_the_most_reacts_top3("HEART")

    print("\nMost smile reacts received TOP3")
    print_who_received_the_most_reacts_top3("SMILE")

    print("\nkicsekk count")
    print(kicsekk_count())

    print("\nkicsekkjel count")
    print(kicsekkjel_count())

    # who_sent_the_most_reacts()

    # print([x for x in _count_reacts_per_message(get_image_filter())])
    # print([x for x in _count_reacts_per_message(get_text_filter())])