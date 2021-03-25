from pontozobiztos import chatmongo
import fbchat
import imagehash
import logging
import random
import requests
from PIL import Image

log = logging.getLogger('chatbot')


re_strings = ['Olvasni kéne', 'Voltmár', 'REEEEEEE', 'vótmá',
              'vót', 'R E P O S T', 're', 'mámegint?', 'hányszor fogod még?',
              'a következőnél elnáspángollak', 'utolsó lövésed volt',
              'irány a gulág', 'Olvasni kéne a chatet', 'Ez már volt',
              'finoooom repost']


def random_reply():
    if random.randint(0, 1) == 0:
        return random.choice(re_strings)
    else:
        votma_list = [c for c in 'vótmá']
        random.shuffle(votma_list)
        return ''.join(votma_list)


def init():
    pass


def on_message(thread, author, message: fbchat.MessageData):
    if images := [att for att in message.attachments
                    if isinstance(att, fbchat.ImageAttachment)]:
        for img in images:
            if img.original_extension == 'gif':
                continue

            try:
                msg_in_db = next(chatmongo.get_message_collection().find({'_id': message.id}))
                img_hash = next(att for att in msg_in_db['attachments'] if att['uid'] == img.id)['image_hash']
            except (StopIteration, KeyError):
                # if not in db (different chat), download again
                largest_image = sorted(list(img.previews),
                                       key=lambda i: i.width or 0)[-1]
                img = Image.open(requests.get(largest_image.url, stream=True).raw)
                img_hash = str(imagehash.phash(img))

            reposts = find_reposts(img_hash)
            reposts = [rep for rep in reposts if rep['_id'] != message.id]

            if reposts:
                thread.send_text(f'{random_reply()} x{len(reposts)}',
                                 reply_to_id=reposts[0]['_id'])

        return True
    else:
        return False


def find_reposts(image_hash):
    result = chatmongo.get_message_collection().aggregate([
        {'$unwind': '$attachments'},
        {'$match': {'attachments.type': 'image'}},
        {'$match': {'attachments.image_hash': image_hash}},
        {'$replaceWith': {
            '_id': '$_id',
            'hash': '$attachments.image_hash',
            'created_at': '$created_at'
        }},
        {'$sort': {'created_at': 1}}
    ])
    return list(result)


if __name__ == '__main__':
    from PIL import Image
    init()
    imghash = imagehash.phash(Image.open('20180920205858_u100001274083888_mid.$gAADTaOUX9sVsKgyfYFl-MdLnwIWo_a1937288356574368.jpg'))
    print(find_reposts(str(imghash)))
