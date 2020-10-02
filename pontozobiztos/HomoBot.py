from . import MyClient
from . import chatmongo
from . import plugins
from .models import User
import importlib
import logging
import fbchat
import pathlib
import urllib.request
import os
import copy


logger = logging.getLogger("chatbot")
logger.setLevel(logging.DEBUG)

logformat = "%(asctime)s.%(msecs)03d [%(levelname)s] <%(module)s> %(funcName)s(): %(message)s"
dateformat = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt=logformat, datefmt=dateformat)

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


class HomoBot(MyClient.MyClient):
    def __init__(self, email, password, session_cookies=None):
        logger.info(f"Starting facebook client. ENABLED: {self.ENABLED}; "
                    f"SILENT: {self.SILENT}")
        super().__init__(email, password, session_cookies)
        logger.debug("Cross-checking facebook data with database")
        self.update_users()
        logger.info("Initializing plugins...")
        init_plugins(client=self.proxy)

    def onMessage(
        self,
        mid=None,
        author_id=None,
        message=None,
        message_object=None,
        thread_id=None,
        thread_type=fbchat.ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return
        # if thread_id != self.uid:
        #     return

        logger.info(f"{message_object} from {author_id}")

        chatmongo.insert_or_update_message(message_object)
        
        print(plugin_dict)
        for mod in plugin_dict.values():
            try:
                mod.on_message(client=self.proxy,
                               author=User.User(author_id),
                               message=copy.copy(message_object))
            except (AttributeError, TypeError):
                pass

    def onMessageUnsent(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(f"{author_id} unsent the message {repr(mid)} at {ts}")

        if not chatmongo.mark_message_as_deleted(mid):
            msg = self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                mod.on_message_unsent(client=self.proxy,
                                      user=User.User(author_id),
                                      mid=mid)
            except (AttributeError, TypeError):
                pass

    def onMessageSeen(
        self,
        seen_by=None,
        thread_id=None,
        thread_type=fbchat.ThreadType.USER,
        seen_ts=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(f"Messages seen by {seen_by} at {seen_ts}")

        chatmongo.set_last_read_at(seen_by, seen_ts)

        for mod in plugin_dict.values():
            try:
                mod.on_message_seen(client=self.proxy, seen_by=seen_by)
            except (AttributeError, TypeError):
                pass

    def onReactionAdded(
        self,
        mid=None,
        reaction=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return

        logger.info(
            f"{author_id} reacted to message {mid} with {reaction.name}")

        if not chatmongo.add_reaction(mid, author_id, reaction):
            msg = self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                mod.on_reaction_added(client=self.proxy,
                                      message_id=mid,
                                      reaction=reaction,
                                      user=User.User(author_id))
            except (AttributeError, TypeError):
                pass

    def onReactionRemoved(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        if thread_id != self.GROUP_ID:
            return
        logger.info(f"{author_id} removed reaction from {mid} message.")
        if not chatmongo.remove_reaction(mid, author_id):
            msg = self.fetch_message_info(mid)
            chatmongo.insert_or_update_message(msg)

        for mod in plugin_dict.values():
            try:
                mod.on_reaction_removed(client=self.proxy,
                                        message_id=mid,
                                        user=User.User(author_id))
            except (AttributeError, TypeError):
                pass

    def update_users(self):
        """Updates the database from Facebook
        (ID, username, nickname w/o points)
        """
        group_info = self.fetch_group_info()
        fb_id_set = group_info.participants
        db_id_set = set(chatmongo.get_user_ids())
        if (fb_id_set - db_id_set) != set():
            for uid, user in (self.fetchUserInfo(*fb_id_set)).items():
                chatmongo.update_or_add_user(
                    uid,
                    user.name,
                    group_info.nicknames.get(uid)
                )
