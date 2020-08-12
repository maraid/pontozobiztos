from pontozobiztos import chatmongo


def _first_message_of_each():
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


def who_joined_last():
    user = _first_message_of_each()[-1]
    print(user.get("fullname"), user.get("timestamp"))



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
        {"$sort": {"author": 1}},
        {
            "$group":
            {
                "_id": "$author",
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
        {"$sort": {"react_count": 1}}
    ],
        allowDiskUse=True)
    return [x for x in ret]


def who_sent_the_most_reacts():
    user = _number_of_reacts_per_user()[-1]
    print(user.get("fullname"), user.get("react_count"))



if __name__ == "__main__":
    who_joined_last()
    who_sent_the_most_reacts()
