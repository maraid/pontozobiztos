"""MongoHelper is the main wrapper for the MongoDB server. Basic
chat functions are defined here, but feel free to write your own
queries or use different collections.
"""

import pymongo
from datetime import datetime
import logging
from pontozobiztos import utils
from fbchat import ImageAttachment, ShareAttachment, Attachment
from fbchat import Message, Mention, MessageReaction

logger = logging.getLogger("chatbot.chatmongo")

client = pymongo.MongoClient('mongodb://mongo:27017')
db = client.chat
user_coll = db.users
message_coll = db.messages


def get_database():
    """Return chat database"""
    return db


def get_user_collection():
    """Returns user collection from chat database"""
    return user_coll


def get_message_collection():
    """Return message collection from chat database"""
    return message_coll


# USER FUNCTIONS

def get_user(user_id):
    """Returns user document. None if not found.

    Args:
        user_id (str): facebook user_id

    Returns:
        dict: The matched user document from the db.
            (None if not found)
    """
    try:
        return user_coll.find({"_id": user_id}).next()
    except StopIteration:
        return None


def get_user_info(user_id):
    """Returns basic information about a user:
        - fullname
        - nickname

    Args:
        user_id (str): facebook user_id

    Returns:
        dict: user information
    """
    try:
        return user_coll.find({'_id': user_id},
                              {'_id': 1,
                               'fullname': 1,
                               'nickname': 1,
                               'last_read_at': 1,
                               'is_admin': 1
                               }
                              ).next()
    except StopIteration:
        return None


def get_user_ids():
    """Returns a list of all user ids in the db.

    Returns:
        list: list of user_ids as strings.
    """
    pipeline = [{'$group': {'_id': 1, 'ids': {'$addToSet': '$_id'}}}]
    try:
        return user_coll.aggregate(pipeline).next()['ids']
    except StopIteration:
        return []


def update_or_add_user(user_id, fullname, nickname, last_read_at=None):
    """Adds a new user to the db if not exists already.

    Args:
        user_id (str): facebook user_id
        nickname (str): Chat nickname
        fullname (str): fullname of user
        last_read_at (datetime): last date when the thread was
            read by the user. (Epoch by default)

    Returns:
        bool: True if changes were made, False otherwise
    """
    last_read_at = last_read_at or datetime.utcfromtimestamp(0)

    update = user_coll.update_one({'_id': user_id},
                                  {'$set': {
                                    'fullname': fullname,
                                    'nickname': nickname,
                                    'last_read_at': last_read_at,
                                    'is_admin': False
                                  },
                                  '$setOnInsert': {
                                      'points': [],
                                      'multipliers': []
                                  }},
                                  upsert=True)

    upserted = bool(update.upserted_id)
    if upserted:
        logger.info(f"New user was added to the database with name: {fullname},"
                    f" id: {user_id}")
    modified = bool(update.modified_count)
    if modified:
        logger.info(f"Existing user '{fullname}' (id: {user_id}) was updated")

    return upserted or modified


def update_info(user_id, field, value):
    """Updates a single user field.

    Args:
        user_id: facebook user_id
        field: name of the field to update
        value: value of the field to replace to

    Returns:
        bool: True if successful, False otherwise
    """
    update = user_coll.update_one({'_id': user_id},
                                  {'$set': {
                                      field: value
                                  }})
    return bool(update.modified_count)


def get_points(user_id, from_date=None, to_date=None):
    """Return a list of points with all the data between from_date
    and to_date.

    Args:
        user_id (str): facebook  user_id
        from_date (datetime): date to return points from
        to_date (datetime): date to return points until

    Returns:
        list: list of dicts of points (empty list if not found)
    """
    from_date = from_date or utils.get_season_start()
    to_date = to_date or utils.get_season_end()

    pipeline = [
        {'$match': {'_id': user_id}},
        {'$project': {'points': 1}},
        {'$unwind': '$points'},
        {'$project': {
            'points': 1,
            'is_between_dates': {
                '$allElementsTrue': [
                    [
                        {'$gte': ['$points.timestamp', from_date]},
                        {'$lt': ['$points.timestamp', to_date]}
                    ]
                ]
            }
        }},
        {'$match': {'is_between_dates': True}},
        {'$group': {
            '_id': None,
            'points': {'$push': '$points'}
        }}
    ]
    try:
        return user_coll.aggregate(pipeline).next()["points"]
    except StopIteration:
        return []


def get_points_sum(user_id: str, from_date=None, to_date=None):
    """Calculates the sum of points between from_date and to_date

    Args:
        user_id (str): facebook user_id
        from_date (datetime): starting date to sum from
        to_date (datetime): end of date to sum until

    Returns:
        float: Sum of points (from_date - to_date)
            (None if not found)
    """
    from_date = from_date or utils.get_season_start()
    to_date = to_date or utils.get_season_end()

    pipeline = [
        {'$match': {'_id': user_id}},
        {'$project': {'points': 1}},
        {'$unwind': '$points'},
        {'$project': {
            'points': 1,
            'is_between_dates': {
                '$allElementsTrue': [
                    [
                        {'$gte': ['$points.timestamp', from_date]},
                        {'$lt': ['$points.timestamp', to_date]}
                    ]
                ]
            }
        }},
        {'$match': {'is_between_dates': True}},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$points.value'}
        }}
    ]
    try:
        return user_coll.aggregate(pipeline).next()["total"]
    except StopIteration:
        return 0


def add_points(user_id, value, source, ts=None, mid=None, desc=""):
    """Adds point entry to a user specified by user_id

    Args:
        user_id (str): facebook user_id
        value (float): amount of points to add
        source (str): source of points (source module name)
        ts (datetime): timestamp of addition (default: now)
        mid (str): facebook message_id
        desc (str): description

    Returns:
        bool: True if addition is successful, otherwise False
    """
    ts = ts or datetime.today()

    update = user_coll.update_one(
        {'_id': user_id},
        {'$push': {
            'points': {
                'value': value,
                'source': source,
                'timestamp': ts,
                'description': desc,
                'mid': mid
            }
        }}
    )
    return bool(update.modified_count)


def set_multiplier(user_id, value, typename, expiration_date):
    """Adds a new, or alters an existing multiplier.

    Args:
        user_id (str): facebook user_id
        value (float): multiplication factor
        typename (str): type of the multiplier
        expiration_date (datetime): expiration date of the
            multiplier

    Returns:
        bool: True if multiplier was set, False otherwise
    """
    update = user_coll.update_one(
        {'_id': user_id,
         'multipliers.typename': {'$ne': typename}},
        {'$push': {
            'multipliers': {
                'typename': typename,
                'value': value,
                'expiration_date': expiration_date,
            }
        }},
    )
    if not update.modified_count:
        update = user_coll.update_one(
            {'_id': user_id,
             'multipliers.typename': typename},
            {'$set': {
                'multipliers.$.expiration_date': expiration_date,
                'multipliers.$.value': value
            }}
        )
    return bool(update.modified_count)


def get_multipliers(user_id, include_expired=False):
    """Returns a list of multiplier documents.

    Args:
        user_id (str): facebook user_id
        include_expired (bool): Returns all multipliers if True,
            returns only the currently active ones otherwise.
     Returns:
        list: list of multipliers (empty list if not found)
     """
    pipeline = [
        {'$match': {'_id': user_id}},
        {'$project': {'multipliers': 1}},
        {'$unwind': '$multipliers'},
        {'$project': {
            'multipliers': 1,
            'is_active': {
                '$or': [
                        {'$gte': ['$multipliers.expiration_date',
                                  datetime.now()]},
                        include_expired
                ]
            }
        }},
        {'$match': {'is_active': True}},
        {'$group': {
            '_id': None,
            'multipliers': {'$push': '$multipliers'}
        }}
    ]
    try:
        return user_coll.aggregate(pipeline).next()["multipliers"]
    except StopIteration:
        return []


def set_last_read_at(user_id, last_read_at=None):
    """Sets last_read_at field for a user to a date.

    Args:
        user_id (str): facebook user id
        last_read_at (datetime): time when the user last read the thread
    """
    last_read_at = last_read_at or datetime.today
    update_info(user_id, 'last_read_at', last_read_at)


def get_admin_stats(user_id):
    """Returns the admin status of the specified user.

    Args:
        user_id (str): facebook user id

    Returns:
        bool: True if user is admin, False otherwise
    """
    return get_user_info(user_id).get('is_admin', False)


# MESSAGE FUNCTIONS

def deserialize_message(data):
    """Deserializes message from mongodb document to fbchat.Message.

    Args:
        data (dict): dictionary containing message fields.

    Returns:
        Message: Message object read from the db.
    """
    def deserialize_mentions(*mentions):
        return [Mention(thread_id=mnt.get('thread_id'),
                        offset=mnt.get('offset'),
                        length=mnt.get('length')) for mnt in mentions]

    def deserialize_reactions(*reactions):
        return [MessageReaction[reaction] for reaction in reactions]

    def deserialize_attachments(*attachments):
        rtn = []
        for att in attachments:
            if att.get('type') == 'share':
                att_obj = ShareAttachment(
                    title=att.get('title'),
                    original_url=att.get('original_url')
                )
            elif att.get('type') == 'image':
                att_obj = ImageAttachment(
                    original_extension=att.get('original_extension'),
                    large_preview_url=att.get('large_preview_url'),
                    large_preview_height=att.get('large_preview_height'),
                    large_preview_width=att.get('large_preview_width')
                )
                att_obj.path = att.get('path')
            else:
                att_obj = Attachment()
            att_obj.uid = att.uid
            rtn.append(att_obj)
        return rtn

    msg = Message(
        text=data.get('text'),
        mentions=deserialize_mentions(*data.get('mentions')),
        attachments=deserialize_attachments(*data.get('attachments')),
        sticker=data.get('sticker')
    )
    msg.uid = data.get('_id')
    msg.author = data.get('author')
    msg.created_at = data.get('created_at')
    # msg.is_read = data.get('is_read')
    # msg.read_by = data.get('read_by')
    msg.reactions = deserialize_reactions(*data.get('reactions'))
    replied_to_message = Message()
    replied_to_message.uid = data.get('replied_to_id')
    msg.replied_to = replied_to_message
    msg.unsent = data.get('unsent')
    return msg


def get_messages_by_user_ids(*user_ids, from_date=None, to_date=None):
    """Retrieves the messages that the user sent between from_date
     and to_date.

    Args:
        user_ids (str): facebook user_ids
        from_date (datetime): date to include messages from
        to_date (datetime): date to include messages until

    Returns:
        list: list of messages (empty list if none found)
    """
    from_date = from_date or utils.get_season_start()
    to_date = to_date or utils.get_season_end()

    query = {'created_at': {'$gte': from_date, '$lte': to_date}}

    if user_ids:
        query.update({'author': {'$in': user_ids}})

    try:
        return [deserialize_message(msg) for msg in message_coll.find(query)]
    except StopIteration:
        return []


def get_messages_by_mid(*mids):
    """Queries messages by message uids. If you want to get all messages
    in a period of time, use get_messages_by_user_ids().

    Args:
        mids (str): facebook message ids

    Returns:
        list: List of fbchat.Message objects
    """
    return [deserialize_message(msg) for msg in
            message_coll.find({'_id': {'$in': mids}})]


def insert_or_update_message(message_object):
    """Adds a message the user with text and image.

    Args:
        message_object (Message): facebook user_id
    """
    def serialize_reactions(*reactions):
        return {uid: reaction.name for uid, reaction in reactions}

    def serialize_mentions(*mentions):
        return {mention.thread_id: {
            'offset': mention.offset,
            'length': mention.length
        } for mention in mentions}

    def serialize_attachments(*attachments):
        rtn = []
        for att in attachments:
            att_dict = {'uid': att.uid}
            if isinstance(att, ShareAttachment):
                att_dict.update({
                    'type': 'share',
                    'title': att.title,
                    'original_url': att.original_url
                })
            elif isinstance(att, ImageAttachment):
                att_dict.update({
                    'type': 'image',
                    'path': (att.path if hasattr(att, 'path') else None),
                    'original_extension': att.original_extension,
                    'large_preview_url': att.large_preview_url,
                    'large_preview_height': att.large_preview_height,
                    'large_preview_width': att.large_preview_width
                })
            else:  # TODO: do the rest?!
                att_dict['type'] = 'other'
            rtn.append(att_dict)
        return rtn

    message_object.created_at = message_object.created_at or datetime.now()
    update = message_coll.update_one(
        {'_id': message_object.uid},
        {'$set': {
            'text': message_object.text,
            'mentions': serialize_mentions(*message_object.mentions),
            'author': message_object.author,
            'created_at': message_object.created_at,
            # 'is_read': message_object.is_read,
            # 'read_by': message_object.read_by,
            'reactions': serialize_reactions(*message_object.reactions),
            'sticker': None,
            'attachments': serialize_attachments(*message_object.attachments),
            'replied_to': message_object.replied_to.uid if message_object.replied_to else None,
            'unsent': message_object.unsent,
         }},
        upsert=True
    )
    return not bool(update.matched_count)


def mark_message_as_deleted(mid):
    """Marks a message as deleted.

    Args:
        mid (str): facebook message_id

    Returns:
        bool: True if successful, false otherwise.

    Notes:
        The message won't actually be deleted from the storage
    """
    update = message_coll.update_one(
        {'_id': mid},
        {'$set': {'unsent': True}}
    )
    return bool(update.modified_count)


def add_reaction(mid, reaction_author, reaction):
    """Adds a reaction to a message. Type of reaction is not saved,
    you have to use the facebook API to get that information.
    The message gets added to the database if it hasn't been before.

    Args:
        mid (str): facebook message_id
        reaction_author (str): facebook user_id of the react owner
        reaction (MessageReaction): Message reaction object.
    Returns:
        bool: True if reaction was added successfully,
            False otherwise
    """
    result = message_coll.update_one(
        {'_id': mid},
        {'$set': {
            f'reactions.{reaction_author}': reaction.name
        }},
    )
    return bool(result.modified_count)


def remove_reaction(mid, reaction_author):
    """Removes a reaction from a message.

    Args:
        mid: facebook message id
        reaction_author: facebook user_id of the reaction author

    Returns:
        bool: True if the reaction was successfully removed,
            False otherwise.
    """
    result = message_coll.update_one(
        {'_id': mid},
        {'$unset': {
            f'reactions.{reaction_author}': 1,
        }}
    )
    return bool(result.modified_count)

# TODO: might be worth doing something like this later
# def read_message(mid, user_id):
#     """Marks a message (mid) as read by user (user_id)
#
#     Args:
#         mid (str): facebook message id
#         user_id (str): facebook user id
#
#     Returns:
#         bool: True of success, False otherwise
#     """
#     result = message_coll.update_one(
#         {'_id': mid},
#         {'$addToSet': {
#             'read_by': user_id
#         }}
#     )
#     return bool(result.modified_count)
