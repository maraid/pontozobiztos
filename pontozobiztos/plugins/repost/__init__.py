from pontozobiztos import chatmongo
import fbchat
import imagehash
import logging
import random

log = logging.getLogger('chatbot')


THRESHOLD = 3

all_hashes = []
all_urls = {}

re_strings = ['re', 'Re', 'RE', 'ree', 'REEEE', 'R E P O S T', 'repost',
              'voltmár', 'vót', 'vótmá', 'mótvá']


def init():
    for h in get_all_hashes():
        all_hashes.append((h['_id'], imagehash.hex_to_hash(h['hash'])))
    all_urls.update(get_all_urls())
    log.info(f'Initialized repost with {len(all_hashes)} image hashes'
             f' and {len(all_urls)} urls')


def on_message(thread, author, message: fbchat.MessageData):
    if message.text.startswith('https://'):
        if mid := all_urls.get(message.text):
            thread.send_text(random.choice(re_strings), reply_to_id=message.id)
            thread.send_text('>', reply_to_id=mid)
        all_urls[message.text] = message.id
    elif images := [att for att in message.attachments
                    if isinstance(att, fbchat.ImageAttachment)]:
        msg = get_msg_from_db(message.id)
        attachments = msg['attachments']
        for img in images:
            try:
                db_att = [x for x in attachments if x['uid'] == img.id][0]
            except IndexError:
                log.warning('No image attachment found. This shouldn\'t happen')
                return False
            imghash = imagehash.hex_to_hash(db_att['image_hash'])
            similar = [(mid, val) for mid, h in all_hashes
                       if (val := h - imghash) <= THRESHOLD]

            if similar:
                similar.sort(key=lambda x: x[1])
                best_match = similar[0]
                best_count = len([x for x in similar if x[1] == best_match[1]])
                thread.send_text(random.choice(re_strings) + f' {best_count}x',
                                 reply_to_id=message.id)
                thread.send_text('>', reply_to_id=best_match[0])
            all_hashes.append((message.id, imghash))
        return True
    else:
        return False


def get_msg_from_db(mid):
    msg = chatmongo.get_message_collection()
    cursor = msg.find({'_id': mid})
    return next(cursor)


def get_all_hashes():
    result = chatmongo.get_message_collection().aggregate([
        {'$unwind': '$attachments'},
        {'$match': {'attachments.type': 'image'}},
        {'$replaceWith': {
            '_id': '$_id',
            'hash': '$attachments.image_hash',
        }}
    ])
    return list(result)


def get_all_urls():
    result = chatmongo.get_message_collection().find(
        {'text': {'$regex': 'https://'}}
    )
    return {x['text']: x['_id'] for x in result}


if __name__ == '__main__':
    from PIL import Image
    init()
    imghash = imagehash.phash(Image.open('20180920205858_u100001274083888_mid.$gAADTaOUX9sVsKgyfYFl-MdLnwIWo_a1937288356574368.jpg'))
    similar = [(mid, val) for mid, h in all_hashes
               if (val := h - imghash) <= THRESHOLD]

    print(similar)


