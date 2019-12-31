from pontozobiztos.chatmongo import db
import fbchat
from . import label_image
import logging


logger = logging.getLogger("chatbot")
classifier_decisions = db.classifier_decision

def add_decision(is_kakie, message_id, attachment, response_message_id=None):
    """Adds a document to the classifier_decision collection.

    Args:
        is_kakie (bool): True if the classifier returned that the image
            is a kakie. False otherwise
        message_id (str): fbchat.Message.uid
        attachment (fbchat.ImageAttachment): Message attachment
        response_message_id (str): Message attachment

    Returns:
        bool: True if added to the database, False otherwise
    """
    result = classifier_decisions.insert_one({
        '_id': message_id,
        'response_message_id': response_message_id,
        'img_path': attachment.path if hasattr(attachment, 'path') else None,
        'response_accepted_by': [],
        'response_declined_by': []
    })
    return bool(result.inserted_id)


def get_decision(message_id):
    """Finds the decision on image identified by attachment_id

    Args:
        message_id (str): fbchat.Message.uid
    Returns:
        dict or None
    """
    result = classifier_decisions.find({'_id': message_id})
    try:
        return result.next()
    except StopIteration:
        return None


def get_image_attachment(message):
    """Return a single ImageAttachment gotten from message. If multiple
    ImageAttachments are in message.attachments, Return None, because
    multiple ones could cause problems in the database.

    TODO: can we or even should we use more than one?! Use first?

    Args:
        message (fbchat.Message): message object

    Returns:
        fbchat.ImageAttachment: attachment object
    """
    image_attachments = [att for att in message.attachments
                         if isinstance(att, fbchat.ImageAttachment)]

    if len(image_attachments) != 1:
        return None
    return image_attachments[0]


def on_message(client, author, message):
    """

    Args:
        client:
        author:
        message (fbchat.Message):

    Returns:

    """
    if (message.text == '🚽' and
            message.replied_to and
            get_decision(message.replied_to.uid)):
        classifier_decisions.update_one(
            {'_id': message.replied_to.uid},
            {'$set': {'response_message_id': message.uid},
             '$addToSet': {'response_accepted_by': author.uid}}
        )

    image_attachment = get_image_attachment(message)
    if image_attachment is None:
        return

    try:
        img_path = image_attachment.path
    except AttributeError:
        return

    # run classifier
    is_kakie: bool


async def prediction_test_mode(client, author, message):
    image_attachment = get_image_attachment(message)
    if image_attachment is None:
        return

    img_path = image_attachment.path if hasattr(image_attachment, "path") else None
    if img_path is None:
        return

    result = 1.0 - label_image.predict(img_path)
    logger.info(f"result: {result}")
    await client.send_reply(reply_to_id=message.uid, text="{0:.2f}%".format(result[0][0] * 100))


def on_reaction_added(client, message_id, reaction, user):
    del client
    if reaction.name == 'YES':
        classifier_decisions.update_one(
            {'response_message_id': message_id},
            {'$addToSet': {'response_accepted_by': user.uid}}
        )
    elif reaction.name == 'NO':
        classifier_decisions.update_one(
            {'response_message_id': message_id},
            {'$addToSet': {'response_declined_by': user.uid}}
        )


def on_reaction_removed(client, message_id, user):
    del client
    classifier_decisions.update_one(
        {'response_message_id': message_id},
        {'$pull': {'response_accepted_by': user.uid}}
    )
    classifier_decisions.update_one(
        {'response_message_id': message_id},
        {'$pull': {'response_declined_by': user.uid}}
    )
