from pontozobiztos import chatmongo
import re

msg_coll = chatmongo.get_message_collection()

# cursor = msg_coll.find({'text': re.compile(r'^https://[w\.]*youtube\.com[^\s]*$')})
cursor = msg_coll.find({'text': re.compile(r'^https://youtu\.be/[^\s]*$')})
# cursor = msg_coll.find({'text': re.compile(r'^https://music.youtube\.com/watch[^\s]*$')})
# cursor = msg_coll.find({'text': re.compile(r'^https://open.spotify\.com/track[^\s]*$')})
msgs = [x for x in cursor]
msgs.sort(key=lambda x: x['created_at'], reverse=True)
with open('../plugins/link_mirror/youtube_links.txt', 'a') as f:
    for m in msgs:
        try:
            f.write(m['text'] + '\n')
        except UnicodeEncodeError:
            pass
