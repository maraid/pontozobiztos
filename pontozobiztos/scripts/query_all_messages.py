import fbchat
import dotenv
import os
import pickle
import logging
import time
import random
from pontozobiztos import chatmongo
import datetime

logging.basicConfig(level=logging.DEBUG)
dotenv.load_dotenv("../../.env")

GROUP_ID = '232447473612485'

try:
    with open("/chatbot_data/cookies", "rb") as cookies:
        session_cookies = pickle.load(cookies)
except (FileNotFoundError, pickle.UnpicklingError, EOFError):
    session_cookies = None

if session_cookies:
    session = fbchat.Session.from_cookies(session_cookies)
else:
    session = fbchat.Session.login(
        os.getenv("EMAIL"), os.getenv("PASSWORD"))

with open("cookie", "wb") as cookies:
    pickle.dump(session.get_cookies(), cookies)

thread = fbchat._threads.Group(session=session, id=GROUP_ID)

before = None
def main():
    global before
    data = thread._fetch_messages(10, before)
    for msg in data:
        chatmongo.insert_or_update_message(msg)
    before = data[0].created_at
    time.sleep(random.uniform(0, 3))

retries = 0
while True:
    if retries == 3:
        retries = 0
        print("Retries exceeded limit. Sleeping for an hour. Starting at: "
              + str(datetime.datetime.now()))
        time.sleep(3600)
    try:
        main()
    except Exception as e:
        print(str(e))
        retries += 1
        print("ERROR trying again #" + str(retries))
        time.sleep(5 * 60)
        continue
    retries = 0
# a = client.fetchUserInfo('100000287377073')
# print(a)
# print(res)
# print(type(res))
# pprint(dict(res['232447473612485']), width=1, indent=4)


