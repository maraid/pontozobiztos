from . import chatmongo
from . import plugins
from .models import User
import importlib
import logging
import fbchat
import os
import pickle
from datetime import datetime
import time
import random
import pytz
import pathlib
from dotenv import load_dotenv
load_dotenv()

utc = pytz.UTC

logger = logging.getLogger("chatbot")
logger.setLevel(logging.DEBUG)

COOKIES_LOC = "/chatbot_data/cookies"

logformat = "%(asctime)s.%(msecs)03d [%(levelname)s] <%(module)s> %(funcName)s(): %(message)s"
dateformat = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=logformat, datefmt=dateformat)

data_dir = pathlib.Path('/chatbot_data')
data_dir.mkdir(exist_ok=True)
log_file = data_dir / 'chatbot.log'
log_file.touch(exist_ok=True)

fh = logging.FileHandler('/chatbot_data/chatbot.log', 'a', 'utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load plugins from plugins folder.
logger.info("Importing plugins from plugins folder...")
plugin_dict = {}
for module in plugins.__all__:
    plugin = importlib.import_module("pontozobiztos.plugins." + module)
    try:
        logger.info(f"Added module {module} to active plugins")
        plugin_dict[module] = plugin
    except AttributeError:
        logger.warning(f"Plugin '{module}' has no attribute 'ENABLED'.")
        del plugin


def init_plugins(*args, **kwargs):
    """Initializes plugins in    plugin_dict"""
    for name, obj in plugin_dict.items():
        try:
            obj.init(*args, **kwargs)
        except (TypeError, AttributeError):
            logger.warning("Plugin '{}' could not be initialized "
                           "because it doesn't implement 'init'.".format(name))


def on_2fa_callback():
    return int(input("Enter 2FA code: "))


class HomoBot(fbchat.Session):
    GROUP_ID = '232447473612485'
    SILENT = False
    ENABLED = True
    group: fbchat.GroupData

    @classmethod
    def create(cls):
        logger.info("Logging in...")
        try:
            with open(COOKIES_LOC, "rb") as cookies:
                session_cookies = pickle.load(cookies)
            self = cls.from_cookies(session_cookies)
        except (FileNotFoundError, pickle.UnpicklingError):
            self = cls.login(os.getenv('EMAIL'),
                             os.getenv('PASSWORD'))

        logger.info(f"Starting facebook client. ENABLED: {self.ENABLED}; "
                    f"SILENT: {self.SILENT}")

        logger.info("Login successful!")
        with open(COOKIES_LOC, "wb") as cookies:
            pickle.dump(self.get_cookies(), cookies)
        logger.debug("Cookies saved with pickle protocol")

        logger.debug("Cross-checking facebook data with database")
        self.update_users()
        logger.debug("Synchronizing database with facebook")
        self.sync_database()
        logger.info("Initializing plugins...")
        init_plugins()
        return self

    def listen(self):
        listener = fbchat.Listener(session=self,
                                   chat_on=False,
                                   foreground=False)
        for event in listener.listen():
            self.handle_event(event)

    def handle_event(self, event: fbchat._events.Event) -> bool:
        if isinstance(event, fbchat.MessageEvent):
            thread = event.message.thread
            msg = event.message.fetch()
            logger.info(msg)
            if thread.id == self.GROUP_ID:
                thread = self.group  # changes from Group to GroupData
                chatmongo.insert_or_update_message(msg)
                return False  # COMMENT THIS
            elif thread.id != self.user.id:
                return False

            for mod in plugin_dict.values():
                try:
                    mod.on_message(thread=thread,
                                   author=User.User(msg.author),
                                   message=msg)
                except (AttributeError, TypeError):
                    pass
        elif isinstance(event, fbchat.ThreadsRead):
            pass
        return False

    # async def onMessage(
    #     self,
    #     mid=None,
    #     author_id=None,
    #     message=None,
    #     message_object=None,
    #     thread_id=None,
    #     thread_type=fbchat.ThreadType.USER,
    #     ts=None,
    #     metadata=None,
    #     msg=None,
    # ):
    #     if thread_id != self.GROUP_ID:
    #         return
    #     # if thread_id != self.uid:
    #     #     return
    #
    #     logger.info(f"{message_object} from {author_id}")
    #
    #     chatmongo.insert_or_update_message(message_object)
    #
    #     print(plugin_dict)
    #     for mod in plugin_dict.values():
    #         try:
    #             await mod.on_message(client=self.proxy,
    #                            author=User.User(author_id),
    #                            message=copy.copy(message_object))
    #         except (AttributeError, TypeError):
    #             pass
    #
    # async def onMessageUnsent(
    #     self,
    #     mid=None,
    #     author_id=None,
    #     thread_id=None,
    #     thread_type=None,
    #     ts=None,
    #     msg=None,
    # ):
    #     if thread_id != self.GROUP_ID:
    #         return
    #
    #     logger.info(f"{author_id} unsent the message {repr(mid)} at {ts}")
    #
    #     if not chatmongo.mark_message_as_deleted(mid):
    #         msg = self.fetch_message_info(mid)
    #         chatmongo.insert_or_update_message(msg)
    #
    #     for mod in plugin_dict.values():
    #         try:
    #             await mod.on_message_unsent(client=self.proxy,
    #                                   user=User.User(author_id),
    #                                   mid=mid)
    #         except (AttributeError, TypeError):
    #             pass
    #
    # async def onMessageSeen(
    #     self,
    #     seen_by=None,
    #     thread_id=None,
    #     thread_type=fbchat.ThreadType.USER,
    #     seen_ts=None,
    #     ts=None,
    #     metadata=None,
    #     msg=None,
    # ):
    #     if thread_id != self.GROUP_ID:
    #         return
    #
    #     logger.info(f"Messages seen by {seen_by} at {seen_ts}")
    #
    #     chatmongo.set_last_read_at(seen_by, seen_ts)
    #
    #     for mod in plugin_dict.values():
    #         try:
    #             await mod.on_message_seen(client=self.proxy, seen_by=seen_by)
    #         except (AttributeError, TypeError):
    #             pass
    #
    # async def onReactionAdded(
    #     self,
    #     mid=None,
    #     reaction=None,
    #     author_id=None,
    #     thread_id=None,
    #     thread_type=None,
    #     ts=None,
    #     msg=None,
    # ):
    #     if thread_id != self.GROUP_ID:
    #         return
    #
    #     logger.info(
    #         f"{author_id} reacted to message {mid} with {reaction.name}")
    #
    #     if not chatmongo.add_reaction(mid, author_id, reaction):
    #         msg = self.fetch_message_info(mid)
    #         chatmongo.insert_or_update_message(msg)
    #
    #     for mod in plugin_dict.values():
    #         try:
    #             await mod.on_reaction_added(client=self.proxy,
    #                                   message_id=mid,
    #                                   reaction=reaction,
    #                                   user=User.User(author_id))
    #         except (AttributeError, TypeError):
    #             pass
    #
    # async def on_reaction_removed(
    #     self,
    #     mid=None,
    #     author_id=None,
    #     thread_id=None,
    #     thread_type=None,
    #     ts=None,
    #     msg=None,
    # ):
    #     if thread_id != self.GROUP_ID:
    #         return
    #     logger.info(f"{author_id} removed reaction from {mid} message.")
    #     if not chatmongo.remove_reaction(mid, author_id):
    #         msg = self.fetch_message_info(mid)
    #         chatmongo.insert_or_update_message(msg)
    #
    #     for mod in plugin_dict.values():
    #         try:
    #             await mod.on_reaction_removed(client=self.proxy,
    #                                     message_id=mid,
    #                                     user=User.User(author_id))
    #         except (AttributeError, TypeError):
    #             pass

    def get_group_user_data(self):
        client = fbchat.Client(session=self)
        self.group = next(client.fetch_thread_info([self.GROUP_ID]))
        ids = [p.id for p in self.group.participants]
        return [(key,
                 data['name'],
                 self.group.nicknames[key])
                for key, data in client._fetch_info(*ids).items()]

    def update_users(self):
        """Updates the database from Facebook
        (ID, username, nickname w/o points)
        """
        for ud in self.get_group_user_data():
            chatmongo.update_or_add_user(*ud)

    def sync_database(self):
        latest_msg_ts = chatmongo.get_latest_message().created_at
        before = datetime.now(tz=utc)
        while before > latest_msg_ts:
            data = self.group._fetch_messages(100, before)
            for msg in data:
                chatmongo.insert_or_update_message(msg)
            before = data[0].created_at
            time.sleep(random.uniform(0, 3))
